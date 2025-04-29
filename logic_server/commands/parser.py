# --- START OF FILE parser.py ---

from typing import Optional, Tuple
from config import BOT_NICK
from shared.logger import setup_logger
from logic_server.db import get_prefix, is_command_enabled, get_channel_log_context
from logic_server.ai.ai_config import AI_CONTEXT_LINES
from .decorator import COMMANDS
# Import the correct function from gemini module
from logic_server.ai.gemini import get_response_with_function_calling

logger = setup_logger("parser") # Changed logger name for clarity

async def handle_line(line: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Process a raw IRC PRIVMSG line and return a tuple (response, target) if a command is detected
    or if the bot's nick is mentioned (triggering AI).
    """
    try:
        # More robust parsing for PRIVMSG lines
        parts = line.split(" ", 3) # :nick!user@host PRIVMSG #channel/#user :message
        if len(parts) < 4 or parts[1] != "PRIVMSG":
            return None, None # Not a valid PRIVMSG line we can handle here

        source = parts[0].lstrip(':') # Remove leading ':' and strip whitespace
        target = parts[2]     # Channel or user the message is sent to
        content = parts[3][1:].strip() # Remove leading ':' and strip whitespace

        # Determine if the message is in a channel or a PM
        is_channel = target.startswith("#") or target.startswith("&") # Add other channel prefixes if needed

        # Default prefix or fetch from DB
        # Ensure get_prefix can handle non-channel targets (PMs) gracefully
        prefix = get_prefix(target) if is_channel else "!" # Default '!' for PMs or if DB fails

        # --- Prefix-based commands ---
        if content.startswith(prefix):
            parts_cmd = content[len(prefix):].split()
            if not parts_cmd:
                return None, target # Just the prefix was typed
            cmd = parts_cmd[0].lower() # Lowercase command for case-insensitivity
            args = parts_cmd[1:]

            # Check if command is enabled (only relevant for channels)
            if is_channel and not is_command_enabled(target, cmd):
                # Optional: Don't announce disabled commands to reduce spam
                # return f"Command '{prefix}{cmd}' is disabled in {target}.", target
                logger.info(f"Command '{prefix}{cmd}' invoked in {target} but is disabled.")
                return None, target

            handler = COMMANDS.get(cmd)
            if handler:
                try:
                    import inspect
                    sig = inspect.signature(handler)
                    params = list(sig.parameters.keys())
                    # Only pass nick for echo/weather if handler expects exactly (channel, source, *args)
                    if cmd in ("weather", "echo", "ping", "uptime", "about", "status", "version", "say", "join", "part", "reload", "commands") and len(params) >= 2 and params[0] == "channel" and params[1] == "source":
                        source_nick = source.split('!')[0]
                        response = handler(target, source_nick, *args)
                    # For commands that expect (channel, *args) (e.g. admin, help, test), match signature len
                    elif len(params) == 1 + len(args):
                        response = handler(target, *args)
                    # For commands that expect (channel, source, *args), match signature len
                    elif len(params) == 2 + len(args):
                        response = handler(target, source, *args)
                    else:
                        # fallback: try (target, *args)
                        response = handler(target, *args)
                    return response, target
                except Exception as e:
                    logger.error(f"Error executing command {prefix}{cmd} by {source} in {target}: {e}", exc_info=True)
                    return f"Error executing command {prefix}{cmd}.", target
            else:
                # Optional: Reply if a prefixed message doesn't match a known command
                # return f"Unknown command: {prefix}{cmd}", target
                pass # Silently ignore unknown prefixed commands

        # --- AI invocation on mention ---
        # Check if the bot's nick is mentioned (case-insensitive)
        # Use word boundaries to avoid partial matches like "somebody_nick"
        import re
        # Ensure BOT_NICK is defined in config
        if BOT_NICK and re.search(rf'\b{re.escape(BOT_NICK)}\b', content, re.IGNORECASE):
            # Remove the bot's nick and surrounding whitespace/punctuation for a cleaner prompt
            # This regex tries to remove "BOT_NICK:", "BOT_NICK,", "BOT_NICK" etc.
            prompt = re.sub(rf'\b{re.escape(BOT_NICK)}\b[ :!,?]*', '', content, flags=re.IGNORECASE).strip()

            if not prompt: # Only the nick was mentioned
                logger.info(f"Bot mentioned by {source} in {target} with empty prompt.")
                return f"Hello {source.split('!')[0]}! How can I help you?", target # Example response

            # Fetch context from channel log
            context_lines = []
            if is_channel:
                try:
                    context_lines = get_channel_log_context(target, limit=AI_CONTEXT_LINES)
                except Exception as ctx_exc:
                    logger.error(f"Error fetching channel context for {target}: {ctx_exc}", exc_info=True)
                    context_lines = []
            # Format context for the AI prompt
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
        # Catch-all for unexpected errors during line processing
        logger.error(f"Error processing line: '{line}'. Error: {e}", exc_info=True)
        return "An unexpected error occurred while processing the message.", None # Generic error

    return None, None # No command or mention detected
# --- END OF FILE parser.py ---