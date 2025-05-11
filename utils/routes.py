from flask import Blueprint, jsonify

def create_engine_routes(game):

    engine_routes = Blueprint('engine_routes', __name__)

    @engine_routes.route("/api/authenticate", methods=['POST'])
    def login():
        return 'hello world'

    @engine_routes.route("/api/boxes", methods=['GET'])
    def boxes():
        return jsonify({box._id: {'name': box.name, 'ip': box.ip} for box in game.boxes})
    
    @engine_routes.route("/api/teams", methods=['GET'])
    def teams():
        return jsonify({team._id: team.name for team in game.teams})

    return engine_routes

def register_routes(app, game):
    app.register_blueprint(create_engine_routes(game))