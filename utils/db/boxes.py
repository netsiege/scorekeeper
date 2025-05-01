from typing import TypedDict
from utils.checks.check import Check
from utils.checks.web import WebCheck
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
    owner: bool
    name: str
    team_id: int
    points: int

DEBUG = 1

CHECK_MAP = {"web": WebCheck}

# Create box
def create_box(db: Database, box: Box) -> None:
    try:
        db.boxes.insert_one(box)
        if DEBUG:
            print(f"Created box: {box['name']}")
    except Exception as e:
        print("Error adding box:", e)
# Parse box config

def parse_box_config(config: dict) -> list[Box]:
    boxes: list[Box] = []
    for entry in config["boxes"]:
        control: list[Flag] = [Flag(path=flag["path"], owner=flag["owner"], name=flag["name"], team_id=-1, points=flag["points"]) for flag in entry["control"]]
        services: list[Check] = [CHECK_MAP[type](**check) for type, check in entry["services"].items()]
        boxes.append(Box(_id=entry["id"], name=entry["name"], ip=entry["ip"], control=control, services=map(lambda x: x.__dict__, services)))
    return boxes
# Create box from config
def create_boxes_from_config(config: dict, db: Database) -> None:
    boxes: list[Box] = parse_box_config(config)
    for box in boxes:
        create_box(db, box)



# move to frontend
def get_root_flag(box: Box) -> Flag | None:
    for flag in box["control"]:
        if flag["owner"] and flag["team_id"] != -1:
            return flag
    return None

# probably for displaying in team dashboard; move to frontend
def get_all_control_by_team(boxes: list[Box], team_id: int) -> list[(Flag, bool)]:
    control_flags = []
    for box in boxes:
        valid: bool = all([check["last"] for check in box["services"]])
        root_flag = get_root_flag(box)
        if not root_flag:
            for flag in box.control:
                if flag["team_id"] == team_id:
                    control_flags.append((flag, valid))
        else:
            if root_flag["team_id"] == team_id:
                control_flags.append((flag, valid))
    return control_flags

def get_box_by_id(db: Database, id: int) -> Box:
    return Box(db.teams.find_one({"_id": id}))

def get_all_boxes(db: Database) -> list[Box]: 
    return [Box(box) for box in list(db.boxes.find({}))]

# for tally
def get_ip_control_path_mapping(boxes: list[Box]) -> list[(str,str)]:
    return [(box.ip, ";".join([flag.path for flag in box["control"]])) for box in boxes]