from shared.logger import setup_logger
from logic_server.commands import command

logger = setup_logger("plugins.echo")

@command("echo")
def echo_command(channel: str, *args) -> str:
    """Echo command: repeats the provided arguments back to the user."""
    logger.info(f"Echo command called with args: {args}")
    if not args:
        return "Usage: !echo <text>"
    return ' '.join(args)
