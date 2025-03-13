import asyncio
import logging
import sys
from aiogram import Router, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.configs import bot
from bot.handlers.admin_handlers import register_admin_handlers
from bot.handlers.survey_handlers import register_survey_handlers

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# Create main router
router = Router()


async def main() -> None:
    """Main function to start the bot."""
    # Create dispatcher with FSM storage
    dp = Dispatcher(storage=MemoryStorage())

    # Register all handlers
    register_admin_handlers(router)
    register_survey_handlers(router)

    # Include the main router
    dp.include_router(router)

    # Start polling
    logger.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())