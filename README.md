# Lolo

A modular Python IRC bot with dynamic plugin support, AI integration, and a focus on extensibility.

## Features
- Decorator-based command registration
- Download and install plugins from remote URLs
- Example plugins: echo, time, weather
- Admin commands for user and plugin management
- **AI Function Calling**: Gemini/OpenAI-powered, with live web search, stock/crypto price, and system uptime tools
- **Context-aware AI chat**: Mention the bot to get answers using channel history (including bot's own messages)
- **Say, Join, Part, and more**: See full command reference below

## Requirements
- Python 3.9+
- Copy and update `config.json` with your IRC server, bot nick, channel, DB path, and other settings.
- (Optional) Set environment variables in `.env` for secrets or deployment.

### Environment Variables
- `OPENAI_API_KEY` — for web search tool (OpenAI)
- `GOOGLE_API_KEY` — for Gemini AI (if used)
- `FINNHUB_API_KEY` — for stock/crypto price tool

## Running the Bot
Lolo uses a two-process architecture:
1. **Logic Server** (handles commands, plugins, logic):
   python -m irc_bot
   ```

## Command Reference

| Command | Arguments | Description |
|---------|-----------|-------------|
| `!help`, `!commands` |  | List available commands |
| `!test` |  | Test command functionality |
| `!echo <text>` | `<text>` | Echo back text |
| `!time` |  | Show current server time |
| `!weather <location>` | `<location>` | Fetch weather via wttr.in |
| `!prefix set <new>` | `<new>` | Set command prefix per channel |
| `!disable <command>` / `!enable <command>` | `<command>` | Disable/enable commands per channel |
| `!admin user list` |  | List users & permission levels |
| `!admin plugin list\|load\|unload\|reload <plugin>` | `<plugin>` | Manage plugins |
| `!admin plugin get <url>` | `<url>` | Download and load a plugin from a remote URL |
| `!say <target> <message>` | `<target> <message>` | Make the bot say something in a channel or PM |
| `!join <#channel>` | `<#channel>` | Make the bot join a specified channel |
| `!part <#channel>` | `<#channel>` | Make the bot leave a specified channel |
| `!ping` |  | Ping the bot (returns pong) |
| `!version` |  | Show bot version |
| `!about` |  | Show bot info |
| `!reload` |  | Reload all command modules (see plugin reload) |
| Mention bot nick | `<question>` | Ask the bot anything; uses channel context and AI tools |

**Note:** Some commands require appropriate permissions (admin/owner).

## AI Features & Natural Language Tools

Lolo supports advanced AI-powered features via Gemini/OpenAI. These are **not direct IRC commands**—instead, you access them by mentioning the bot in a channel and asking a question in natural language. The AI will use channel context and can automatically call tools to answer your question.

### Supported AI Tools (via natural language)
- **Web Search:** Ask the bot to look up information online (requires `OPENAI_API_KEY`).
    - Example: `PythonLolo, search the web for the latest news on Bitcoin.`
- **Stock/Crypto Price Lookup:** Ask for stock or crypto prices.
    - Example: `PythonLolo, what's the price of NVDA?` or `PythonLolo, how much is bitcoin worth?`
- **System Uptime:** Ask for the server's uptime.
    - Example: `PythonLolo, how long have you been running?`
- **General Q&A:** Ask any question and the bot will use up to 50 lines of channel context (including its own messages) to respond intelligently.

**Note:** These features are only available when you mention the bot in your message. There are no direct commands like `!web_search` or `!get_stock_price`.

## Extending Lolo
- Build your own plugins! See [PLUGIN_GUIDE.md](PLUGIN_GUIDE.md) for details and examples.