from shared.logger import setup_logger

logger = setup_logger("commands")

# Command registry
COMMANDS: dict[str, callable] = {}

def command(name: str):
    """Decorator to register a command handler."""
    def decorator(func: callable):
        COMMANDS[name] = func
        return func
    return decorator
