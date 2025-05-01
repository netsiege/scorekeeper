from typing import TypedDict
from pymongo.database import Database
from pymongo.collection import Collection
import uuid

class Team(TypedDict):
    _id: int
    name: str
    password: str
    points: int
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

def get_all_teams(db: Database) -> list[dict]:
    return [Team(team) for team in list(db.teams.find({}))]

def get_team_by_id(db: Database, id: int) -> dict:
    return Team(db.teams.find_one({"_id": id}))


def modify_team_attribute(db: Database, id: int, increment: int) -> bool:
    # attribute: penalties, points
    cur_value = get_team_by_id(id).points
    new_value = { "$set": { "points": cur_value + increment } }
    db.teams.update_one({"_id": id}, new_value)

def rotate_team_token(db: Database, id: int) -> None:
    new_uuid = uuid.uuid4()
    new_value = { "$set": { "token": str(new_uuid) } }
    db.teams.update_one({"_id": id}, new_value)

def rotate_all_team_tokens(db: Database) -> None:
    teams = get_all_teams(db)
    for team in teams:
        rotate_team_token(db, team._id)
