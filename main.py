import asyncio
import logging
import os
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import config
from database import db
from handlers import admin, user
from seed import seed_if_empty

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def start_healthcheck_server():
    """
    Render's free Web Service plan requires binding to a port, or it kills the
    process after a ~15 minute port-scan timeout. This bot doesn't need to serve
    HTTP traffic, so this is just a dummy endpoint to keep Render happy.
    (Not needed if you're on a plan that supports Background Workers instead.)
    """
    port = int(os.getenv("PORT", "8080"))
    app = web.Application()
    app.router.add_get("/", lambda request: web.Response(text="Bot is running"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Healthcheck server listening on port {port}")


async def main():
    await db.init()
    await seed_if_empty()
    await start_healthcheck_server()

    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Admin router first so /commands are handled before the catch-all text handler
    dp.include_router(admin.router)
    dp.include_router(user.router)

    logger.info("Starting FAQ bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
