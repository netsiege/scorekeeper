from utils.checks.service import Service
from utils.checks.web import WebCheck
from utils.checks.claim import Claim
from utils.checks.ssh import SSHCheck
from utils.checks.rdp import RDPCheck
from utils.checks.mysql import MySQLCheck
from utils.checks.ftp import FTPCheck
from utils.checks.smb import SMBCheck
from utils.checks.custom.custom_charon import CustomCharonCheck

from pymongo.database import Database

class Box:
    def __init__(self, id, name="", ip="", services=None, claims=None):
        self._id: int = id
        self.name: str = name
        self.ip: str = ip
        self.services: dict[str, Service] = services if services is not None else {}
        # Claims stored as dict keyed by file_path for O(1) lookup
        self.claims: dict[str, Claim] = claims if claims is not None else {}

    def to_dict(self):
        claims_dict = {}
        for v in self.claims.values():
            claims_dict.update(v.to_dict())
        services_dict = {}
        for v in self.services.values():
            services_dict.update(v.to_dict())
        return {
            "_id": self._id,
            "name": self.name,
            "ip": self.ip,
            "claims": claims_dict,
            "services": services_dict
        }
    
    def update_db(self, db: Database):
        cur = self.to_dict()
        db.boxes.update_one({"_id": self._id}, {"$set": {"services": cur["services"], "claims": cur["claims"]}})

    def update_claim_by_name(self, name: str, team_id: int) -> bool:
        """Update a claim's team_id by claim name."""
        for claim in self.claims.values():
            if claim.name == name:
                claim.team_id = team_id
                return True
        return False

    def update_claim_by_path(self, path: str, team_id: int) -> bool:
        """Update a claim's team_id by path (O(1) lookup)."""
        for claim in self.claims.values():
            if claim.path == path:
                claim.team_id = team_id
                return True
        return False

    def get_claim_by_path(self, path: str) -> Claim | None:
        """Get a claim by its path (O(1) lookup)."""
        return self.claims.get(path)

    def get_claim_by_name(self, name: str) -> Claim | None:
        """Get a claim by its name."""
        for claim in self.claims.values():
            if claim.name == name:
                return claim
        return None

DEBUG = 1

CHECK_MAP = {"web": WebCheck, "claim": Claim, "ssh": SSHCheck, "rdp": RDPCheck, "mysql": MySQLCheck, "ftp": FTPCheck, "smb": SMBCheck}

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
        services: dict[str, Service] = {}
        claims: dict[str, Claim] = {}
        for check in entry["checks"]:
            for key, value in check.items():
                if key != "claim":
                    check_obj = CHECK_MAP[key](**(value), credentials=config["creds"])
                    services[check_obj.name] = check_obj
                else:
                    claim= Claim(**(value))
                    claims[claim.path] = claim
        box = Box(entry["id"], name=entry["name"], ip=entry["ip"], services=services, claims=claims)
        boxes[box.name] = box
    return boxes

# Create box from config
def create_boxes_from_config(config: dict, db: Database) -> None:
    boxes: dict[str, Box] = parse_box_config(config)
    for box in boxes.values():
        create_box(db, box)


def get_all_services(boxes: dict[str, Box]) -> dict[int, dict[str, bool]]:
    return {box._id: {name: service.last for name, service in box.services.items()} for box in boxes.values()}

def get_all_claims(boxes: dict[str, Box]) -> dict[int, dict[str, int]]:
    return {box._id: {path: claim.team_id for path, claim in box.claims.items()} for box in boxes.values()}


def get_box_by_id(db: Database, id: int) -> Box:
    return Box(db.teams.find_one({"_id": id}))

def get_all_boxes(db: Database) -> dict[str, Box]: 
    boxes: dict[str, Box] = {}
    for box in db.boxes.find({}):
        services: dict[str, Service] = {}
        claims: dict[str, Claim] = {}
        for key,value in box["services"].items():
            check_obj = CHECK_MAP[key](**value)
            services[check_obj.name] = check_obj
        for key,value in box["claims"].items():
            claim = Claim(**value)
            if key == "claim":
                claims[claim.path] = claim
        box_obj = Box(box["_id"], name=box["name"], ip=box["ip"], services=services, claims=claims)
        boxes[box_obj.name] = box_obj
    return boxes

def get_all_claim_box_mapping(boxes: list[Box]) -> dict[int, Claim]:
    pass    
