# local imports
import utils.routes as routes
import utils.config as config
import utils.db.db as db
import utils.db.teams as teams
import utils.db.round as round
import utils.db.boxes as boxes
# non-local imports
from flask import Flask

app = Flask(__name__)

if __name__ == "__main__":
    routes.register_routes(app)
    config_file: dict = config.read_config("config/config.yml")
    print(config.read_boxes(config_file))

    config.check_configs(config_file)

    database = db.initialize("mongodb://10.7.7.7:27017", config_file)

    teams.modify_team_attribute(database, 1, 10)
    teams.rotate_all_team_tokens(database)
    boxes.create_boxes_from_config(config_file, database)
    round.save_round(database)
    
    app.run(host="0.0.0.0", debug=True, port=8000, use_reloader=False)
