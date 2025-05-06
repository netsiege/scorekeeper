from typing import TypedDict
from utils.checks.check import Check
from utils.checks.web import WebCheck
from utils.checks.control import ControlCheck
from utils.control import Flag
from pymongo.database import Database

class Box:
    def __init__(self, id, name="", ip = "", checks=[]):
        self._id: int = id
        self.name: str = name
        self.ip: str = ip
        self.checks: list[Check] = checks

    def to_dict(self):
        ret = dict()
        for key in self.__dict__:
            if key == "checks":
                ret[key] = [x.to_dict() for x in getattr(self, key)]
            else:
                ret[key] = getattr(self, key)
        return ret
    
    def update_db(self, db: Database):
        db.boxes.update_one({"_id": self._id}, {"$set": {"checks": [x.to_dict() for x in self.checks]}})

    def update_control(self, name: str, team_id: int):
        for check in self.checks:
            if type(check) == ControlCheck and check.name == name:
                check.team_id = team_id

DEBUG = 1

CHECK_MAP = {"web": WebCheck, "control": ControlCheck}

# Create box
def create_box(db: Database, box: Box) -> None:
    try:
        print(box.to_dict())
        db.boxes.insert_one(box.to_dict())
        if DEBUG:
            print(f"Created box: {box.name}")
    except Exception as e:
        print("Error adding box:", e)
# Parse box config

def parse_box_config(config: dict) -> list[Box]:
    boxes: list[Box] = []
    for entry in config["boxes"]:
        checks: list[Check] = [CHECK_MAP[key](**(value)) for check in entry["checks"] for key, value in check.items()]
        print(checks)
        boxes.append(Box(entry["id"], name=entry["name"], ip=entry["ip"], checks=checks))
    return boxes

# Create box from config
def create_boxes_from_config(config: dict, db: Database) -> None:
    boxes: list[Box] = parse_box_config(config)
    for box in boxes:
        create_box(db, box)



# # move to frontend
# def get_root_flag(box: Box) -> Flag | None:
#     for check, details in box["checks"].items():
#         if check == "control" and details["owner"] and details["team_id"] != -1:
#             return 
#     return None

# # probably for displaying in team dashboard; move to frontend
# def get_all_control_by_team(boxes: list[Box], team_id: int) -> list[(Flag, bool)]:
#     control_flags = []
#     for box in boxes:
#         valid: bool = all([details["last"] for check, details in box["checks"] if check != "control"])
#         root_flag = get_root_flag(box)
#         if not root_flag:
#             for control in:
#                 if flag["team_id"] == team_id:
#                     control_flags.append((flag, valid))
#         else:
#             if root_flag["team_id"] == team_id:
#                 control_flags.append((flag, valid))
#     return control_flags

def get_box_by_id(db: Database, id: int) -> Box:
    return Box(db.teams.find_one({"_id": id}))

def get_all_boxes(db: Database) -> list[Box]: 
    boxes = []
    for box in db.boxes.find({}):
        checks: list[Check] = [CHECK_MAP[key](**value) for check in box["checks"] for key, value in check.items()]
        boxes.append(Box(box["_id"], name=box["name"], ip=box["ip"], checks=checks))
    return boxes

def get_all_control_box_mapping(boxes: list[Box]) -> dict[int, ControlCheck]:
    pass    