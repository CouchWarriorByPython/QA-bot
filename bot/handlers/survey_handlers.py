from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
import os

from bot.configs import bot, IMAGES_FOLDER
from bot.models.state import SurveyStates
from bot.models.callbacks import AnswerCallback, AdminCallback
from bot.utils.helpers import (
    is_admin, questions, generate_keyboard, save_answers
)

from bot.logger import info, warning, error, debug


def register_survey_handlers(router: Router):
    """Register all survey-related handlers"""
    debug("Реєстрація обробників опитування")

    @router.message(CommandStart())
    async def start_command(message: Message, state: FSMContext) -> None:
        """Start the survey when user sends /start command."""
        user_id = message.from_user.id
        username = message.from_user.username

        # If admin, show admin panel instead of starting survey
        if is_admin(user_id):
            info(f"Адміністратор {user_id} (@{username}) розпочав роботу з ботом")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Показати результати опитування",
                                      callback_data=AdminCallback(action="all_results").pack())],
                [InlineKeyboardButton(text="Почати опитування",
                                      callback_data="start_survey")]
            ])
            await message.answer("Вітаю, адміністратор! Виберіть опцію:", reply_markup=keyboard)
            return

        # Otherwise, start the survey for regular users
        info(f"Користувач {user_id} (@{username}) розпочав роботу з ботом")
        await state.set_data({
            "current_question": 0,
            "answers": {}
        })

        await send_question(user_id, state)

    @router.callback_query(F.data == "start_survey")
    async def start_survey_callback(callback_query: CallbackQuery, state: FSMContext) -> None:
        """Start the survey from a callback button."""
        await callback_query.answer()
        user_id = callback_query.from_user.id
        username = callback_query.from_user.username

        info(f"Користувач {user_id} (@{username}) розпочав опитування")

        # Initialize user data
        await state.set_data({
            "current_question": 0,
            "answers": {}
        })

        await send_question(user_id, state)

    @router.callback_query(AnswerCallback.filter(F.action == "toggle"))
    async def process_toggle_answer(callback_query: CallbackQuery, callback_data: AnswerCallback,
                                    state: FSMContext) -> None:
        """Handle toggling a multiple-choice answer."""
        await callback_query.answer()
        user_id = callback_query.from_user.id

        # Get current data
        data = await state.get_data()
        question_index = data.get("current_question", 0)
        user_answers = data.get("answers", {})

        question_data = questions[question_index]
        q_text = question_data["question"]
        answer_idx = callback_data.answer_idx
        answer_text = question_data["answers"][answer_idx]

        # Initialize answer structure if not exists
        if q_text not in user_answers:
            user_answers[q_text] = {"selected": [], "custom": None}

        # Toggle selection
        selected = user_answers[q_text]["selected"]
        if answer_text in selected:
            selected.remove(answer_text)
            debug(f"Користувач {user_id} зняв вибір відповіді '{answer_text}' на питання {question_index + 1}")
        else:
            selected.append(answer_text)
            debug(f"Користувач {user_id} вибрав відповідь '{answer_text}' на питання {question_index + 1}")

        # Update state
        data["answers"] = user_answers
        await state.set_data(data)

        # Update message keyboard
        try:
            keyboard = await generate_keyboard(question_data, user_answers)
            await callback_query.message.edit_reply_markup(reply_markup=keyboard)
        except TelegramBadRequest as e:
            error(f"Не вдалося оновити клавіатуру для користувача {user_id}: {e}")

    @router.callback_query(AnswerCallback.filter(F.action == "select"))
    async def process_select_answer(callback_query: CallbackQuery, callback_data: AnswerCallback,
                                    state: FSMContext) -> None:
        """Handle selecting a single-choice answer."""
        await callback_query.answer()
        user_id = callback_query.from_user.id

        # Get current data
        data = await state.get_data()
        question_index = data.get("current_question", 0)
        user_answers = data.get("answers", {})

        question_data = questions[question_index]
        q_text = question_data["question"]
        answer_idx = callback_data.answer_idx
        answer_text = question_data["answers"][answer_idx]

        # Save answer
        user_answers[q_text] = {"selected": answer_text, "custom": None}
        data["answers"] = user_answers
        data["current_question"] += 1
        await state.set_data(data)

        info(f"Користувач {user_id} відповів '{answer_text}' на питання {question_index + 1}")

        # Go to next question
        await send_question(user_id, state)

    @router.callback_query(AnswerCallback.filter(F.action == "custom"))
    async def process_custom_input_request(callback_query: CallbackQuery, state: FSMContext) -> None:
        """Handle request for custom text input."""
        await callback_query.answer()
        user_id = callback_query.from_user.id

        debug(f"Користувач {user_id} вибрав власний варіант відповіді")
        await bot.send_message(user_id, "Напишіть ваш варіант відповіді:")
        await state.set_state(SurveyStates.custom_input)

    @router.callback_query(AnswerCallback.filter(F.action == "done"))
    async def process_done(callback_query: CallbackQuery, state: FSMContext) -> None:
        """Handle completion of multiple-choice question."""
        await callback_query.answer()
        user_id = callback_query.from_user.id

        # Move to next question
        data = await state.get_data()
        question_index = data.get("current_question", 0)
        data["current_question"] += 1
        await state.set_data(data)

        debug(f"Користувач {user_id} завершив відповідь на питання {question_index + 1}")

        await send_question(user_id, state)

    @router.message(SurveyStates.custom_input)
    async def process_text_response(message: Message, state: FSMContext) -> None:
        """Process text response from user."""
        user_id = message.from_user.id

        # Get current data
        data = await state.get_data()
        question_index = data.get("current_question", 0)
        user_answers = data.get("answers", {})

        question_data = questions[question_index]
        q_text = question_data["question"]

        # Save custom text answer
        if q_text not in user_answers:
            default_selected = [] if question_data["multiple_choice"] else None
            user_answers[q_text] = {"selected": default_selected, "custom": message.text}
        else:
            user_answers[q_text]["custom"] = message.text

        # Update state and move to next question
        data["answers"] = user_answers
        data["current_question"] += 1
        await state.set_data(data)

        info(
            f"Користувач {user_id} надав текстову відповідь на питання {question_index + 1}: '{message.text[:50]}...' " if len(
                message.text) > 50 else f"Користувач {user_id} надав текстову відповідь на питання {question_index + 1}: '{message.text}'")

        await send_question(user_id, state)

    @router.message()
    async def handle_unexpected(message: Message) -> None:
        """Handle unexpected messages."""
        user_id = message.from_user.id
        warning(f"Користувач {user_id} надіслав неочікуване повідомлення: '{message.text}'")
        await message.answer("Будь ласка, використовуйте кнопки опитування або команду /start для початку опитування.")

    debug("Обробники опитування успішно зареєстровані")


async def send_question(user_id: int, state: FSMContext) -> None:
    """Send the current question to the user."""
    # Get current user data
    data = await state.get_data()
    question_index = data.get("current_question", 0)
    user_answers = data.get("answers", {})

    # Check if survey is complete
    if question_index >= len(questions):
        info(f"Користувач {user_id} завершив опитування")
        final_message = "Після збору анкет ми сформуємо технічне завдання:\n\n• Які продукти замовляти\n• Які страви готувати\n• Скільки потрібно площі\n• Який формат і графік роботи магазину\n• Які ремонти та обладнання необхідні"
        await bot.send_message(user_id, final_message)
        await save_answers(user_id, user_answers)
        await state.clear()
        return

    # Get current question data
    question_data = questions[question_index]
    question_text = f"{question_data['question']}\n\n{question_data['hint']}"

    debug(f"Відправка питання {question_index + 1} користувачу {user_id}")

    # Send image for the question first
    image_number = question_index + 1  # Question indexes start from 0, image files from 1
    image_filename = f"{image_number}.PNG"
    image_path = os.path.join(IMAGES_FOLDER, image_filename)

    try:
        # Create appropriate keyboard if needed
        keyboard = None
        if question_data["answers"]:
            keyboard = await generate_keyboard(question_data, user_answers)
            await state.set_state(SurveyStates.answering)
        elif question_data["text_response"]:
            await state.set_state(SurveyStates.custom_input)

        # Send the image with caption and keyboard (if available)
        image = FSInputFile(image_path)
        await bot.send_photo(
            user_id,
            image,
            caption=question_text,
            reply_markup=keyboard
        )
        debug(f"Відправлено зображення {image_filename} для питання {question_index + 1}")

    except FileNotFoundError:
        error(f"Зображення {image_filename} не знайдено у {IMAGES_FOLDER}")
        # If image not found, just send the question as text
        if question_data["answers"]:
            keyboard = await generate_keyboard(question_data, user_answers)
            await bot.send_message(user_id, question_text, reply_markup=keyboard)
            await state.set_state(SurveyStates.answering)
        elif question_data["text_response"]:
            await bot.send_message(user_id, question_text)
            await state.set_state(SurveyStates.custom_input)

    except Exception as e:
        error(f"Помилка при відправці зображення для питання {question_index + 1}: {e}")
        # If any error, fall back to text-only question
        if question_data["answers"]:
            keyboard = await generate_keyboard(question_data, user_answers)
            await bot.send_message(user_id, question_text, reply_markup=keyboard)
            await state.set_state(SurveyStates.answering)

        # Handle text-only questions
        elif question_data["text_response"]:
            await bot.send_message(user_id, question_text)
            await state.set_state(SurveyStates.custom_input)

    # Skip questions without any response type
    if not question_data["answers"] and not question_data["text_response"]:
        warning(f"Питання {question_index + 1} не має варіантів відповіді, пропускаємо")
        data["current_question"] += 1
        await state.set_data(data)
        await send_question(user_id, state)