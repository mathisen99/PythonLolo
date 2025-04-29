
from typing import Optional, Tuple
from config import BOT_NICK
from shared.logger import setup_logger
from logic_server.db import get_prefix, is_command_enabled, get_channel_log_context
from logic_server.ai.ai_config import AI_CONTEXT_LINES
from .decorator import COMMANDS
from logic_server.ai.gemini import get_response_with_function_calling

logger = setup_logger("parser") # Changed logger name for clarity

async def handle_line(line: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Process a raw IRC PRIVMSG line and return a tuple (response, target) if a command is detected
    or if the bot's nick is mentioned (triggering AI).
    """
    try:
        parts = line.split(" ", 3) # :nick!user@host PRIVMSG #channel/#user :message
        if len(parts) < 4 or parts[1] != "PRIVMSG":
            return None, None # Not a valid PRIVMSG line we can handle here

        source = parts[0].lstrip(':') # Remove leading ':' and strip whitespace
        target = parts[2]     # Channel or user the message is sent to
        content = parts[3][1:].strip() # Remove leading ':' and strip whitespace

        is_channel = target.startswith("#") or target.startswith("&") # Add other channel prefixes if needed

        prefix = get_prefix(target) if is_channel else "!" # Default '!' for PMs or if DB fails

        if content.startswith(prefix):
            parts_cmd = content[len(prefix):].split()
            if not parts_cmd:
                return None, target # Just the prefix was typed
            cmd = parts_cmd[0].lower() # Lowercase command for case-insensitivity
            args = parts_cmd[1:]

            if is_channel and not is_command_enabled(target, cmd):
                logger.info(f"Command '{prefix}{cmd}' invoked in {target} but is disabled.")
                return None, target

            handler = COMMANDS.get(cmd)
            if handler:
                try:
                    import inspect
                    sig = inspect.signature(handler)
                    params = sig.parameters
                    positional = [p for p in params.values() if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)]
                    varargs = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params.values())
                    source_nick = source.split('!')[0]
                    if len(positional) >= 2:
                        response = handler(target, source_nick, *args)
                    elif len(positional) == 1:
                        response = handler(target, *args)
                    elif varargs:
                        response = handler(*args)
                    else:
                        logger.error(f"Unexpected handler signature {sig} for command {cmd}")
                        response = handler(target, *args)
                    return response, target
                except Exception as e:
                    logger.error(f"Error executing command {prefix}{cmd} by {source} in {target}: {e}", exc_info=True)
                    return f"Error executing command {prefix}{cmd}.", target
            else:
                pass # Silently ignore unknown prefixed commands

        import re
        if BOT_NICK and re.search(rf'\b{re.escape(BOT_NICK)}\b', content, re.IGNORECASE):
            prompt = re.sub(rf'\b{re.escape(BOT_NICK)}\b[ :!,?]*', '', content, flags=re.IGNORECASE).strip()

            if not prompt: # Only the nick was mentioned
                logger.info(f"Bot mentioned by {source} in {target} with empty prompt.")
                return f"Hello {source.split('!')[0]}! How can I help you?", target # Example response

            context_lines = []
            if is_channel:
                try:
                    context_lines = get_channel_log_context(target, limit=AI_CONTEXT_LINES)
                except Exception as ctx_exc:
                    logger.error(f"Error fetching channel context for {target}: {ctx_exc}", exc_info=True)
                    context_lines = []
            context_str = "\n".join(
                f"[{ts.strftime('%H:%M')}] <{nick}> {msg}" for ts, nick, msg in context_lines
            )
            if context_str:
                full_prompt = f"Context:\n{context_str}\n\nUser: {prompt}"
            else:
                full_prompt = prompt

            logger.info(f"AI prompt from {source} in {target}: '{full_prompt}'")
            try:
                resp = get_response_with_function_calling(full_prompt)
                return resp, target
            except ConnectionError as e:
                logger.error(f"AI connection error for prompt '{prompt}': {e}")
                return "Sorry, I'm having trouble connecting to my brain right now.", target
            except Exception as e:
                logger.error(f"AI error for prompt '{prompt}': {e}", exc_info=True)
                return "Sorry, I encountered an error while thinking about that.", target

    except Exception as e:
        logger.error(f"Error processing line: '{line}'. Error: {e}", exc_info=True)
        return "An unexpected error occurred while processing the message.", None # Generic error

    return None, None # No command or mention detected
