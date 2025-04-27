import os
import asyncio
import json
import config
import websockets
import irc.client
from shared.logger import setup_logger
from datetime import datetime
import logic_server.db as db
import signal
from .handlers import IRCHandlers
from irc_bot.irc_message_utils import sanitize_for_irc, split_irc_messages

logger = setup_logger("irc_bot.client")

class IRCBot:
    def __init__(self, verify_secret=None):
        # owner verification
        self.verify_secret = verify_secret
        self.owner_setup_pending = bool(verify_secret)
        # pending admin WHOIS callbacks
        self.pending_admin = {}
        # initialize database
        db.init_db()
        self.reactor = irc.client.Reactor()
        self.ws = None
        self.ws_down_since = None
        self.connection = self.reactor.server().connect(
            config.IRC_SERVER, config.IRC_PORT, config.BOT_NICK
        )
        # delegate event handling
        self.handlers = IRCHandlers(self)
        self.connection.add_global_handler("welcome", self.handlers.on_welcome)
        self.connection.add_global_handler("pubmsg", self.handlers.on_pubmsg)
        self.connection.add_global_handler("privmsg", self.handlers.on_privmsg)
        self.connection.add_global_handler("whoisuser", self.handlers.on_whoisuser)
        self.connection.add_global_handler("endofwhois", self.handlers.on_endofwhois)
        self.connection.add_global_handler("disconnect", self.on_disconnect)
        # event hooks: join, part, nick change via handlers
        self.connection.add_global_handler("join", self.handlers.on_join)
        self.connection.add_global_handler("part", self.handlers.on_part)
        self.connection.add_global_handler("nick", self.handlers.on_nick)
        self._irc_reconnect_task = None  # Track running reconnect task

    def on_disconnect(self, connection, event):
        logger.warning("Disconnected from IRC, scheduling reconnect")
        # Prevent multiple reconnect loops
        if self._irc_reconnect_task and not self._irc_reconnect_task.done():
            logger.warning("Reconnect already in progress, skipping duplicate trigger.")
            return
        self._irc_reconnect_task = asyncio.create_task(self._irc_reconnect())

    async def _irc_reconnect(self):
        backoff = 1
        while True:
            try:
                conn = self.reactor.server().connect(
                    config.IRC_SERVER, config.IRC_PORT, config.BOT_NICK
                )
                self.connection = conn
                conn.add_global_handler("welcome", self.handlers.on_welcome)
                conn.add_global_handler("pubmsg", self.handlers.on_pubmsg)
                conn.add_global_handler("privmsg", self.handlers.on_privmsg)
                conn.add_global_handler("whoisuser", self.handlers.on_whoisuser)
                conn.add_global_handler("endofwhois", self.handlers.on_endofwhois)
                conn.add_global_handler("disconnect", self.on_disconnect)
                conn.add_global_handler("join", self.handlers.on_join)
                conn.add_global_handler("part", self.handlers.on_part)
                conn.add_global_handler("nick", self.handlers.on_nick)
                logger.info("IRC reconnected successfully")
                self._irc_reconnect_task = None
                backoff = 1  # Reset backoff after successful reconnect
                return
            except Exception as e:
                logger.warning(f"IRC reconnect failed: {e}, retrying in {backoff}s")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

    async def send_ws(self, raw_line: str):
        try:
            await self.ws.send(json.dumps({"line": raw_line}))
            logger.debug(f"WS >> sent IRC line: {raw_line}")
        except Exception as e:
            logger.error(f"Error sending to WS: {e}")
            if not self.ws_down_since:
                self.ws_down_since = datetime.now()
            # clear stale WS connection so on_pubmsg handles downtime
            self.ws = None

    async def process_irc(self):
        while True:
            try:
                self.reactor.process_once(timeout=0)
            except Exception as e:
                logger.error(f"process_irc exception: {e}")
                # If not already reconnecting, trigger reconnect
                if not (self._irc_reconnect_task and not self._irc_reconnect_task.done()):
                    self._irc_reconnect_task = asyncio.create_task(self._irc_reconnect())
                await asyncio.sleep(1)
                continue
            await asyncio.sleep(0.1)

    async def process_ws(self):
        async for msg in self.ws:
            logger.debug(f"WS << {msg}")
            try:
                data = json.loads(msg)
                response = data.get("response")
                if response:
                    # Handle __PRIVMSG__ special marker for !say command
                    if isinstance(response, str):
                        if response.startswith("__PRIVMSG__::"):
                            parts = response.split("::", 2)
                            if len(parts) == 3:
                                target, message = parts[1], parts[2]
                                logger.info(f"Sending IRC PM: {message} to {target}")
                                lines = split_irc_messages(sanitize_for_irc(message))
                                for line in lines:
                                    if line.strip():
                                        self.connection.privmsg(target, line)
                                        logger.info(f"IRC >> PRIVMSG {target} :{line}")
                                return
                        elif response.startswith("__JOIN__::"):
                            target = response.split("::", 1)[1]
                            logger.info(f"Joining channel: {target}")
                            self.connection.join(target)
                            logger.info(f"IRC >> JOIN {target}")
                            return
                        elif response.startswith("__PART__::"):
                            target = response.split("::", 1)[1]
                            logger.info(f"Parting channel: {target}")
                            self.connection.part(target)
                            logger.info(f"IRC >> PART {target}")
                            return
                    logger.info(f"Sending IRC response: {response}")
                    # Sanitize and split all outgoing messages
                    if isinstance(response, list):
                        lines = []
                        for resp in response:
                            lines.extend(split_irc_messages(sanitize_for_irc(str(resp))))
                    else:
                        lines = split_irc_messages(sanitize_for_irc(str(response)))
                    for line in lines:
                        if line.strip():
                            self.connection.privmsg(config.IRC_CHANNEL, line)
                            logger.info(f"IRC >> PRIVMSG {config.IRC_CHANNEL} :{line}")
                            # Log bot's own message to the DB
                            db.log_message(
                                f"{config.BOT_NICK}!bot@localhost",
                                config.BOT_NICK,
                                config.IRC_CHANNEL,
                                line
                            )
            except json.JSONDecodeError:
                logger.warning("WS >> invalid JSON")

    async def start(self):
        # start IRC processing loop
        asyncio.create_task(self.process_irc())
        # manage WebSocket connection with auto-reconnect
        uri = f"ws://{config.LOGIC_SERVER_HOST}:{config.LOGIC_SERVER_PORT}"
        backoff = 1
        while True:
            try:
                self.ws = await websockets.connect(uri, ping_interval=20, ping_timeout=20)
                self.ws_down_since = None
                logger.info(f"WS connected to {uri}")
                backoff = 1  # Reset backoff after successful WS connect
                await self.process_ws()
            except Exception as e:
                now = datetime.now()
                if not self.ws_down_since:
                    self.ws_down_since = now
                # clear stale connection
                self.ws = None
                logger.warning(f"WS disconnected: {e}; reconnecting in {backoff}s")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

    def on_welcome(self, connection, event):
        return self.handlers.on_welcome(connection, event)

    def on_pubmsg(self, connection, event):
        return self.handlers.on_pubmsg(connection, event)

    def on_privmsg(self, connection, event):
        return self.handlers.on_privmsg(connection, event)

    def handle_admin(self, connection, event):
        return self.handlers.handle_admin(connection, event)

    def on_whoisuser(self, connection, event):
        return self.handlers.on_whoisuser(connection, event)

    def on_endofwhois(self, connection, event):
        return self.handlers.on_endofwhois(connection, event)

    def on_join(self, connection, event):
        return self.handlers.on_join(connection, event)

    def on_part(self, connection, event):
        return self.handlers.on_part(connection, event)

    def on_nick(self, connection, event):
        return self.handlers.on_nick(connection, event)

async def main():
    # prompt for owner secret if needed
    # check for existing Owner via Peewee
    owner = db.User.get_or_none(db.User.level == "Owner")
    if not owner:
        secret = input("No owner found. Enter secret passphrase for first owner: ").strip()
    else:
        secret = None
    bot = IRCBot(verify_secret=secret)
    # start bot and listen for shutdown signals
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    # safe signal handler to avoid InvalidStateError
    def _stop_signal():
        if not stop.done():
            stop.set_result(None)
    for s in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(s, _stop_signal)
    task = asyncio.create_task(bot.start())
    await stop
    logger.info("Shutting down IRC bot")
    # cancel bot.start task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.info("Bot start task cancelled")
    # close WS and IRC connections
    if bot.ws:
        await bot.ws.close()
    bot.connection.disconnect("Shutting down")
    # cleanup signal handlers
    for s in (signal.SIGINT, signal.SIGTERM):
        loop.remove_signal_handler(s)

if __name__ == '__main__':
    asyncio.run(main())
