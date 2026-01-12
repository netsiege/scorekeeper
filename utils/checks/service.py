class Service:
    def __init__(self, name: str, port: int, last: bool, credentials: dict = {}):
        self.name = name
        self.port = port
        self.last = last
        self.credentials = credentials
    def to_dict(self):
        return {self.name: self.__dict__}
    def run(self, ip: str) -> bool:
        pass
        
