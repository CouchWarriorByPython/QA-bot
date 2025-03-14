import textwrap
import json
from typing import Dict, Any

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.configs import QUESTIONS_FILE, ADMIN_IDS
from bot.models.callbacks import AnswerCallback
from bot.db.database import save_all_user_answers
from bot.logger import info, error, debug

# Load questions from JSON file
with open(QUESTIONS_FILE, "r", encoding="utf-8") as json_file:
    questions = json.load(json_file)
    debug(f"Завантажено {len(questions)} питань з файлу {QUESTIONS_FILE}")

# Create map for quick access to question parameters
questions_map = {q["question_id"]: q for q in questions}


def is_admin(user_id):
    """Check if user is admin"""
    is_admin_user = user_id in ADMIN_IDS
    debug(f"Перевірка прав адміністратора для користувача {user_id}: {is_admin_user}")
    return is_admin_user


def wrap_text(text, max_width=20):
    """Wrap text to fit within maximum width"""
    if len(text) <= max_width:
        return text

    # Use textwrap module for better text wrapping
    wrapped_text = "\n".join(textwrap.wrap(text, width=max_width))
    return wrapped_text


async def generate_keyboard(question_data: Dict[str, Any], user_answers: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Generate an inline keyboard based on question data and current user answers."""
    keyboard = []
    q_text = question_data["question"]

    # Get current selections for this question
    current_answer = user_answers.get(q_text, {})
    selected = current_answer.get("selected", []) if question_data["multiple_choice"] else current_answer.get(
        "selected")

    # Create buttons for each answer
    for idx, answer in enumerate(question_data["answers"]):
        if not answer.strip():
            continue

        if question_data["multiple_choice"]:
            is_selected = "✔️ " if answer in selected else ""
            callback_data = AnswerCallback(
                action="toggle",
                question_idx=question_data.get("question_id", 0),
                answer_idx=idx
            ).pack()
        else:
            is_selected = ""
            callback_data = AnswerCallback(
                action="select",
                question_idx=question_data.get("question_id", 0),
                answer_idx=idx
            ).pack()

        keyboard.append([InlineKeyboardButton(
            text=f"{is_selected}{answer}",
            callback_data=callback_data
        )])

    # Add custom input option if allowed
    if question_data["text_response"]:
        keyboard.append([InlineKeyboardButton(
            text="Інше (ввести свій варіант)",
            callback_data=AnswerCallback(
                action="custom",
                question_idx=question_data.get("question_id", 0)
            ).pack()
        )])

    # Add done button for multiple choice questions
    if question_data["multiple_choice"]:
        keyboard.append([InlineKeyboardButton(
            text="✅ Готово",
            callback_data=AnswerCallback(
                action="done",
                question_idx=question_data.get("question_id", 0)
            ).pack()
        )])

    debug(f"Згенеровано клавіатуру для питання {question_data.get('question_id', 0)} з {len(keyboard)} кнопками")
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def save_answers(user_id: int, user_answers: Dict[str, Any]) -> None:
    """Save user answers to SQLAlchemy database."""
    try:
        info(f"Спроба збереження відповідей користувача {user_id}")

        # Use the SQLAlchemy function to save all answers
        result = save_all_user_answers(user_id, user_answers, questions_map)

        if result:
            info(f"Відповіді користувача {user_id} успішно збережено в базі даних")
        else:
            error(f"Не вдалося зберегти відповіді користувача {user_id} в базі даних")
    except Exception as e:
        error(f"Виникла помилка при збереженні відповідей користувача {user_id}: {e}")