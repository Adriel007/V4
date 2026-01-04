from enum import Enum
class Colors:
    BLUE = "\033[1;34m"
    GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    RESET = "\033[0m"
    CLEAR_LINE = "\r\033[K"

class Chat(Enum):
    WEB = "web"
    CLI = "cli"

class Mode(Enum):
    VOICE = "voice"
    VOICE_BETTER = "voice_better"
    TEXT = "text"
