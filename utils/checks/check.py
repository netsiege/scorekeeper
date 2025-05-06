class Check:
    def __init__(self, name: str, port: int, last: bool):
        self.name = name
        self.port = port
        self.last = last
    def _to_dict(self):
        pass
    def run(self, ip: str) -> bool:
        pass
