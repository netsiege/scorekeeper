from utils.db.round import Round
from pymongo.database import Database
from utils.db.teams import get_all_teams, rotate_all_team_tokens, get_team_by_id, get_team_token_mapping, get_team_points_mapping, Team
from utils.db.boxes import get_all_boxes, get_all_claims, get_all_services, Box
from utils.checks.claim import Claim
from utils.task_queue import task_queue
import requests
import json


DEBUG = 1


class FrontendError(Exception):
    pass


class Game:
    def __init__(self, db: Database, round: Round, timeout: int = 2, interval: int = 600, jitter: int = 120, endpoint: str = "", phase_config: str = ""):
        self.db: Database = db
        self.round: Round = round
        self.teams: list[Team] = get_all_teams(self.db)
        self.boxes: dict[str, Box] = get_all_boxes(self.db)
        self.timeout = timeout
        self.interval = interval
        self.jitter = jitter
        self.frontend = endpoint
        self.headers = {'Content-type': 'application/json'}
        self.phase_config = phase_config
        # Load box-specific tasks from phase config
        if phase_config:
            task_queue.load_phase_config(phase_config)
    
    def get_box_tasks(self, hostname: str) -> list[dict]:
        """Get pending tasks for a specific box."""
        return task_queue.get_tasks(hostname)
    
    
    def save_round(self) -> None:
        self.round.teams_to_save(self.teams)
        self.round.boxes_to_save(list(self.boxes.values()))
        self.round.update_db(self.db)
    
    def sync(self) -> None:
        self.teams = get_all_teams(self.db)
        self.boxes = get_all_boxes(self.db)

    def rotate_team_tokens(self):
        rotate_all_team_tokens(self.teams)
    
    def update_db(self):
        for team in self.teams:
            team.update_db(self.db)
        for box in self.boxes.values():
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
        

    def send_teams(self):
        res = requests.post(f"{self.frontend}/update/teams", data=json.dumps([team.to_dict_frontend() for team in self.teams]), headers=self.headers)
        if not res.ok:
            raise FrontendError("Could not send team data to frontend")

    def verify_token(self, token: str) -> int | None:
        """
        Verify a token and return the team ID if valid.
        Checks both current token and cached token.
        
        Args:
            token: The token to verify
        
        Returns:
            Team ID if token is valid, None otherwise
        """
        for team in self.teams:
            if token == team.token or token == team.cached_token:
                return team._id
        return None

    def assign_box_team_id(self, hostname: str, token: str, file_path: str) -> int | None:
        """
        Verify token and assign team_id to the corresponding Claim.
        Points are awarded later in check_all_and_update.
        
        Args:
            hostname: The box hostname
            token: The team's token to verify
            file_path: The file path of the Claim to update
        
        Returns:
            team_id if token is valid and check found, None otherwise
        """
        # Verify token first
        team_id = self.verify_token(token)
        if team_id is None:
            if DEBUG:
                print(f"Invalid token: {token}")
            return None
        
        # Find the box by hostname - O(1) lookup
        box = self.boxes.get(hostname)
        if not box:
            if DEBUG:
                print(f"Box {hostname} not found")
            return None
        
        # Update claim team_id using the fast path lookup
        if box.update_claim_by_path(file_path, team_id):
            if DEBUG:
                claim = box.get_claim_by_path(file_path)
                print(f"Assigned team {team_id} to Claim {claim.name} on {hostname}")
            return team_id
        
        if DEBUG:
            print(f"No Claim found with path {file_path} on {hostname}")
        return None

    def check_all_and_update(self):
        if DEBUG:
            print("Running all checks")
        for box in self.boxes.values():
            # Run service checks
            services = 1
            for service in box.services.values():
                services &= service.run(box.ip)
            
            # Process claims if services are up
            if services:
                team_update = {}
                owner = tuple()
                
                for claim in box.claims.values():
                    if claim.team_id != -1:
                        if claim.owner:
                            owner = (claim.team_id, claim.value)
                        else:
                            team_update[claim.team_id] = claim.value if claim.team_id not in team_update else team_update[claim.team_id] + claim.value
                
                if owner:
                    team = get_team_by_id(self.teams, owner[0])
                    team.modify_team_points(owner[1])
                else:
                    for team_id, value in team_update.items():
                        team = get_team_by_id(self.teams, team_id)
                        team.modify_team_points(value)
        
                    

                