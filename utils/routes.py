from utils.db.boxes import get_all_checks, get_all_services
from utils.task_queue import task_queue


from flask import Blueprint, jsonify, request
from flask_cors import CORS

def create_engine_routes(game):

    engine_routes = Blueprint('engine_routes', __name__)

    # @engine_routes.route("/api/authenticate", methods=['POST'])
    # def login():
    #     return 'hello world'

    @engine_routes.route("/api/boxes", methods=['GET'])
    def boxes():
        return jsonify([box.to_dict_frontend() for box in game.boxes])
    
    @engine_routes.route("/api/teams", methods=['GET'])
    def teams():
        return jsonify([team.to_dict_frontend() for team in game.teams])

    @engine_routes.route("/api/tasks", methods=['GET'])
    def get_tasks():
        """
        Get all pending tasks for a specific box.
        Query parameter: hostname - the box hostname to get tasks for
        """
        hostname = request.args.get('hostname')
        if not hostname:
            return jsonify({"error": "hostname query parameter is required"}), 400
        
        tasks = task_queue.get_tasks(hostname)
        
        return jsonify({
            "hostname": hostname,
            "tasks": tasks
        })
    
    @engine_routes.route("/api/rotate_key", methods=['POST'])
    def rotate_key():
        """
        Queue a rotate_key task for a specific box.
        Query parameter: hostname - the box hostname to queue rotate_key for
        """
        hostname = request.args.get('hostname')
        if not hostname:
            return jsonify({"error": "hostname query parameter is required"}), 400
        
        task_queue.populate_from_config(hostname, "rotate_key")
        
        return jsonify({
            "message": "Rotate key task queued",
            "hostname": hostname
        }), 201

    # @engine_routes.route("/api/tasks", methods=['POST'])
    # def add_task():
    #     """
    #     Add a task to a box's queue.
    #     Query parameter: hostname - the box hostname to add task for
    #     Body: JSON task object
    #     """
    #     hostname = request.args.get('hostname')
    #     if not hostname:
    #         return jsonify({"error": "hostname query parameter is required"}), 400
        
    #     task = request.get_json()
    #     if not task:
    #         return jsonify({"error": "task data is required in request body"}), 400
        
    #     task_queue.add_task(hostname, task)
    #     return jsonify({"message": "Task added", "hostname": hostname, "task": task}), 201
    
    # @engine_routes.route("/api/tasks/bulk", methods=['POST'])
    # def add_tasks_bulk():
    #     """
    #     Add multiple tasks to a box's queue.
    #     Query parameter: hostname - the box hostname to add tasks for
    #     Body: JSON array of task objects
    #     """
    #     hostname = request.args.get('hostname')
    #     if not hostname:
    #         return jsonify({"error": "hostname query parameter is required"}), 400
        
    #     tasks = request.get_json()
    #     if not tasks or not isinstance(tasks, list):
    #         return jsonify({"error": "task array is required in request body"}), 400
        
    #     task_queue.add_tasks(hostname, tasks)
    #     return jsonify({"message": f"{len(tasks)} tasks added", "hostname": hostname}), 201

    @engine_routes.route("/api/claim", methods=['POST'])
    def submit_claim():
        """
        Submit a claim response and remove the task from the queue.
        Query parameter: hostname - the box hostname submitting the claim
        Body: JSON with claim data including:
            - file_path/path: identifies which task to remove
            - token: the team's token for verification
        Points are awarded based on the task's value and owner status.
        """
        hostname = request.args.get('hostname')
        if not hostname:
            return jsonify({"error": "hostname query parameter is required"}), 400
        
        claim_data = request.get_json()
        if not claim_data:
            return jsonify({"error": "claim data is required in request body"}), 400
        
        token = claim_data.get('token')
        if not token:
            return jsonify({"error": "token is required in claim data"}), 400
        
        # Try to remove by file_path first (most specific)
        file_path = claim_data.get('file_path') or claim_data.get('path')
        removed_task = None
        if file_path:
            removed_task = task_queue.remove_task_by_path(hostname, file_path)
        
        # Fall back to task type if not removed by path
        if not removed_task:
            task_type = claim_data.get('task_type') or claim_data.get('type')
            if task_type:
                removed_task = task_queue.remove_task_by_type(hostname, task_type)
            else:
                # If no type specified, remove the first task
                removed_task = task_queue.remove_task(hostname, 0)
        
        points_awarded = 0
        team_id = None
        if removed_task:
            # Verify token and award points based on the task's value
            points_awarded, team_id = game.award_claim_points(hostname, token, removed_task)
            if team_id is None:
                return jsonify({"error": "Invalid token"}), 401
        
        response = {
            "message": "Claim submitted successfully",
            "hostname": hostname,
            "team_id": team_id,
            "claim": claim_data,
            "task_removed": removed_task is not None,
            "points_awarded": points_awarded
        }
        
        return jsonify(response), 200
    
    # @engine_routes.route("/api/tasks/clear", methods=['DELETE'])
    # def clear_tasks():
    #     """
    #     Clear all tasks for a specific box.
    #     Query parameter: hostname - the box hostname to clear tasks for
    #     """
    #     hostname = request.args.get('hostname')
    #     if not hostname:
    #         return jsonify({"error": "hostname query parameter is required"}), 400
        
    #     task_queue.clear_tasks(hostname)
    #     return jsonify({"message": "Tasks cleared", "hostname": hostname}), 200
    
    @engine_routes.route("/api/tasks/all", methods=['GET'])
    def get_all_tasks():
        """
        Get all task queues for all boxes.
        """
        return jsonify(task_queue.get_all_queues())

    # @engine_routes.route("/api/claims", methods=['GET'])
    # def claims():
    #     return jsonify(get_all_checks(game.boxes))
    
    # @engine_routes.route("/api/services", methods=['GET'])
    # def services():
    #     return jsonify(get_all_services(game.boxes))
    return engine_routes


def register_routes(app, game):
    app.register_blueprint(create_engine_routes(game))
    CORS(app)