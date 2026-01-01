from utils.checks.check import Check
from utils.db.teams import Team
import socket

DEBUG = 1

class ClaimCheck(Check):
    def __init__(self, name: str = "flag", port: int = 1550, path: str = "/ctrl.txt", owner: bool = False, value: int = 2, team_id: int = -1, credentials: dict = {}, last: bool = True):
        self.path = path
        self.owner = owner
        self.value = value
        self.team_id = team_id

        super().__init__(name, port, last)
    
    def to_dict(self):
        return {"claim": self.__dict__}
    
    # ':/et/flat/path'

    def run(self, ip: str, teams: list[Team], timeout: int = 1) -> bool: 
        if DEBUG:
            print(f"Running claim check for {self.name} on {ip}")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            try:
                s.connect((ip,self.port))   
                s.send(f"{self.path}".encode("utf-8"))
            except:
                self.team_id = -1
                if DEBUG:
                    print("Could not communicate with Tally")
                return True
            try:
                response = s.recv(1024)
                response = str(response, 'utf-8')
            except:
                if DEBUG:
                    print("No new token")
                return True
        # Responses no longer need to be hashed - direct token matching
        team_id = self.verify_token(response, teams)
        self.team_id = team_id
        if DEBUG:
            print(f"Team {team_id} claimed {self.name} on {ip}!")
        return True

    def verify_token(self, response: str, teams: list[Team]):
        """
        Verify the token directly without hashing.
        The response should contain the raw team token.
        """
        response = response.strip()
        for team in teams:
            for token in (team.token, team.cached_token):
                if response == token:
                    return team._id
        return self.team_id
