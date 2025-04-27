from shared.logger import setup_logger
from logic_server.commands import command
from datetime import datetime

logger = setup_logger("plugins.time")

@command("time")
def time_command(channel: str, *args) -> str:
    """Returns the current server time."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"Current time: {now}"
