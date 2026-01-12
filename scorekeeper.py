# local imports
import utils.routes as routes
import utils.config as config
import utils.db.db as db
import utils.db.teams as t
from utils.db.round import Round
import utils.db.boxes as b
from game import Game
from utils.task_queue import task_queue
from utils.task_scheduler import task_scheduler
# non-local imports
from flask import Flask
import time
import threading
import random

DEBUG = 1


def main(game: Game):
    while True:
        game.check_all_and_update()
        game.rotate_team_tokens()
        print([team.__dict__ for team in game.teams])
        print([box.to_dict() for box in game.boxes.values()])
        tokens = t.get_team_token_mapping(game.teams)
        print(tokens)
        game.update_db()
        game.save_round()
        try:
            game.send_claims()
            game.send_services()
            # game.send_tokens()
            # game.send_points()
            game.send_teams()
        except Exception as e:
            print("Cannot connect to frontend", e)
            pass
        time.sleep(game.interval + random.randrange(game.jitter))


def web():
    app.run(host="0.0.0.0", debug=True, port=8000, use_reloader=False)

if __name__ == "__main__":
    app = Flask(__name__)
    config_file: dict = config.read_config("config/config.yml")

    config.check_configs(config_file)

    event = config_file["event"]

    # Change static ip to use config file
    database = db.initialize(config_file)
    round_num = database.rounds.count_documents({})
    if DEBUG:
        print(f"Starting from round {round_num}")
    round = Round(round_num)
    checks_config = event["checks"]
    frontend_config = event["frontend"]
    tasks_config = event.get("tasks", {})
    
    # Get phase config path based on current phase
    phase_num = event.get("phase", 1)
    phases = event.get("phases", [])
    phase_config = phases[phase_num - 1] if phases and phase_num <= len(phases) else ""
    
    game = Game(database, round, **checks_config, **frontend_config, phase_config=phase_config)
    game.sync()
    game.rotate_team_tokens()
    game.update_db()
    game.save_round()

    # Start task schedulers for automatic task queuing
    hostnames = [box.name for box in game.boxes.values()]
    task_scheduler.start_all(
        tasks_config,
        lambda hostname, task_type: task_queue.populate_from_config(hostname, task_type),
        hostnames
    )

    routes.register_routes(app, game)
    main_thread = threading.Thread(target=main, args=(game,), daemon=True)
    # web_thread = threading.Thread(target=web, daemon=True)
    main_thread.start()
    web()
