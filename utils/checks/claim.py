from utils.checks.check import Check
from utils.db.teams import Team
import socket
import hashlib

class claimCheck(Check):
    def __init__(self, name: str = "flag", port: int = 1550, path: str = "/ctrl.txt", owner: bool = 0, value: int = 2, team_id: int = -1, last: bool = True):
        self.path = path
        self.owner = owner
        self.value = value
        self.team_id = team_id

        super().__init__(name, port, last)
    
    def to_dict(self):
        return {"claim": self.__dict__}
    
    # ':/et/flat/path'

    def run(self, ip: str, teams: list[Team]) -> bool: 
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip,self.port))   
            s.send(f"{self.path}".encode("utf-8"))
            challenge = str(s.recv(1024), 'utf-8')
        if not challenge:
            return True
        else:
            team_id = self.verify_token(challenge, teams)
            print(team_id)
            self.team_id = team_id
        return True

    def verify_token(self, challenge: str, teams: list[Team]):
        for team in teams:
            hasher =  hashlib.sha1()
            hash_string = f"{team.token}:{self.path}"
            print(hash_string)
            hasher.update(hash_string.encode('utf-8'))
            print(challenge, hasher.hexdigest())
            if challenge == hasher.hexdigest():
                return team._id
        return self.team_id
