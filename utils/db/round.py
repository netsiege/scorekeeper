from typing import TypedDict
from pymongo.database import Database
from pymongo.collection import Collection
from utils.db.teams import Team, get_all_teams
from utils.db.boxes import Box
from utils.control import Flag

class Round:
    def __init__(self, id, teams = [], boxes = []):
        self._id: int = id
        self.teams: list[dict] = teams
        self.boxes: list[dict] = boxes
    def teams_to_save(self, teams: list[Team]) -> None:
        save_data: set = {"_id", "name", "points", "token"}
        self.teams = [{key: team.__dict__[key] for key in save_data} for team in teams]
    
    def boxes_to_save(self, boxes: list[Team]) -> None:
        save_data: set = {"_id", "name", "ip", "checks"}
        self.boxes = [{key: box.to_dict()[key] for key in save_data} for box in boxes]

    def update_db(self, db: Database):
        self._id += 1
        db.rounds.insert_one(self.__dict__)

if __name__ == "__main__":
    pass