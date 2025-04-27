from shared.logger import setup_logger
from .decorator import command, COMMANDS

logger = setup_logger("commands")

@command("help")
def help_command(*args) -> str:
    """List all registered commands"""
    names = sorted(COMMANDS.keys())
    return f"Available commands: {', '.join(names)}"
