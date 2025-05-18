from utils.checks.check import Check
import mysql.connector
DEBUG = 1


class MySQLCheck(Check):
    def __init__(self, name: str = "mysql", port: int=3306, credentials: dict = {}, cred_list: str = "default", last: bool = False):
        self.cred_list = cred_list

        super().__init__(name, port, last, credentials)


    def to_dict(self):
        return {"mysql": self.__dict__}
    

    def run(self, ip: str, timeout: int = 5) -> bool:
        for username, password in self.credentials[self.cred_list].items(): 
            try:
                connection = mysql.connector.connect(
                    host=ip,
                    user=username,
                    password=password,
                    port=self.port,
                    connection_timeout=timeout
                )
                if connection.is_connected():
                    if DEBUG:
                        print(f"Successfully connected to MySQL database on {ip} with user {username} using password {password}")
                    connection.close()
                    self.last = True
                else:
                    self.last = False
                    return False
            except Exception as e:
                if DEBUG:
                    print(e)
                self.last = False
                return False
        return self.last