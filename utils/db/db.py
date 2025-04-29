from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from utils.db.teams import create_teams_from_config, get_team_by_name
DEBUG = 1

def initialize(connect_url: str, config: dict) -> Database:
    client: MongoClient = MongoClient(connect_url)
    if client is None:
        print(f"Could not connect to the database using url {connect_url}")
        return
    
    if DEBUG:
        print("Sucessfully connected to the database")

    if "scorekeeper" in client.list_database_names():
        client.drop_database("scorekeeper")
    # Initialize database
    db: Database = client["scorekeeper"]

    # Create teams from config

    create_teams_from_config(config, db)

    if DEBUG:
        print(f"Successfully created collections: {"".join(db.list_collection_names())}")

    return db


