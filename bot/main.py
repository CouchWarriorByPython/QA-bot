import asyncio
from aiogram import Router, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.configs import bot
from bot.handlers.admin_handlers import register_admin_handlers
from bot.handlers.survey_handlers import register_survey_handlers
from bot.db.database import init_db
from bot.logger import ProjectLogger, info, error

logger = ProjectLogger().get_logger()

# Create main router
router = Router()


async def main() -> None:
    """Main function to start the bot."""
    try:
        # Initialize the SQLAlchemy database
        init_db()
        info("SQLAlchemy database initialized")

        # Create dispatcher with FSM storage
        dp = Dispatcher(storage=MemoryStorage())

        # Register all handlers
        register_admin_handlers(router)
        register_survey_handlers(router)

        # Include the main router
        dp.include_router(router)

        # Start polling
        info("Starting bot...")
        await dp.start_polling(bot)
    except Exception as e:
        error(f"Error starting bot: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())