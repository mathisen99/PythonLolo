import asyncio
import json
import websockets
import config
import signal
from shared.logger import setup_logger
logger = setup_logger("logic_server")
from logic_server.commands import handle_line

async def handler(websocket, path=None):
    logger.info("Logic server: client connected")
    try:
        async for message in websocket:
            logger.debug(f"Received raw WS message: {message}")
            data = json.loads(message)
            if data.get("type") == "heartbeat":
                await websocket.send(json.dumps({"type": "heartbeat"}))
                logger.debug("Replied to WS heartbeat")
                continue
            raw_line = data.get("line")
            if raw_line:
                resp, target = await handle_line(raw_line)
                if resp and target:
                    logger.info(f"Sending response: {resp} to {target}")
                    await websocket.send(json.dumps({"response": resp, "target": target}))
                elif resp:
                    logger.info(f"Sending response: {resp} (no target)")
                    await websocket.send(json.dumps({"response": resp}))
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected")

async def main():
    server = await websockets.serve(
        handler,
        config.LOGIC_SERVER_HOST,
        config.LOGIC_SERVER_PORT,
    )
    logger.info(f"Logic server running at ws://{config.LOGIC_SERVER_HOST}:{config.LOGIC_SERVER_PORT}")
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGINT, stop.set_result, None)
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
    await stop
    logger.info("Shutting down logic server")
    server.close()
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
