from utils.db.round import Round
from pymongo.database import Database
from utils.db.teams import get_all_teams, rotate_all_team_tokens, get_team_by_id, Team
from utils.db.boxes import get_all_boxes, Box
from utils.checks.claim import claimCheck

def check_all():
    pass

class Game:
    def __init__(self, db: Database, round: Round):
        self.db: Database = db
        self.round: Round = round
        self.teams: list[Team] = []
        self.boxes: list[Box] = []
    
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

    def check_all_and_update(self):
        for box in self.boxes:
            services = 1
            team_update = {}
            owner = tuple()
            for check in box.checks:
                if type(check) is claimCheck:
                    check.run(box.ip, self.teams)
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
        
                    

                