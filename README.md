# Lolo

A modular Python IRC bot with dynamic plugin support and a focus on extensibility.

## Features
- Decorator-based command registration
- Channel-scoped settings & custom prefixes
- Graceful shutdown & database migrations (Peewee)
- Dynamic plugin loading, unloading, reloading, and listing via `!admin plugin` commands
- Download and install plugins from remote URLs
- Example plugins: echo, time, weather
- Admin commands for user and plugin management

## Requirements
- Python 3.9+
- Install dependencies: `pip install -r requirements.txt`

## Configuration
- Copy and update `config.json` with your IRC server, bot nick, channel, DB path, and other settings.
- (Optional) Set environment variables in `.env` for secrets or deployment.

## Running the Bot
Lolo uses a two-process architecture:
1. **Logic Server** (handles commands, plugins, logic):
   ```bash
   python -m logic_server.server
   ```
2. **IRC Bot** (connects to IRC, relays messages):
   ```bash
   python -m irc_bot
   ```

## Usage
- `!help` — List available commands
- `!test` — Test command functionality
- `!echo <text>` — Echo back text
- `!time` — Show current server time
- `!weather <location>` — Fetch weather via wttr.in
- `!prefix set <new>` — Set command prefix per channel
- `!disable <command>` / `!enable <command>` — Disable/enable commands per channel
- `!admin user list` — List users & permission levels
- `!admin plugin list|load|unload|reload <plugin>` — Manage plugins
- `!admin plugin get <url>` — Download and load a plugin from a remote URL

## Extending Lolo
- Build your own plugins! See [PLUGIN_GUIDE.md](PLUGIN_GUIDE.md) for details and examples.
- Plugins are auto-discovered from `logic_server/plugins/` and can be managed at runtime.

## Contributing
Contributions welcome! Please open pull requests, issues, or suggestions.

## License
MIT
# PythonLolo
