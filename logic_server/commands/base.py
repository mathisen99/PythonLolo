from shared.logger import setup_logger
from .decorator import command
import time

logger = setup_logger("commands")

START_TIME = time.time()

@command("about")
def about_command(*args):
    """Show information about the bot."""
    return "PythonLolo IRC Bot - by Mathisen | https://github.com/mathisen99 | Type !help for commands."

@command("uptime")
def uptime_command(*args):
    """Show bot uptime."""
    uptime = int(time.time() - START_TIME)
    h, m, s = uptime // 3600, (uptime % 3600) // 60, uptime % 60
    return f"Uptime: {h}h {m}m {s}s"

@command("ping")
def ping_command(*args):
    """Ping the bot."""
    return "pong"

@command("commands")
def commands_command(*args):
    """Alias for !help."""
    from .decorator import COMMANDS
    names = sorted(COMMANDS.keys())
    return f"Available commands: {', '.join(names)}"

@command("reload")
def reload_command(channel, *args):
    """Reload all command modules (admin only)."""
    # This is a stub; actual reload logic is handled by !admin plugin reload
    return "Use !admin plugin reload <name> to reload plugins."

@command("status")
def status_command(*args):
    """Show bot status."""
    from .decorator import COMMANDS
    loaded_cmds = ', '.join(sorted(COMMANDS.keys()))
    return f"Status: {len(COMMANDS)} commands loaded."

@command("version")
def version_command(*args):
    """Show bot version (from VERSION file only)."""
    version = None
    try:
        with open("VERSION", "r") as f:
            version = f.read().strip()
    except Exception:
        version = None
    if version:
        return f"Version: {version}"
    else:
        return "Version: unknown"

@command("echo")
def echo_command(channel, *args):
    """Echo back the input."""
    return ' '.join(args) if args else "Usage: !echo <text>"

@command("say")
def say_command(channel, *args):
    """Make the bot say something in a channel or private message. Usage: !say <target> <message>"""
    if len(args) < 2:
        return "Usage: !say <target> <message>"
    target = args[0]
    message = ' '.join(args[1:])
    # Special marker for the IRC bot to send to a specific target
    return f"__PRIVMSG__::{target}::{message}"

@command("join")
def join_command(channel, *args):
    """Make the bot join a specified channel. Usage: !join <#channel>"""
    if len(args) != 1 or not args[0].startswith("#"):
        return "Usage: !join <#channel>"
    target = args[0]
    # Special marker for the IRC bot to join a channel
    return f"__JOIN__::{target}"

@command("part")
def part_command(channel, *args):
    """Make the bot leave a specified channel. Usage: !part <#channel>"""
    if len(args) != 1 or not args[0].startswith("#"):
        return "Usage: !part <#channel>"
    target = args[0]
    # Special marker for the IRC bot to part a channel
    return f"__PART__::{target}"
