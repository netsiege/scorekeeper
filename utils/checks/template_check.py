from utils.checks.service import Service

DEBUG = 1


class TEMPLATECheck(Service):
    def __init__(self, name: str = "TEMPLATE", port: int=999999, credentials: dict = {}, last: bool = False):

        super().__init__(name, port, last, credentials)
    

    def run(self, ip: str, timeout: int = 30) -> bool:
        pass