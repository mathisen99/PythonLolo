from shared.logger import setup_logger
from .decorator import command
from logic_server.db import get_prefix, set_prefix

logger = setup_logger("commands")

@command("prefix")
def prefix_handler(channel: str, *args) -> str:
    if not args:
        return f"Current prefix is '{get_prefix(channel)}'"
    if len(args) == 2 and args[0] == "set":
        new = args[1]
        set_prefix(channel, new)
        return f"Prefix set to '{new}' for {channel}"
    return "Usage: !prefix set <new_prefix>"
