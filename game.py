from utils.db.round import Round
from pymongo.database import Database
from utils.db.teams import get_all_teams, rotate_all_team_tokens, get_team_by_id, get_team_token_mapping, get_team_points_mapping, Team
from utils.db.boxes import get_all_boxes, get_all_claims, get_all_services, Box
from utils.checks.claim import ClaimCheck
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
        self.boxes: list[Box] = get_all_boxes(self.db)
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
    
    def process_claim(self, hostname: str, claim_data: dict) -> bool:
        """
        Process a claim submission and remove the task from the queue.
        Returns True if task was successfully removed.
        """
        # Try to remove by file_path first (most specific)
        file_path = claim_data.get('file_path') or claim_data.get('path')
        if file_path:
            removed = task_queue.remove_task_by_path(hostname, file_path)
            if removed:
                return True
        
        # Fall back to task type
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

    def award_claim_points(self, hostname: str, token: str, task: dict) -> tuple[int, int | None]:
        """
        Verify token and award points to a team based on a completed claim task.
        
        Args:
            hostname: The box hostname
            token: The team's token to verify
            task: The task that was completed (contains value and owner fields)
        
        Returns:
            Tuple of (points_awarded, team_id) - team_id is None if token invalid
        """
        # Verify token first
        team_id = self.verify_token(token)
        if team_id is None:
            if DEBUG:
                print(f"Invalid token: {token}")
            return (0, None)
        
        value = task.get('value', 1)
        is_owner = task.get('owner', False)
        
        # Check if services are up for this box before awarding points
        box = next((b for b in self.boxes if b.name == hostname), None)
        if not box:
            if DEBUG:
                print(f"Box {hostname} not found")
            return (0, team_id)
        
        # Verify services are running
        services_up = all(
            check.run(box.ip) for check in box.checks 
            if not isinstance(check, ClaimCheck)
        )
        
        if not services_up:
            if DEBUG:
                print(f"Services not up for {hostname}, no points awarded")
            return (0, team_id)
        
        team = get_team_by_id(self.teams, team_id)
        if not team:
            if DEBUG:
                print(f"Team {team_id} not found")
            return (0, team_id)
        
        # Award points
        team.modify_team_points(value)
        if DEBUG:
            if is_owner:
                print(f"Team {team_id} awarded {value} owner points for {hostname}")
            else:
                print(f"Team {team_id} awarded {value} points for {hostname}")
        return (value, team_id)

    def check_all_and_update(self):
        """
        Run all service checks (non-claim checks) for all boxes.
        Claim points are now awarded via the /api/claim endpoint.
        """
        if DEBUG:
            print("Running all service checks")
        for box in self.boxes:
            for check in box.checks:
                # Skip claim checks - they are handled via API
                if not isinstance(check, ClaimCheck):
                    check.run(box.ip)
        
                    

                