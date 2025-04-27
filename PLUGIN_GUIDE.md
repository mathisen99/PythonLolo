# Plugin Creation Guide

This guide explains how to create new plugins for **Lolo** (Python IRC bot).

## 1. Create a Plugin File
- Place your plugin in the `logic_server/plugins/` directory.
- File name should be `<plugin_name>.py`.

## 2. Import Required Modules
```python
from shared.logger import setup_logger
from logic_server.commands import command
```
- `setup_logger` initializes a logger for your plugin.
- `command` is the decorator to register your command with the bot.

## 3. Define Your Command Handler
```python
logger = setup_logger("plugins.<plugin_name>")

@command("<command_name>")
def <command_function>(channel: str, *args) -> str:
    """Short description of what the command does."""
    # args is a tuple of parameters passed by the user
    # implement your logic here
    return "Your response here"
```
- The first argument `channel` is where the command was invoked.
- `args` contains user-supplied parameters.
- Return a string which will be sent back to the IRC channel or PM.

## 4. (Optional) External Dependencies
If your plugin needs external libraries:
- Add them to `requirements.txt` or install them in your environment.
- Handle import errors gracefully and log failures.

## 5. Plugin Management & Loading
- On logic server startup, all `.py` files in `logic_server/plugins/` are auto-discovered and imported.
- Plugins can be managed at runtime with admin commands:
  - `!admin plugin list` — List loaded plugins
  - `!admin plugin load <plugin>` — Load a plugin
  - `!admin plugin reload <plugin>` — Reload a plugin
  - `!admin plugin unload <plugin>` — Unload a plugin
- **Download plugins from a URL:**
  - `!admin plugin get <url>` — Download and load a plugin from a remote Python file URL

## 6. Example Plugins

### Time Plugin (`time.py`)
```python
from shared.logger import setup_logger
from logic_server.commands import command
from datetime import datetime

logger = setup_logger("plugins.time")

@command("time")
def time_command(channel: str, *args) -> str:
    """Returns the current server time."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"Current time: {now}"
```

### Weather Plugin (`weather.py`)
```python
from shared.logger import setup_logger
from logic_server.commands import command
from urllib.request import urlopen
from urllib.parse import quote_plus

logger = setup_logger("plugins.weather")

@command("weather")
def weather_command(channel: str, *args) -> str:
    """Fetches current weather for a specified location using wttr.in."""
    if not args:
        return "Usage: !weather <location>"
    location = " ".join(args)
    try:
        url = f"http://wttr.in/{quote_plus(location)}?format=3"
        with urlopen(url) as resp:
            data = resp.read().decode().strip()
        return data
    except Exception as e:
        logger.error(f"Weather lookup failed for {location}: {e}")
        return f"Error fetching weather for {location}"
```

## 7. Best Practices & Troubleshooting
- Use logging for errors and debugging (`setup_logger`).
- Handle exceptions gracefully to avoid crashing the logic server.
- Test your plugin by reloading or unloading/reloading at runtime.
- If a plugin fails to load, check the server logs for error messages.
- Keep plugin dependencies minimal and document any requirements.

---
Happy coding! Create awesome plugins!
