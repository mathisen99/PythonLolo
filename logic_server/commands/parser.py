from typing import Optional
from config import BOT_NICK
from shared.logger import setup_logger
from logic_server.db import get_prefix, is_command_enabled
from .decorator import COMMANDS
from logic_server.ai.gemini import get_intelligent_response

logger = setup_logger("commands")

async def handle_line(line: str) -> Optional[str]:
    """
    Process a raw IRC PRIVMSG line and return a response if a command is detected.
    """
    try:
        content = line.split(" :", 1)[1].strip()
    except IndexError:
        content = ""
    # parse IRC target and prefix
    parts_line = line.split()
    target = parts_line[2] if len(parts_line) >= 4 and parts_line[1] == "PRIVMSG" else None
    prefix = get_prefix(target) if target else "!"
    # prefix-based commands
    if content.startswith(prefix):
        parts_cmd = content[len(prefix):].split()
        if not parts_cmd:
            return None
        cmd = parts_cmd[0]
        args = parts_cmd[1:]
        # channel-specific enable check
        if not is_command_enabled(target, cmd):
            return f"Command {cmd} is disabled in {target}"
        handler = COMMANDS.get(cmd)
        if handler:
            try:
                return handler(target, *args)
            except Exception as e:
                logger.error(f"Error executing command {prefix}{cmd}: {e}")
                return f"Error executing command {prefix}{cmd}"
    # AI invocation on mention
    if BOT_NICK in content:
        prompt = content.replace(BOT_NICK, "").strip()
        try:
            # get AI response, return raw
            resp = get_intelligent_response(prompt)
            return resp
        except Exception as e:
            logger.error(f"AI error for prompt {prompt}: {e}")
            return "Error generating AI response"
    return None
