import asyncio
import sys
import threading
from loguru import logger
import config
from bot.client import DiscordBot
from database.connection import init_database

bot = DiscordBot()

def start_web_server():
    import uvicorn
    from web.app import app
    logger.info(f"Starting web dashboard on port {config.WEB_PORT}")
    uvicorn.run(app, host=config.WEB_HOST, port=config.WEB_PORT, log_level="warning")

async def start_bot():
    try:
        await bot.start(config.BOT_TOKEN)
    finally:
        await bot.close()

async def main():
    logger.info("Starting Discord Bot")
    await init_database()
    logger.info("Database initialized")

    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()

    try:
        await start_bot()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as exc:
        logger.error(f"Fatal error: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
