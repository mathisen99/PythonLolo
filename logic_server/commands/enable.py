from shared.logger import setup_logger
from .decorator import command
from logic_server.db import enable_command

logger = setup_logger("commands")

@command("enable")
def enable_handler(channel: str, *args) -> str:
    if len(args) != 1:
        return "Usage: !enable <command>"
    cmd_name = args[0]
    enable_command(channel, cmd_name)
    return f"Enabled command '{cmd_name}' in {channel}"
