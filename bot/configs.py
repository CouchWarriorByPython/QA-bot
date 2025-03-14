import os

from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from typing import Final


CURRENT_FOLDER: Final[str] = os.getcwd()
ENV_FILE_PATH = os.path.join(CURRENT_FOLDER, '.env')
load_dotenv(ENV_FILE_PATH)


QUESTIONS_FILE = os.path.join(CURRENT_FOLDER, "questions.json")


BOT_TOKEN: Final[str] = os.getenv('BOT_TOKEN')

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

ADMIN_IDS = [446915311, 299793265]