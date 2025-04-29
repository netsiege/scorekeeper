from flask import Blueprint

engine_routes = Blueprint('engine_routes', __name__)

@engine_routes.route("/")
def home():
    return 'hello world'

def register_routes(app):
    app.register_blueprint(engine_routes)