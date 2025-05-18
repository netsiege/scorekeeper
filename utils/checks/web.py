from utils.checks.check import Check
import requests

DEBUG = 1

class WebCheck(Check):
    def __init__(self, name: str = "web", port: int=80, regex: str="", path: str="/", credentials: dict = {}, last: bool = False):
        self.regex = regex
        self.path = path

        super().__init__(name, port, last)
    
    def to_dict(self):
        return {"web": self.__dict__}

    def run(self, ip: str, timeout: int = 1) -> bool:
        url = f"http://{ip}:{self.port}{self.path}"
        if DEBUG:
            print(f"Running web check for {self.name} on {url}")
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200: 
                if self.regex:
                    if self.regex in response.text.decode('utf-8'):
                        self.last = True
                    else:
                        self.last = False
                else:
                    self.last = True
        except:
            self.last = False
        return self.last