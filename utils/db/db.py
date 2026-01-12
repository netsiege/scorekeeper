from pymongo import MongoClient
from pymongo.database import Database
from utils.db.teams import create_teams_from_config
from utils.db.boxes import create_boxes_from_config
from utils.config import read_config
DEBUG = 1

def initialize(config: dict) -> Database:
    event = config["event"]
    db_config = event["database"]
    phase_config = read_config(event["phases"][event["phase"] - 1])
    connect_url = f"mongodb://{db_config['location']}:27017" 
    client: MongoClient = MongoClient(connect_url)
    if client is None:
        print(f"Could not connect to the database using url {connect_url}")
        return
    if DEBUG:
        print("Sucessfully connected to the database")

    db: Database = client["scorekeeper"]
    if "scorekeeper" in client.list_database_names():
        if event["reset"] == True:
            client.drop_database("scorekeeper")
            create_teams_from_config(config,db)
        else:
            db.boxes.drop()
    # Initialize database
    else:
    # Create teams from config
        create_teams_from_config(config, db)
    create_boxes_from_config(phase_config, db)

    if DEBUG:
        print(f"Successfully created collections: {', '.join(db.list_collection_names())}")

    return db


