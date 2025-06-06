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
            data = resp.read().decode('utf-8').strip()
        if channel and channel != '':
            nick_and_location = f"{channel}+{location}".replace('+', ' ')
            if data.lower().startswith(f"{channel.lower()}+{location.lower()}"):
                data = data.replace(f"{channel}+{location}", f"{channel} {location}")
            data = data.replace('+', ' ', 1)
        return data
    except Exception as e:
        logger.error(f"Weather lookup failed for {location}: {e}")
        return f"Error fetching weather for {location}"
