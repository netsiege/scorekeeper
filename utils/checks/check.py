class Check:
    def __init__(self, name: str, port: int, last: bool, credentials: dict = {}):
        self.name = name
        self.port = port
        self.last = last
        self.credentials = credentials
    def _to_dict(self):
        pass
    def run(self, ip: str) -> bool:
        pass
        
