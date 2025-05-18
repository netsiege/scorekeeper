from utils.checks.check import Check

DEBUG = 1


class TEMPLATECheck(Check):
    def __init__(self, name: str = "TEMPLATE", port: int=999999, credentials: dict = {}, last: bool = False):

        super().__init__(name, port, last, credentials)
    
    def to_dict(self):
        return {"TEMPLATE": self.__dict__}
    

    def run(self, ip: str, timeout: int = 30) -> bool:
        pass