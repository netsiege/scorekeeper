from typing import TypedDict
from utils.checks.check import Check
from utils.control import Flag
from pymongo.database import Database

class Box(TypedDict):
    _id: int
    name: str
    ip: str
    control: list[Flag]
    services: list[Check]

class Flag(TypedDict):
    path: str
    root: bool
    name: str
    team_id: int

# Create box

# Parse box config

# Create box from config


# move to frontend
def get_root_flag(box: Box) -> Flag | None:
    for flag in box.control:
        if flag.root and flag.team_id != -1:
            return flag
    return None

# probably for displaying in team dashboard; move to frontend
def get_all_control_by_team(boxes: list[Box], team_id: int) -> list[(Flag, bool)]:
    control_flags = []
    for box in boxes:
        valid: bool = all([check.last for check in box.services])
        root_flag = get_root_flag(box)
        if not root_flag:
            for flag in box.control:
                if flag.team_id == team_id:
                    control_flags.append((flag, valid))
        else:
            if root_flag.team_id == team_id:
                control_flags.append((flag, valid))
    return control_flags

def get_box_by_id(db: Database, id: int) -> Box:
    return Box(db.teams.find_one({"_id": id}))

def get_all_boxes(db: Database) -> list[Box]: 
    return [Box(box) for box in list(db.boxes.find({}))]

# for tally
def get_ip_control_path_mapping(boxes: list[Box]) -> list[(str,str)]:
    return [(box.ip, ";".join([flag.path for flag in box.control])) for box in boxes]

    