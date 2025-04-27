import asyncio
import json
import config
import logic_server.db as db
from shared.logger import setup_logger
from datetime import datetime

logger = setup_logger("irc_bot.handlers")

class IRCHandlers:
    def __init__(self, client):
        self.client = client

    def on_welcome(self, connection, event):
        logger.info("Connected to IRC, joining channels")
        # join primary channel
        connection.join(config.IRC_CHANNEL)
        logger.info(f"IRC >> JOIN {config.IRC_CHANNEL}")
        # join additional auto channels
        for chan in config.IRC_AUTOCHANNELS:
            connection.join(chan)
            logger.info(f"IRC >> JOIN {chan}")

    def on_pubmsg(self, connection, event):
        hostmask = event.source
        # IGNORE: Check if user is ignored
        if db.get_user_level(hostmask) == "Ignored":
            return
        raw = event.arguments[0]
        # local admin user commands handled here
        prefix = db.get_prefix(event.target)
        if any(raw.startswith(prefix + f"admin user {sub}") for sub in ("add","remove","set")):
            self.client.handlers.handle_admin(connection, event)
            return
        # log public message
        db.log_message(event.source, event.source.split('!')[0], event.target, raw)
        message = raw
        # if logic server down and user mentions bot, notify downtime
        if config.BOT_NICK.lower() in message.lower() and self.client.ws_down_since:
            downtime = int((datetime.now() - self.client.ws_down_since).total_seconds())
            msg = f"Command server is down for {downtime}s"
            connection.privmsg(config.IRC_CHANNEL, msg)
            logger.info(f"IRC >> PRIVMSG {config.IRC_CHANNEL} :{msg}")
            return
        # forward message to logic server for command processing
        raw_line = f"{event.source} PRIVMSG {event.target} :{message}"
        asyncio.create_task(self.client.send_ws(raw_line))

    def on_privmsg(self, connection, event):
        message = event.arguments[0]
        hostmask = event.source
        # IGNORE: Check if user is ignored
        if db.get_user_level(hostmask) == "Ignored":
            return
        # local admin user commands via private message
        prefix_pm = db.get_prefix(event.target)
        if any(message.startswith(prefix_pm + f"admin user {sub}") for sub in ("add","remove","set")):
            self.client.handlers.handle_admin(connection, event)
            return
        nick = event.source.split('!')[0]
        hostmask = event.source
        # owner verification via private PM
        if self.client.owner_setup_pending and message.startswith("!verify "):
            provided = message.split(" ", 1)[1].strip()
            if provided == self.client.verify_secret:
                db.add_user(hostmask, nick, "Owner")
                connection.privmsg(nick, "You are now the owner.")
                self.client.owner_setup_pending = False
                self.client.verify_secret = None
            else:
                connection.privmsg(nick, "Invalid passphrase.")
            return
        # log private message
        db.log_message(event.source, nick, nick, message)
        # forward private message to logic server
        raw = f"{event.source} PRIVMSG {nick} :{message}"
        asyncio.create_task(self.client.send_ws(raw))

    def handle_admin(self, connection, event):
        parts = event.arguments[0].split()
        channel = event.target
        caller = event.source
        lvl = db.get_user_level(caller)
        if lvl not in ("Owner","Admin"):
            connection.privmsg(channel, "Permission denied")
            return
        if len(parts) < 4 or parts[1] != "user":
            connection.privmsg(channel, "Usage: !admin user add|remove NICK [LEVEL]")
            return
        cmd, target = parts[2], parts[3]
        if cmd not in ("add","remove","set"):
            connection.privmsg(channel, f"Unknown subcommand {cmd}")
            return
        if cmd in ("add","set"):
            if len(parts) != 5:
                connection.privmsg(channel, "Usage: !admin user add NICK LEVEL")
                return
            newlvl = parts[4].capitalize()
            if newlvl not in ("Owner","Admin","Normal","Ignored"):
                connection.privmsg(channel, f"Invalid level {newlvl}")
                return
            self.client.pending_admin[target] = (cmd, newlvl, channel)
        else:
            self.client.pending_admin[target] = (cmd, None, channel)
        connection.whois([target])
        connection.privmsg(channel, f"Looking up hostmask for {target}...")

    def on_whoisuser(self, connection, event):
        nick, user, host = event.arguments[0], event.arguments[1], event.arguments[2]
        hostmask = f"{nick}!{user}@{host}"
        info = self.client.pending_admin.pop(nick, None)
        if not info:
            return
        cmd, lvl, channel = info
        if cmd in ("add","set"):
            db.add_user(hostmask, nick, lvl)
            connection.privmsg(channel, f"User {nick} added as {lvl}")
        else:
            db.remove_user(hostmask)
            connection.privmsg(channel, f"User {nick} removed")

    def on_endofwhois(self, connection, event):
        nick = event.arguments[0]
        info = self.client.pending_admin.pop(nick, None)
        if info:
            _, _, channel = info
            connection.privmsg(channel, f"WHOIS failed for {nick}")

    def on_join(self, connection, event):
        channel = event.target
        nick = event.source.split('!')[0]
        hostmask = event.source
        # IGNORE: Check if user is ignored
        if db.get_user_level(hostmask) == "Ignored":
            return
        db.log_message(hostmask, nick, channel, f"{nick} joined {channel}")
        raw = f"{event.source} JOIN {channel}"
        asyncio.create_task(self.client.send_ws(raw))

    def on_part(self, connection, event):
        channel = event.target
        nick = event.source.split('!')[0]
        hostmask = event.source
        # IGNORE: Check if user is ignored
        if db.get_user_level(hostmask) == "Ignored":
            return
        db.log_message(hostmask, nick, channel, f"{nick} left {channel}")
        raw = f"{event.source} PART {channel}"
        asyncio.create_task(self.client.send_ws(raw))

    def on_nick(self, connection, event):
        old_nick = event.source.split('!')[0]
        new_nick = event.target
        hostmask = event.source
        # IGNORE: Check if user is ignored
        if db.get_user_level(hostmask) == "Ignored":
            return
        db.log_message(hostmask, old_nick, new_nick, f"{old_nick} is now {new_nick}")
        raw = f"{event.source} NICK :{new_nick}"
        asyncio.create_task(self.client.send_ws(raw))

async def handle_irc(reader, ws, writer):
    while True:
        raw = await reader.readline()
        if not raw:
            break
        message = raw.decode('utf-8', errors='ignore').rstrip('\r\n')
        logger.debug(f"IRC << {message}")
        if message.startswith('PING'):
            pong = message.replace('PING', 'PONG')
            writer.write(f"{pong}\r\n".encode())
            await writer.drain()
            logger.debug(f"IRC >> {pong}")
        else:
            if ' 001 ' in message:
                join_cmd = f"JOIN {config.IRC_CHANNEL}"
                writer.write(f"{join_cmd}\r\n".encode())
                await writer.drain()
                logger.info(f"IRC >> {join_cmd}")
            if 'PRIVMSG' in message:
                await ws.send(json.dumps({'line': message}))
                logger.debug("WS >> sent IRC line")

async def handle_ws(ws, writer):
    async for msg in ws:
        logger.debug(f"WS << {msg}")
        try:
            data = json.loads(msg)
            response = data.get('response')
            if response:
                privmsg = f"PRIVMSG {config.IRC_CHANNEL} :{response}"
                writer.write(f"{privmsg}\r\n".encode())
                await writer.drain()
                logger.info(f"IRC >> {privmsg}")
        except json.JSONDecodeError:
            logger.warning("WS >> invalid JSON")
