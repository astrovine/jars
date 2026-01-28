from pathlib import Path

API_BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"
TOKEN_FILE = Path.home() / ".jars" / "token"


class Theme:
    PRIMARY = "cyan"
    SECONDARY = "bright_blue"
    ACCENT = "green"
    WARNING = "yellow"
    ERROR = "red"
    MUTED = "dim white"
    
    ONLINE = "bold green"
    OFFLINE = "bold red"
    PENDING = "yellow"
    
    BORDER = "bright_black"
    HEADER = "bold cyan"
