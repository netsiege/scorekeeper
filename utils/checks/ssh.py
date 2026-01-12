
from utils.checks.service import Service
import requests
import paramiko
import re


DEBUG = 1

class SSHCheck(Service):
    def __init__(self, name: str = "ssh", port: int=22, command: str="", regex: str="", credentials: dict = {}, cred_list: str="default", last: bool = False):
        self.command = command
        self.regex = regex
        self.cred_list = cred_list

        super().__init__(name, port, last, credentials)
    
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
                    if _stdout.channel.recv_exit_status() != 0:
                        self.last = False
                    elif self.regex:
                        self.last = bool(re.search(self.regex, _stdout.read().decode()))
                    else:
                        self.last = True
                else:
                    self.last = True
                if not self.last:
                    if client:
                        client.close()
                    if DEBUG:
                        print("SSH check failed")
                    return False
        except:
            if client:
                client.close()
            self.last = False
            if DEBUG:
                print("SSH check failed")
            return False

        if client:
            client.close()
        if DEBUG:
            print("SSH check passed!") if self.last else print("SSH check failed")
        return self.last
