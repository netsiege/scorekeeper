from utils.checks.service import Service
from ftplib import FTP, error_perm
DEBUG = 1


class FTPCheck(Service):
    def __init__(self, name: str = "ftp", port: int=21, command: str = "LIST", credentials: dict = {}, cred_list: str = "", last: bool = False):
        self.cred_list = cred_list
        self.command = command
        super().__init__(name, port, last, credentials)

    def to_dict(self):
        data = self.__dict__.copy()
        # data.pop('credentials', None)
        return {"ftp": data}

    def run(self, ip: str, timeout: int = 30) -> bool:
        try:
            # Connect to FTP server
            ftp = FTP()
            ftp.connect(ip, self.port, timeout=timeout)
            
            if self.cred_list:
                for username, password in self.credentials.get(self.cred_list, {}).items():
                    ftp.connect(user=username, passwd=password)
                    if DEBUG:
                        print(f"Connected to {ip} as {username}")
            # Login as anonymous
            ftp.login()
            if DEBUG:
                print(f"Connected to {ip} as anonymous.")
            
            # List directory contents
            ftp.retrlines(self.command)
            
            # Quit the session
            ftp.quit()
            
        except error_perm as e:
            self.last = False
            if DEBUG:
                print(f"Permission error: {e}")
            return self.last
        except Exception as e:
            self.last = False
            if DEBUG:
                print(f"Failed to connect to {ip}: {e}")
            return self.last
        self.last = True
        return self.last
