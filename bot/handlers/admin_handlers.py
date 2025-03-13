from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile

from bot.models.callbacks import AdminCallback
from bot.utils.helpers import is_admin
from bot.utils.visualization import generate_pie_chart


def register_admin_handlers(router: Router):
    """Register all admin-related handlers"""

    @router.callback_query(AdminCallback.filter(F.action == "all_results"))
    async def all_results_callback(callback_query: CallbackQuery, callback_data: AdminCallback) -> None:
        """Handle button click to show all results"""
        # Only admins can see results
        if not is_admin(callback_query.from_user.id):
            await callback_query.answer("У вас немає прав доступу до цієї функції.", show_alert=True)
            return

        await callback_query.answer()
        await callback_query.message.answer("Генерую діаграми для всіх питань...")

        # Send all charts in sequence
        for question_id in range(1, 14):  # Assuming question IDs are 1 through 13
            chart_buffer, color_data = generate_pie_chart(question_id)

            if not chart_buffer:
                await callback_query.message.answer(f"Не вдалося згенерувати діаграму для питання {question_id}.")
                continue

            # Send the chart without any caption
            await callback_query.message.answer_photo(
                BufferedInputFile(chart_buffer.read(), filename=f"question_{question_id}.png")
            )

            # Format the results data without repeating the question
            results_text = "📊 Результати:\n\n"
            for line in color_data.split('\n'):
                if line.strip():
                    results_text += line + "\n"

            await callback_query.message.answer(results_text)