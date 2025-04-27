from shared.logger import setup_logger
from .decorator import command, COMMANDS
import pkgutil
import importlib
import sys
import logic_server.plugins as plugins
from logic_server.db import User
import config

logger = setup_logger("commands")

@command("admin")
def admin_command(channel: str, *args) -> str:
    """Admin operations: user & plugin management"""
    # list users
    if len(args) >= 2 and args[0] == "user" and args[1] == "list":
        users = User.select()
        if not users:
            return "No users found."
        return "Users: " + ", ".join(f"{u.nick} ({u.level})" for u in users)
    # help for user subcommand when no action specified
    if len(args) >= 1 and args[0] == "user":
        return "Usage: !admin user list"
    # channel autojoin management
    if len(args) >= 1 and args[0] == "channels":
        sub_args = args[1:]
        if not sub_args or sub_args[0] not in ("add", "remove", "list"):
            return "Usage: !admin channels add <#channel> | !admin channels remove <#channel> | !admin channels list"
        channels = config.IRC_AUTOCHANNELS
        changed = False
        if sub_args[0] == "add" and len(sub_args) == 2 and sub_args[1].startswith("#"):
            if sub_args[1] not in channels:
                channels.append(sub_args[1])
                changed = True
                msg = f"Added {sub_args[1]} to auto-join list."
            else:
                msg = f"{sub_args[1]} is already in auto-join list."
        elif sub_args[0] == "remove" and len(sub_args) == 2 and sub_args[1].startswith("#"):
            if sub_args[1] in channels:
                channels.remove(sub_args[1])
                changed = True
                msg = f"Removed {sub_args[1]} from auto-join list."
            else:
                msg = f"{sub_args[1]} is not in auto-join list."
        else:
            if channels:
                return "Auto-join channels: " + ", ".join(channels)
            else:
                return "No auto-join channels set."
        if changed:
            # Persist changes
            config._conf["IRC_AUTOCHANNELS"] = channels
            config.save_config()
        return msg
    # plugin management
    if len(args) >= 1 and args[0] == "plugin":
        action_args = args[1:]
        if not action_args:
            return "Usage: !admin plugin list|load|unload|reload|get <url>"
        cmd = action_args[0]
        if cmd == "list":
            available = [name for _, name, _ in pkgutil.iter_modules(plugins.__path__)]
            loaded = [m.split('.')[-1] for m in sys.modules if m.startswith("logic_server.plugins.")]
            return f"Plugins available: {', '.join(available)}; loaded: {', '.join(loaded)}"
        if cmd in ("load", "unload", "reload") and len(action_args) == 2:
            action, plugin_name = cmd, action_args[1]
            module_name = f"logic_server.plugins.{plugin_name}"
            def _unload():
                removed = [c for c, f in COMMANDS.items() if f.__module__ == module_name]
                for c in removed:
                    del COMMANDS[c]
                sys.modules.pop(module_name, None)
                return removed
            if action == "load":
                if module_name in sys.modules:
                    return f"Plugin {plugin_name} already loaded."
                try:
                    importlib.import_module(module_name)
                    return f"Plugin {plugin_name} loaded."
                except Exception as e:
                    logger.error(f"Error loading plugin {plugin_name}: {e}")
                    return f"Error loading plugin {plugin_name}: {e}"
            if action == "unload":
                if module_name not in sys.modules:
                    return f"Plugin {plugin_name} not loaded."
                removed = _unload()
                return f"Plugin {plugin_name} unloaded. Removed cmds: {', '.join(removed) or 'none'}"
            if action == "reload":
                removed = []
                if module_name in sys.modules:
                    removed = _unload()
                try:
                    mod = importlib.import_module(module_name)
                    importlib.reload(mod)
                    return f"Plugin {plugin_name} reloaded. Removed cmds: {', '.join(removed) or 'none'}"
                except Exception as e:
                    logger.error(f"Error reloading plugin {plugin_name}: {e}")
                    return f"Error reloading plugin {plugin_name}: {e}"
        # NEW: download and load plugin from URL
        if cmd == "get" and len(action_args) == 2:
            _, plugin_url = action_args
            from .plugin_downloader import download_and_load_plugin
            return download_and_load_plugin(plugin_url)
        return "Usage: !admin plugin list|load|unload|reload|get <url>"
    return "Usage: !admin user list | plugin list|load|unload|reload|get <url> | channels add <#channel> | channels remove <#channel> | channels list"
