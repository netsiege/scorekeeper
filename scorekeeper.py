# local imports
import utils.routes as routes
import utils.config as config
import utils.db.db as db
import utils.db.teams as t
from utils.db.round import Round
import utils.db.boxes as b
from game import Game
# non-local imports
from flask import Flask

app = Flask(__name__)

if __name__ == "__main__":
    routes.register_routes(app)
    config_file: dict = config.read_config("config/config.yml")

    config.check_configs(config_file)

    # Change static ip to use config file
    database = db.initialize("mongodb://10.7.7.7:27017", config_file)
    round = Round(0)
    game = Game(database, round) 
    game.sync()
    game.save_round()

    game.rotate_team_tokens()

    for team in game.teams:
        team.modify_team_points(10)
        team.update_db(database)

    game.check_all_and_update()
    game.update_db()
    game.save_round()
    game.sync()

    tokens = t.get_team_token_mapping(game.teams)
    print(tokens)
    app.run(host="0.0.0.0", debug=True, port=8000, use_reloader=False)
