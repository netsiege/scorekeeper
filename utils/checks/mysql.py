from utils.checks.service import Service
import mysql.connector
DEBUG = 1


class MySQLCheck(Service):
    def __init__(self, name: str = "mysql", port: int=3306, credentials: dict = {}, cred_list: str = "default", last: bool = False):
        self.cred_list = cred_list

        super().__init__(name, port, last, credentials)
    def to_dict(self):
        data = self.__dict__.copy()
        # data.pop('credentials', None)
        return {"mysql": data}
    
    def run(self, ip: str, timeout: int = 5) -> bool:
        for username, password in self.credentials[self.cred_list].items(): 
            try:
                if DEBUG:
                    print(f"Attempting to connect to MySQL database on {ip} with user {username} using password {password}")
                connection = mysql.connector.connect(
                    host=ip,
                    user=username,
                    password=password,
                    port=self.port,
                    connection_timeout=timeout
                )
                if connection.is_connected():
                    connection.close()
                    self.last = True
                else:
                    self.last = False
                    if DEBUG:
                        print("MySQL check failed")
                    return False
            except Exception as e:
                if DEBUG:
                    print(e)
                    print("MySQL check failed")
                self.last = False
                return False
        print("MySQL check passed!") if self.last else print("MySQL check failed")
        return self.last
