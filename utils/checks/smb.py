from utils.checks.check import Check
from smb.SMBConnection import SMBConnection
import socket

DEBUG = 1


class SMBCheck(Check):
    def __init__(self, name: str = "smb", port: int = 445, share: str = "", path: str = "/", regex: str = "", credentials: dict = {}, cred_list: str = "default", last: bool = False):
        self.share = share
        self.path = path
        self.regex = regex
        self.cred_list = cred_list

        super().__init__(name, port, last, credentials)
    
    def to_dict(self):
        return {"smb": self.__dict__}
    

    def run(self, ip: str, timeout: int = 5) -> bool:
        if DEBUG:
            print(f"Running SMB check for {self.name} on {ip}")
        
        try:
            for username, password in self.credentials[self.cred_list].items():
                if DEBUG:
                    print(f"Attempting to connect to SMB as {username} on {ip}")
                
                # Create SMB connection
                conn = SMBConnection(
                    username,
                    password,
                    "scorekeeper",  # client machine name
                    ip,             # server name
                    use_ntlm_v2=True,
                    is_direct_tcp=True
                )
                
                # Connect to the server
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                sock.connect((ip, self.port))
                
                connected = conn.connect(sock, ip, self.port)
                
                if not connected:
                    if DEBUG:
                        print(f"Failed to authenticate as {username}")
                    sock.close()
                    continue
                
                if DEBUG:
                    print(f"Connected to SMB as {username}")
                
                # If a share is specified, try to list it
                if self.share:
                    try:
                        files = conn.listPath(self.share, self.path)
                        if DEBUG:
                            print(f"Successfully listed {len(files)} items in {self.share}{self.path}")
                        
                        if self.regex:
                            import re
                            found = False
                            for f in files:
                                if re.search(self.regex, f.filename):
                                    found = True
                                    break
                            self.last = found
                        else:
                            self.last = True
                    except Exception as e:
                        if DEBUG:
                            print(f"Failed to list share {self.share}: {e}")
                        self.last = False
                else:
                    # Just list available shares
                    try:
                        shares = conn.listShares()
                        if DEBUG:
                            print(f"Found {len(shares)} shares")
                        self.last = True
                    except Exception as e:
                        if DEBUG:
                            print(f"Failed to list shares: {e}")
                        self.last = False
                
                conn.close()
                sock.close()
                
                if not self.last:
                    if DEBUG:
                        print("SMB check failed")
                    return False
                
                if DEBUG:
                    print("SMB check passed!")
                return self.last
                
        except Exception as e:
            if DEBUG:
                print(f"SMB check failed with exception: {e}")
            self.last = False
            return False
        
        self.last = False
        if DEBUG:
            print("SMB check failed - no valid credentials")
        return False
