from utils.checks.check import Check

class WebCheck(Check):
    def __init__(self, name: str, port: int, regex: str, path: str):
        self.regex = regex
        self.path = path

        super().__init__(name, port)

    def run(ip: str) -> bool:
        pass

