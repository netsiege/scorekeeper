from utils.db.teams import Team

DEBUG = 1

class Claim:
    def __init__(self, name: str = "flag",  path: str = "/ctrl.txt", owner: bool = False, value: int = 2, team_id: int = -1, last: bool = True):
        self.path = path
        self.owner = owner
        self.value = value
        self.team_id = team_id
        self.name = name
        self.last = last
    
    def to_dict(self):
        return {self.path: self.__dict__}

    def verify_token(self, response: str, teams: list[Team]):
        """
        Verify the token directly without hashing.
        The response should contain the raw team token.
        """
        response = response.strip()
        for team in teams:
            for token in (team.token, team.cached_token):
                if response == token:
                    return team._id
        return self.team_id
