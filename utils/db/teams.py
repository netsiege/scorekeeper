from pymongo.database import Database
import uuid

class Team:
    def __init__(self, id, name="", password="", points=0, token=""):
        self._id: int = id
        self.name: str = name
        self.password: str = password
        self.points: int = points
        self.token: str = token
        self.cached_token: str = ""
    

    def update_db(self, db: Database):
        db.teams.update_one({"_id": self._id}, {"$set": {"token":self.token, "points": self.points}})

    def rotate_team_token(self) -> None:
        self.cached_token = self.token
        self.token = str(uuid.uuid4())

    def modify_team_points(self, increment: int) -> None:
        self.points += increment

    def to_dict_frontend(self):
        keep = ["_id", "name", "points", "token"]
        return {key:value for key, value in self.__dict__ if key in keep}
        # keep = ["name", "points", "token"]s
        # return {self._id : {key:value for key, value in self.__dict__ if key in keep}}
DEBUG = 1


def create_team(db: Database, team: Team) -> None:
    try:
        db.teams.insert_one(team.__dict__)
        if DEBUG:
            print(f"Created team: {team.name}")
    except Exception as e:
        print("Error adding team:", e)

def parse_team_config(config: dict) -> list[Team]:
    teams: list[Team] = []
    for entry in config["teams"]:
        teams.append(Team(entry["id"], name=entry["name"], password=entry["password"], points=0, token=""))

    return teams

def create_teams_from_config(config: dict, db: Database) -> None:
    teams: list[Team] = parse_team_config(config)
    for team in teams:
        create_team(db, team)

def get_all_teams(db: Database) -> list[dict]:
    return [Team(team["_id"], name=team["name"], password=team["password"], points=team["points"], token=team["token"]) for team in db.teams.find({})]

def get_team_by_id(teams: list[Team], id: int) -> Team:
    for team in teams:
        if team._id == id:
            return team



def get_team_token_mapping(teams: list[Team]) -> dict[str, int]:
    return {team._id: team.token for team in teams}

def get_team_points_mapping(teams: list[Team]) -> dict[str, int]:
    return {team._id: team.points for team in teams}



def rotate_all_team_tokens(teams: list[Team]) -> None:
    for team in teams:
        team.rotate_team_token()
