from utils.checks.check import Check

class WebCheck(Check):
    def __init__(self, name: str = "web", port: int=80, regex: str="", path: str="/", last: bool = True):
        self.regex = regex
        self.path = path

        super().__init__(name, port, last)
    
    def to_dict(self):
        return {"web": self.__dict__}

    def run(self, ip: str) -> bool:
        return True

