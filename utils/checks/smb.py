from utils.checks.service import Service
from smb.SMBConnection import SMBConnection
import socket

DEBUG = 1


class SMBCheck(Service):
    def __init__(self, name: str = "smb", port: int = 445, share: str = "", path: str = "/", regex: str = "", credentials: dict = {}, cred_list: str = "default", last: bool = False):
        self.share = share
        self.path = path
        self.regex = regex
        self.cred_list = cred_list

        super().__init__(name, port, last, credentials)


    def run(self, ip: str, timeout: int = 5) -> bool:
        if DEBUG:
            print(f"Running SMB check for {self.name} on {ip}")
        
        try:
            for username, password in self.credentials[self.cred_list].items():
                if DEBUG:
                    print(f"Attempting to connect to SMB as {username} on {ip}")
                
                # Resolve to IPv4 explicitly to avoid EAFNOSUPPORT (Errno 97)
                try:
                    ipv4 = socket.getaddrinfo(ip, None, family=socket.AF_INET)[0][4][0]
                except Exception:
                    ipv4 = ip  # assume already an IPv4 literal

                # Create SMB connection (direct TCP)
                conn = SMBConnection(
                    username,
                    password,
                    "scorekeeper",  # client machine name
                    ipv4,            # remote name
                    use_ntlm_v2=True,
                    is_direct_tcp=True,
                )

                # Let pysmb manage the TCP socket and force IPv4
                connected = conn.connect(ipv4, self.port, timeout=timeout, sock_family=socket.AF_INET)
                
                if not connected:
                    if DEBUG:
                        print(f"Failed to authenticate as {username}")
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
