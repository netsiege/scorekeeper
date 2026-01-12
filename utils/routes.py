from utils.db.boxes import get_all_checks, get_all_services
from utils.task_queue import task_queue

from flask import Blueprint, jsonify, request
from flask_cors import CORS
import jwt
import os
from datetime import datetime, timedelta

def get_client_ip():
    """Get the actual TCP peer IP address."""
    return request.remote_addr

def create_engine_routes(game):
    engine_routes = Blueprint('engine_routes', __name__)

    @engine_routes.route("/api/boxes", methods=['GET'])
    def boxes():
        return jsonify([box.to_dict_frontend() for box in game.boxes.values()])
    
    @engine_routes.route("/api/teams", methods=['GET'])
    def teams():
        return jsonify([team.to_dict_frontend() for team in game.teams])

    @engine_routes.route("/api/tasks", methods=['GET'])
    def get_tasks():
        """Get all pending tasks for the client's box based on their IP.
        Client IP is automatically mapped to hostname from phase config.
        Header: Authorization: Bearer {token} (required if key exists)
        """
        client_ip = get_client_ip()
        hostname = task_queue.get_hostname_by_ip(client_ip)
        
        if not hostname:
            return jsonify({
                "error": f"No hostname mapping found for IP {client_ip}",
                "ip": client_ip
            }), 400
        
        # If a key exists for this box, require authentication
        existing_key = task_queue.get_box_key(hostname)
        if existing_key:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "Authorization header with Bearer token is required"}), 401
            
            box_key = auth_header[7:]  # Remove 'Bearer ' prefix
            if not task_queue.verify_box_key(hostname, box_key):
                return jsonify({"error": "Invalid box key"}), 401
        
        tasks = task_queue.get_tasks(hostname)
        
        return jsonify({
            "hostname": hostname,
            "ip": client_ip,
            "tasks": tasks
        })
    
    @engine_routes.route("/api/rotate_key", methods=['POST'])
    def rotate_key():
        """Set a new authentication key for the client's box.
        Client IP is automatically mapped to hostname from phase config.
        Header: Authorization: Bearer {token} (required if key already exists)
        Body: JSON with:
            - key: the new authentication key to set for this box
        """
        client_ip = get_client_ip()
        hostname = task_queue.get_hostname_by_ip(client_ip)
        
        if not hostname:
            return jsonify({
                "error": f"No hostname mapping found for IP {client_ip}",
                "ip": client_ip
            }), 400
        
        # If a key already exists, require authentication with the current key
        existing_key = task_queue.get_box_key(hostname)
        if existing_key:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "Authorization header with Bearer token is required to rotate existing key"}), 401
            
            provided_key = auth_header[7:]  # Remove 'Bearer ' prefix
            if not task_queue.verify_box_key(hostname, provided_key):
                return jsonify({"error": "Invalid box key"}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON body is required"}), 400
        
        new_key = data.get('new_key')
        if not new_key:
            return jsonify({"error": "new_key is required in request body"}), 400
        
        task_queue.set_box_key(hostname, new_key)
        
        # Remove the rotate_key task from the queue after successfully setting the key
        task_queue.remove_task_by_type(hostname, "rotate_key")
        
        return jsonify({
            "message": "Key updated successfully",
            "hostname": hostname,
            "ip": client_ip
        }), 200

    @engine_routes.route("/api/claim", methods=['POST'])
    def submit_claim():
        """Submit a claim response and remove the task from the queue.
        Client IP is automatically mapped to hostname from phase config.
        Header: Authorization: Bearer {token} (required if key exists)
        Body: JSON with claim data including:
            - token: the team's token for verification
            - file_path/path: identifies which task to remove (optional)
            - task_type/type: task type to remove (optional)
        Points are awarded based on the task's value and owner status.
        """
        client_ip = get_client_ip()
        hostname = task_queue.get_hostname_by_ip(client_ip)
        
        if not hostname:
            return jsonify({
                "error": f"No hostname mapping found for IP {client_ip}",
                "ip": client_ip
            }), 400
        
        # If a key exists for this box, require authentication
        existing_key = task_queue.get_box_key(hostname)
        if existing_key:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "Authorization header with Bearer token is required"}), 401
            
            box_key = auth_header[7:]  # Remove 'Bearer ' prefix
            if not task_queue.verify_box_key(hostname, box_key):
                return jsonify({"error": "Invalid box key"}), 401
        
        claim_data = request.get_json()
        if not claim_data:
            return jsonify({"error": "claim data is required in request body"}), 400
        
        # Check if there are any tasks in the queue before processing
        if not task_queue.has_tasks(hostname):
            return jsonify({"error": "No tasks available in queue for this box"}), 400
        
        # Get the file_path to find and remove the task
        file_path = claim_data.get('file_path') or claim_data.get('path')
        if not file_path:
            return jsonify({"error": "file_path is required in claim data"}), 400
        
        # Remove task by file_path (regardless of token validity)
        removed_task = task_queue.remove_task_by_path(hostname, file_path)
        if not removed_task:
            return jsonify({"error": f"No task found with file_path: {file_path}"}), 400
        
        # Verify token and assign team_id after removing task
        token = claim_data.get('file_content')
        if not token:
            return jsonify({"error": "token is required in claim data"}), 400
        
        team_id = game.assign_box_team_id(hostname, token, file_path)
        if team_id is None:
            return jsonify({"error": "Invalid token"}), 401
        
        check_id = f"{hostname}_{file_path}"
        
        response = {
            "message": "Claim submitted successfully",
            "hostname": hostname,
            "ip": client_ip,
            "team_id": team_id,
            "claim": claim_data,
            "task_removed": removed_task is not None,
            "check_id": check_id
        }
        
        return jsonify(response), 200
    
    @engine_routes.route("/api/tasks/all", methods=['GET'])
    def get_all_tasks():
        """Get all task queues for all boxes.
        Header: Authorization: Bearer {token}
        """
        client_ip = get_client_ip()
        hostname = task_queue.get_hostname_by_ip(client_ip)
        
        if not hostname:
            return jsonify({
                "error": f"No hostname mapping found for IP {client_ip}",
                "ip": client_ip
            }), 400
        
        # Authenticate using box key
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authorization header with Bearer token is required"}), 401
        
        box_key = auth_header[7:]  # Remove 'Bearer ' prefix
        if not task_queue.verify_box_key(hostname, box_key):
            return jsonify({"error": "Invalid box key"}), 401
        
        return jsonify(task_queue.get_all_queues())

    @engine_routes.route("/api/team/auth", methods=['POST'])
    def authenticate_team():
        """Authenticate a team and return a JWT session token.
        Body: JSON with:
            - team_name: the team's name
            - password: the team's password
        Returns JWT token if credentials are valid.
        """
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON body is required"}), 400
        
        team_name = data.get('team_name')
        password = data.get('password')
        
        if not team_name or not password:
            return jsonify({"error": "team_name and password are required"}), 400
        
        # Find the team by name
        team = None
        for t in game.teams:
            if t.name.lower() == team_name.lower():
                team = t
                break
        
        if not team:
            return jsonify({"error": "Team not found"}), 404
        
        # Verify password
        if team.password != password:
            return jsonify({"error": "Invalid password"}), 401
        
        # Generate JWT session token with 1 hour expiration
        secret_key = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        payload = {
            'team_id': team._id,
            'team_name': team.name,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        session_token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        return jsonify({
            "message": "Authentication successful",
            "team_id": team._id,
            "team_name": team.name,
            "session_id": session_token,
            "token": team.token,
            "expires_in": 3600
        }), 200

    @engine_routes.route("/api/team/verify", methods=['GET'])
    def verify_session():
        """Verify JWT session token and return team info.
        Header: Authorization: Bearer {jwt_token}
        Returns team information if token is valid.
        """
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authorization header with Bearer token is required"}), 401
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        try:
            secret_key = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            
            return jsonify({
                "valid": True,
                "team_id": payload['team_id'],
                "team_name": payload['team_name']
            }), 200
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

    return engine_routes


def register_routes(app, game):
    app.register_blueprint(create_engine_routes(game))
    CORS(app)