from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram import Bot, Dispatcher
import gspread
import os

CURRENT_DIR = os.getcwd()
QUESTIONS_FILE = os.path.join(CURRENT_DIR, "questions.json")

API_TOKEN = "7450502864:AAF87mbGefW9N43_dI_DlO-6ej4dyfrf9RU"

# 🔹 Підключення до Google Sheets
CREDS_FILE = os.path.join(CURRENT_DIR, "service_account.json")
SPREADSHEET_ID = "1mxJrE2X_vXCWFXNnrD4j7b9HDnalsOGqgLaw5OIXVh0"

# Підключення до Google Sheets
gc = gspread.service_account(filename=CREDS_FILE)
sheet = gc.open_by_key(SPREADSHEET_ID)
answers_sheet = sheet.worksheet("Answers")

# Ініціалізація бота
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

ADMIN_IDS = [446915311, 299793265]