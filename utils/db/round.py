from typing import TypedDict
from pymongo.database import Database
from pymongo.collection import Collection
from utils.db.teams import Team, get_all_teams
from utils.db.boxes import Box
from utils.control import Flag
class SaveTeam(TypedDict):
    _id: int
    name: str
    points: int
    penalties: int
        
class SaveBox(TypedDict):
    name: str
    ip: str
    control: list[Flag]

class Round(TypedDict):
    _id: int
    teams: list[SaveTeam]
    boxes: list[SaveBox]

def teams_to_save(data: list[Team]) -> SaveTeam:
    save_data: set = {"_id", "name", "points", "penalties"}
    return [SaveTeam({key: team[key] for key in save_data}) for team in data]
 
def boxes_to_save(data: list[Box]) -> SaveBox:
    save_data: set = {"name", "ip", "control"}
    return [SaveBox({key: box[key] for key in save_data}) for box in data]


def build_round(db: Database) -> Round:
    teams: list[Team] = get_all_teams(db)
    save_teams: list[SaveTeam] = teams_to_save(teams)
    rounds: int = db.rounds.count_documents({})
    return Round(_id=rounds, teams=save_teams, boxes={})

def save_round(db: Database) -> None:
    round: Round = build_round(db)
    db.rounds.insert_one(round)

if __name__ == "__main__":
    box = Team(_id=1, name="eh", password="asdf", points=123, penalties=1, token="123")
    box1= Team(_id=2, name="eh", password="asdf", points=123, penalties=1, token="123")
    l = [box, box1]
    d = teams_to_save(l)
    print(d)