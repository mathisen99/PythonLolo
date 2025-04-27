from shared.logger import setup_logger
from .decorator import command

logger = setup_logger("commands")

@command("test")
def test_command(*args) -> str:
    logger.info("Received !test command")
    return "Test successful!"
