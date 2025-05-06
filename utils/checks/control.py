from utils.checks.check import Check
import socket

class ControlCheck(Check):
    def __init__(self, name: str = "flag", port: int = 1550, path: str = "/ctrl.txt", owner: bool = 0, value: int = 2, team_id: int = -1, last: bool = True):
        self.path = path
        self.owner = owner
        self.value = value
        self.team_id = team_id

        super().__init__(name, port, last)
    
    def to_dict(self):
        return {"control": self.__dict__}
    
    def run(self, ip: str, tokens: list[str]) -> bool:
        # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # s.connect((ip,self.port))   
        # s.send(f"{self.path}")
        # print(s.recv(1024))
        # s.close()
        self.team_id = 1

    def verify_token(self, challenge: str):
        pass
