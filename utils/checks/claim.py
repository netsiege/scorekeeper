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
            print(ip, self.port)
            s.connect((ip,self.port))   
            s.send(f"{self.path}".encode("utf-8"))
            challenge = str(s.recv(1024))
        if not challenge:
            return True
        team_id = self.verify_token(challenge, teams)
        self.team_id = team_id

    def verify_token(self, challenge: str, teams: list[Team]):
        for team in teams:
            hasher =  hashlib.sha1()
            hasher.update(team.token.encode('utf-8'))
            if challenge == hasher.hexdigest():
                return team._id
