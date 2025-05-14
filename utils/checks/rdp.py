
from utils.checks.check import Check
import requests
import paramiko
import subprocess

DEBUG = 1


class RDPCheck(Check):
    def __init__(self, name: str = "rdp", port: int=3389, domain: str="", credentials: dict = {}, cred_list: str="default", last: bool = True):
        self.domain = domain
        self.cred_list = cred_list

        super().__init__(name, port, last, credentials)
    
    def to_dict(self):
        return {"rdp": self.__dict__}
    

    def run(self, ip: str, timeout: int = 1) -> bool:
        if DEBUG:
            print(f"Running rdp check for {self.name} on {ip}")
        client = paramiko.client.SSHClient()
        try:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            for username, password in self.credentials[self.cred_list].items():
                if DEBUG:
                    print(f"Attempting to connect to user {username} using password {password} on {ip}")
                command = [
                    'xfreerdp',
                    f'/v:{ip}',
                    f'/u:{username}',
                    f'/p:{password}',
                    '/cert:ignore',
                    '/log-level:ERROR',
                    '/sec:nla',
                ]
                if self.domain:
                    command.append(f'/d:{self.domain}')
                result = subprocess.run(command, capture_output=True, timeout=timeout, text=True)
                if result.returncode == 0:
                    self.last = True
                    return True
                else:
                    self.last = False
                    return False
        except:
            self.last = False
            return False
        self.last = False
        return False
    