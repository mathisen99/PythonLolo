from shared.logger import setup_logger
logger = setup_logger("commands")

from .decorator import COMMANDS, command
# import submodules to register commands
from .test import *
from .help import *
from .admin import *
from .prefix import *
from .disable import *
from .enable import *
from .base import *
from .parser import handle_line

# Dynamically load plugin modules
import pkgutil
import importlib
import logic_server.plugins as plugins

for finder, name, _ in pkgutil.iter_modules(plugins.__path__):
    try:
        importlib.import_module(f"logic_server.plugins.{name}")
        logger.info(f"Plugin loaded: {name}")
    except Exception as e:
        logger.error(f"Failed to load plugin {name}: {e}")
