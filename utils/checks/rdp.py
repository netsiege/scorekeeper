
from utils.checks.service import Service
import subprocess

DEBUG = 1


class RDPCheck(Service):
    def __init__(self, name: str = "rdp", port: int=3389, domain: str="", credentials: dict = {}, cred_list: str="default", last: bool = False):
        self.domain = domain
        self.cred_list = cred_list

        super().__init__(name, port, last, credentials)
    
    def to_dict(self):
        data = self.__dict__.copy()
        # data.pop('credentials', None)
        return {"rdp": data}
    
    def run(self, ip: str, timeout: int = 10) -> bool:
        if DEBUG:
            print(f"Running rdp check for {self.name} on {ip}")
            print(self.credentials)
        try:
            for username, password in self.credentials[self.cred_list].items():
                if DEBUG:
                    print(f"Attempting to connect to user {username} using password {password} on {ip}")
                command = [
                    'xvfb-run',
                    '-a',
                    'xfreerdp',
                    '+auth-only',
                    f'/v:{ip}',
                    f'/u:{username}',
                    f'/p:{password}',
                    '/cert:ignore',
                    '/log-level:INFO'
                ]
                if self.domain:
                    command.append(f'/d:{self.domain}')
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                while process.returncode is None:
                    process.poll()
                if process.returncode == 0:
                    self.last = True
                else:
                    self.last = False
                    if DEBUG:
                        print("RDP check failed")
                    return False
        except Exception as e:
            print(e)
            self.last = False
        print("RDP check passed!") if self.last else print("RDP check failed")
        return self.last
    
