import socket 

class CustomCharon:
    def __init__(self, name: str = "charon", port: int = 9131, last: bool = False, credentials: dict = {}):
        self.name = name
        self.port = port
        self.last = last
        self.credentials = credentials

    def to_dict(self):
        return {"charon": self.__dict__}

    def run(self, ip: str) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((ip, self.port))
                s.sendall(b"ping")
                data = s.recv(1024)
                if data == b"pong":
                    return True
            except Exception as e:
                self.last = False
                return False
        
        self.last = True
        return True
