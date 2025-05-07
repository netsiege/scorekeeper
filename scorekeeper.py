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
import time
import threading

app = Flask(__name__)


def main(game: Game):
    while True:
        game.update_db()
        game.sync()
        game.save_round()


        game.check_all_and_update()
        game.rotate_team_tokens()
        print([team.__dict__ for team in game.teams])
        tokens = t.get_team_token_mapping(game.teams)
        print(tokens)
        time.sleep(30)

if __name__ == "__main__":
    routes.register_routes(app)
    config_file: dict = config.read_config("config/config.yml")

    config.check_configs(config_file)

    # Change static ip to use config file
    database = db.initialize("mongodb://10.7.7.7:27017", config_file)
    round = Round(0)
    game = Game(database, round) 
    game.rotate_team_tokens()

    thread = threading.Thread(target=main, args=(game,))
    thread.daemon = True
    thread.start()
    app.run(host="0.0.0.0", debug=True, port=8000, use_reloader=False)
