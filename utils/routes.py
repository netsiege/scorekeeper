from utils.db.boxes import get_all_checks, get_all_services


from flask import Blueprint, jsonify

def create_engine_routes(game):

    engine_routes = Blueprint('engine_routes', __name__)

    @engine_routes.route("/api/authenticate", methods=['POST'])
    def login():
        return 'hello world'

    @engine_routes.route("/api/boxes", methods=['GET'])
    def boxes():
        return jsonify([box.to_dict_frontend() for box in game.boxes])
    
    @engine_routes.route("/api/teams", methods=['GET'])
    def teams():
        return jsonify({team._id: team.name for team in game.teams})

    @engine_routes.route("/api/claims", methods=['GET'])
    def claims():
        return jsonify(get_all_checks(game.boxes))
    
    @engine_routes.route("/api/services", methods=['GET'])
    def services():
        return jsonify(get_all_services(game.boxes))
    return engine_routes


def register_routes(app, game):
    app.register_blueprint(create_engine_routes(game))