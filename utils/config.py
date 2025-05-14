import yaml

class ConfigException(Exception):
    pass

def read_config(path: str) -> dict:
    with open(path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def read_boxes(config: dict) -> dict:
    return config["boxes"]

def check_configs(config: dict) -> None:
    # Check teams config
    for entry in config["teams"]:
        if "id" not in entry or "name" not in entry or "password" not in entry or not entry["name"] or not entry["password"] or not entry["id"]:
            raise ConfigException("Incorrect team configuration")
    
    # Check box config
    for entry in config["boxes"]:
        pass # TODO

