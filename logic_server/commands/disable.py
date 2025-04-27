from shared.logger import setup_logger
from .decorator import command
from logic_server.db import disable_command

logger = setup_logger("commands")

@command("disable")
def disable_handler(channel: str, *args) -> str:
    if len(args) != 1:
        return "Usage: !disable <command>"
    cmd_name = args[0]
    disable_command(channel, cmd_name)
    return f"Disabled command '{cmd_name}' in {channel}"
