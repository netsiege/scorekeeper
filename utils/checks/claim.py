from utils.checks.check import Check
from utils.db.teams import Team
import socket
import hashlib

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
            try:
                s.settimeout(timeout)
                s.connect((ip,self.port))   
                s.send(f"{self.path}".encode("utf-8"))
                challenge = s.recv(1024)
                challenge = str(challenge, 'utf-8')
            except:
                return True
        print(challenge)
        if not challenge:
            return True
        else:
            team_id = self.verify_token(challenge, teams)
            self.team_id = team_id
            if DEBUG:
                print(f"Team {team_id} claimed {self.name} on {ip}!")
        return True

    def verify_token(self, challenge: str, teams: list[Team]):
        for team in teams:
            hasher =  hashlib.sha1()
            hash_string = f"{team.token}:{self.path}"
            hasher.update(hash_string.encode('utf-8'))
            if challenge == hasher.hexdigest():
                return team._id
        return self.team_id
