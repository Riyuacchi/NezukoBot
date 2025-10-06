from datetime import timedelta
import humanize
import re

def format_duration(seconds: int) -> str:
    return humanize.naturaldelta(timedelta(seconds=seconds))

def calculate_level(xp: float) -> int:
    return int((xp / 100) ** 0.5)

def calculate_xp_for_level(level: int) -> int:
    return int((level ** 2) * 100)

def progress_bar(current: int, total: int, length: int = 10) -> str:
    filled = int((current / total) * length)
    bar = "█" * filled + "░" * (length - filled)
    percentage = int((current / total) * 100)
    return f"{bar} {percentage}%"

def parse_time(time_str: str) -> int:
    time_dict = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
    match = re.match(r"(\d+)([smhdw])", time_str.lower())
    if match:
        value, unit = match.groups()
        return int(value) * time_dict[unit]
    return 0

def format_number(num: int) -> str:
    return humanize.intcomma(num)