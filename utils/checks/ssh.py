
from utils.checks.check import Check
import requests
import paramiko


DEBUG = 1

class SSHCheck(Check):
    def __init__(self, name: str = "ssh", port: int=22, command: str="", regex: str="", credentials: dict = {}, cred_list: str="default", last: bool = True):
        self.command = command
        self.regex = regex
        self.cred_list = cred_list

        super().__init__(name, port, last, credentials)
    
    def to_dict(self):
        return {"ssh": self.__dict__}
    

    def run(self, ip: str, timeout: int = 1) -> bool:
        if DEBUG:
            print(f"Running ssh check for {self.name} on {ip}")
        client = paramiko.client.SSHClient()
        try:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            for username, password in self.credentials[self.cred_list].items():
                if DEBUG:
                    print(f"Attempting to connect to user {username} using password {password} on {ip}")
                client.connect(ip, username=username, password=password, timeout=timeout)
                if self.command:
                    _stdin,_stdout,_stderr = client.exec_command(self.command)
                    client.close()
                    if _stdout.channel.recv_exit_status() != 0:
                        self.last = False
                        return False
                    elif self.regex and self.regex in _stdout.read().decode():
                        self.last = True
                        return True
                    else:
                        self.last = True
                        return True
        except:
            if client:
                client.close()
            self.last = False
            return False
        self.last = False
        return False