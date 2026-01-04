from utils.checks.check import Check
from utils.checks.web import WebCheck
from utils.checks.claim import ClaimCheck
from utils.checks.ssh import SSHCheck
from utils.checks.rdp import RDPCheck
from utils.checks.mysql import MySQLCheck
from utils.checks.ftp import FTPCheck
from utils.checks.custom.custom_charon import CustomCharonCheck

from pymongo.database import Database

class Box:
    def __init__(self, id, name="", ip="", checks=None, claims=None):
        self._id: int = id
        self.name: str = name
        self.ip: str = ip
        self.checks: list[Check] = checks if checks is not None else []
        # Claims stored as dict keyed by file_path for O(1) lookup
        self.claims: dict[str, ClaimCheck] = claims if claims is not None else {}

    def to_dict(self):
        return {
            "_id": self._id,
            "name": self.name,
            "ip": self.ip,
            "checks": [x.to_dict() for x in self.checks] + [x.to_dict() for x in self.claims.values()]
        }

    def to_dict_frontend(self):
        return {
            "_id": self._id,
            "name": self.name,
            "ip": self.ip,
            "claims": [claim.__dict__ for claim in self.claims.values()],
            "services": [check.__dict__ for check in self.checks]
        }
    
    def update_db(self, db: Database):
        all_checks = [x.to_dict() for x in self.checks] + [x.to_dict() for x in self.claims.values()]
        db.boxes.update_one({"_id": self._id}, {"$set": {"checks": all_checks}})

    def update_claim_by_name(self, name: str, team_id: int) -> bool:
        """Update a claim's team_id by claim name."""
        for claim in self.claims.values():
            if claim.name == name:
                claim.team_id = team_id
                return True
        return False

    def update_claim_by_path(self, path: str, team_id: int) -> bool:
        """Update a claim's team_id by path (O(1) lookup)."""
        if path in self.claims:
            self.claims[path].team_id = team_id
            return True
        return False

    def get_claim_by_path(self, path: str) -> ClaimCheck | None:
        """Get a claim by its path (O(1) lookup)."""
        return self.claims.get(path)

    def get_claim_by_name(self, name: str) -> ClaimCheck | None:
        """Get a claim by its name."""
        for claim in self.claims.values():
            if claim.name == name:
                return claim
        return None

DEBUG = 1

CHECK_MAP = {"web": WebCheck, "claim": ClaimCheck, "ssh": SSHCheck, "rdp": RDPCheck, "mysql": MySQLCheck, "ftp": FTPCheck, "charon": CustomCharonCheck}

# Create box
def create_box(db: Database, box: Box) -> None:
    try:
        db.boxes.insert_one(box.to_dict())
        if DEBUG:
            print(f"Created box: {box.name}")
    except Exception as e:
        print("Error adding box:", e)
# Parse box config

def parse_box_config(config: dict) -> dict[str, Box]:
    boxes: dict[str, Box] = {}
    for entry in config["boxes"]:
        checks: list[Check] = []
        claims: dict[str, ClaimCheck] = {}
        for check in entry["checks"]:
            for key, value in check.items():
                check_obj = CHECK_MAP[key](**(value), credentials=config["creds"])
                if key == "claim":
                    claims[check_obj.path] = check_obj
                else:
                    checks.append(check_obj)
        box = Box(entry["id"], name=entry["name"], ip=entry["ip"], checks=checks, claims=claims)
        boxes[box.name] = box
    return boxes

# Create box from config
def create_boxes_from_config(config: dict, db: Database) -> None:
    boxes: dict[str, Box] = parse_box_config(config)
    for box in boxes.values():
        create_box(db, box)


def get_all_services(boxes: dict[str, Box]) -> dict[int, dict[str, bool]]:
    return {box._id: [check.__dict__ for check in box.checks] for box in boxes.values()}

def get_all_claims(boxes: dict[str, Box]) -> dict[int, dict[str, int]]:
    return {box._id: [claim.__dict__ for claim in box.claims.values()] for box in boxes.values()}

def get_all_checks(boxes: dict[str, Box]) -> dict[int, list[dict[str, str | int | bool]]]:
    return {box._id: [check.__dict__ for check in box.checks] + [claim.__dict__ for claim in box.claims.values()] for box in boxes.values()}
# # move to frontend
# def get_root_flag(box: Box) -> Flag | None:
#     for check, details in box["checks"].items():
#         if check == "claim" and details["owner"] and details["team_id"] != -1:
#             return 
#     return None

# # probably for displaying in team dashboard; move to frontend
# def get_all_claim_by_team(boxes: list[Box], team_id: int) -> list[(Flag, bool)]:
#     claim_flags = []
#     for box in boxes:
#         valid: bool = all([details["last"] for check, details in box["checks"] if check != "claim"])
#         root_flag = get_root_flag(box)
#         if not root_flag:
#             for claim in:
#                 if flag["team_id"] == team_id:
#                     claim_flags.append((flag, valid))
#         else:
#             if root_flag["team_id"] == team_id:
#                 claim_flags.append((flag, valid))
#     return claim_flags

def get_box_by_id(db: Database, id: int) -> Box:
    return Box(db.teams.find_one({"_id": id}))

def get_all_boxes(db: Database) -> dict[str, Box]: 
    boxes: dict[str, Box] = {}
    for box in db.boxes.find({}):
        checks: list[Check] = []
        claims: dict[str, ClaimCheck] = {}
        for check in box["checks"]:
            for key, value in check.items():
                check_obj = CHECK_MAP[key](**value)
                if key == "claim":
                    claims[check_obj.path] = check_obj
                else:
                    checks.append(check_obj)
        box_obj = Box(box["_id"], name=box["name"], ip=box["ip"], checks=checks, claims=claims)
        boxes[box_obj.name] = box_obj
    return boxes

def get_all_claim_box_mapping(boxes: list[Box]) -> dict[int, ClaimCheck]:
    pass    
