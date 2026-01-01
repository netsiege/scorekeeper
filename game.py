from utils.db.round import Round
from pymongo.database import Database
from utils.db.teams import get_all_teams, rotate_all_team_tokens, get_team_by_id, get_team_token_mapping, get_team_points_mapping, Team
from utils.db.boxes import get_all_boxes, get_all_claims, get_all_services, Box
from utils.checks.claim import ClaimCheck
from utils.task_queue import task_queue, TASK_TYPES
import requests
import json


DEBUG = 1


class FrontendError(Exception):
    pass


class Game:
    def __init__(self, db: Database, round: Round, timeout: int = 2, interval: int = 600, jitter: int = 120, endpoint: str = ""):
        self.db: Database = db
        self.round: Round = round
        self.teams: list[Team] = get_all_teams(self.db)
        self.boxes: list[Box] = get_all_boxes(self.db)
        self.timeout = timeout
        self.interval = interval
        self.jitter = jitter
        self.frontend = endpoint
        self.headers = {'Content-type': 'application/json'}
        # Load task types from config
        task_queue.load_task_types("tasks.json")
    
    def upload_tasks_to_boxes(self) -> None:
        """Upload tasks to each box's task queue."""
        for box in self.boxes:
            hostname = box.name
            # Add all available task types to each box's queue
            for task in TASK_TYPES:
                task_queue.add_task(hostname, task.copy())
            if DEBUG:
                print(f"Uploaded {len(TASK_TYPES)} tasks to {hostname}")
    
    def get_box_tasks(self, hostname: str) -> list[dict]:
        """Get pending tasks for a specific box."""
        return task_queue.get_tasks(hostname)
    
    def process_claim(self, hostname: str, claim_data: dict) -> bool:
        """
        Process a claim submission and remove the task from the queue.
        Returns True if task was successfully removed.
        """
        task_type = claim_data.get('task_type') or claim_data.get('type')
        if task_type:
            removed = task_queue.remove_task_by_type(hostname, task_type)
        else:
            removed = task_queue.remove_task(hostname, 0)
        return removed is not None
    
    def save_round(self) -> None:
        self.round.teams_to_save(self.teams)
        self.round.boxes_to_save(self.boxes)
        self.round.update_db(self.db)
    
    def sync(self) -> None:
        self.teams = get_all_teams(self.db)
        self.boxes = get_all_boxes(self.db)

    def rotate_team_tokens(self):
        rotate_all_team_tokens(self.teams)
    
    def update_db(self):
        for team in self.teams:
            team.update_db(self.db)
        for box in self.boxes:
            box.update_db(self.db)

    def send_claims(self):
        res = requests.post(f"{self.frontend}/update/claims", data=json.dumps(get_all_claims(self.boxes)), headers=self.headers)
        if not res.ok:
            raise FrontendError("Could not send claim data to the frontend")

    def send_services(self):
        print(get_all_services(self.boxes))
        res = requests.post(f"{self.frontend}/update/services", data=json.dumps(get_all_services(self.boxes)), headers=self.headers)
        if not res.ok:
            raise FrontendError("Could not send service data to the frontend")
        
    # def send_tokens(self):
    #     res = requests.post(f"{self.frontend}/update/tokens", data=json.dumps(get_team_token_mapping(self.teams)), headers=self.headers)
    #     if not res.ok:
    #         raise FrontendError("Could not send team token data to the frontend")
        
    # def send_points(self):
    #     res = requests.post(f"{self.frontend}/update/points", data=json.dumps(get_team_points_mapping(self.teams)), headers=self.headers)
    #     if not res.ok:
    #         raise FrontendError("Could not send team score data to the frontend")
    def send_teams(self):
        res = requests.post(f"{self.frontend}/update/teams", data=json.dumps([team.to_dict_frontend() for team in self.teams]), headers=self.headers)
        if not res.ok:
            raise FrontendError("Could not send team data to frontend")


    def check_all_and_update(self):
        if DEBUG:
            print("Running all checks")
        for box in self.boxes:
            services = 1
            team_update = {}
            owner = tuple()
            for check in box.checks:
                if type(check) is ClaimCheck:
                    check.run(box.ip, self.teams)
                    if check.team_id != -1:
                        if check.owner:
                            owner = (check.team_id, check.value)
                        else:
                            team_update[check.team_id] = check.value if check.team_id not in team_update else team_update[check.team_id] + check.value
                else:
                    services &= check.run(box.ip)
            if services:
                if owner:
                    team = get_team_by_id(self.teams, owner[0])
                    team.modify_team_points(owner[1])
                else:
                    for team_id, value in team_update.items():
                        team = get_team_by_id(self.teams, team_id)
                        team.modify_team_points(value)
        
                    

                