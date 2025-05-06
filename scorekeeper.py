# local imports
import utils.routes as routes
import utils.config as config
import utils.db.db as db
import utils.db.teams as t
import utils.db.round as r
import utils.db.boxes as b
# non-local imports
from flask import Flask

app = Flask(__name__)

if __name__ == "__main__":
    routes.register_routes(app)
    config_file: dict = config.read_config("config/config.yml")
    print(config.read_boxes(config_file))

    config.check_configs(config_file)

    database = db.initialize("mongodb://10.7.7.7:27017", config_file)
    b.create_boxes_from_config(config_file, database)
    round = r.Round(0)
    teams = t.get_all_teams(database)
    boxes = b.get_all_boxes(database)
    round.teams_to_save(teams)
    round.boxes_to_save(boxes)
    round.update_db(database)

    
    t.rotate_all_team_tokens(teams)
    for team in teams:
        team.modify_team_points(10)
        team.update_db(database)

    boxes[0].update_control("root", 1)
    boxes[0].update_db(database)

    teams = t.get_all_teams(database)
    boxes = b.get_all_boxes(database)
    round.teams_to_save(teams)
    round.boxes_to_save(boxes)
    round.update_db(database)
    
    tokens = t.get_team_token_mapping(teams)
    print(tokens)
    print(b.get_all_boxes(database))
    app.run(host="0.0.0.0", debug=True, port=8000, use_reloader=False)
