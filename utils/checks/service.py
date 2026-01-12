class Service:
    def __init__(self, name: str, port: int, last: bool, credentials: dict = {}):
        self.name = name
        self.port = port
        self.last = last
        self.credentials = credentials
    def to_dict(self):
        data = self.__dict__.copy()
        data.pop('credentials', None)
        return {self.name: data}
    def run(self, ip: str) -> bool:
        pass
        
