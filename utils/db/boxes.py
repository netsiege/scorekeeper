from typing import TypedDict
from utils.checks.check import Check
from utils.control import Flag

class Box(TypedDict):
    name: str
    ip: str
    control: list[Flag]
    checks: list[Check]

