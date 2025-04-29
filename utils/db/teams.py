from typing import TypedDict
from pymongo.database import Database
from pymongo.collection import Collection
import uuid

class Team(TypedDict):
    _id: int
    name: str
    password: str
    points: int
    penalties: int
    token: str
    

DEBUG = 1


def create_team(db: Database, team: Team) -> None:
    try:
        db.teams.insert_one(team)
        if DEBUG:
            print(f"Created team: {team["name"]}")
    except Exception as e:
        print("Error adding team:", e)

def parse_team_config(config: dict) -> list[Team]:
    teams: list[Team] = []
    for entry in config["teams"]:
        teams.append(Team(_id=entry["id"], name=entry["name"], password=entry["password"], points=0, penalties=0, token=""))

    return teams

def create_teams_from_config(config: dict, db: Database) -> None:
    teams: list[Team] = parse_team_config(config)
    for team in teams:
        create_team(db, team)

def get_teams(db: Database) -> list[dict]:
    return list(db.teams.find({}))

def get_team_by_name(db: Database, name: str) -> dict:
    return db.teams.find_one({"name": name})

def get_team_by_id(db: Database, id: int) -> dict:
    return db.teams.find_one({"_id": id})

def get_team_attribute(db: Database, id: int, attribute: str) -> int | str:
    # attribute: password, points, penalties, token
    return db.teams.find_one({"_id": id})[attribute]

def modify_team_attribute(db: Database, id: int, attribute: str, increment: int) -> bool:
    # attribute: penalties, points
    cur_value = get_team_attribute(db, id, attribute)
    new_value = { "$set": { attribute: cur_value + increment } }
    db.teams.update_one({"_id": id}, new_value)

def rotate_team_token(db: Database, id: int) -> None:
    new_uuid = uuid.uuid4()
    new_value = { "$set": { "token": str(new_uuid) } }
    db.teams.update_one({"_id": id}, new_value)

def rotate_all_team_tokens(db: Database) -> None:
    teams = get_teams(db)
    for team in teams:
        rotate_team_token(db, team["_id"])
