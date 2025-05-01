from flask import Blueprint

engine_routes = Blueprint('engine_routes', __name__)


@engine_routes.route("/api/authenticate", methods=['POST'])
def login():
    return 'hello world'

@engine_routes.route("/api/boxes", methods=['GET'])
def boxes():
    return 'hello world'

@engine_routes.route("/api/teams", methods=['GET'])
def teams():
    return 'hello world'


def register_routes(app):
    app.register_blueprint(engine_routes)