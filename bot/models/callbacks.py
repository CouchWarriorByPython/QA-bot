from typing import Optional
from aiogram.filters.callback_data import CallbackData

class AnswerCallback(CallbackData, prefix="ans"):
    """Callback data for survey answers"""
    action: str  # "toggle", "select", "custom", "done"
    question_idx: int
    answer_idx: Optional[int] = None


class AdminCallback(CallbackData, prefix="admin"):
    """Callback data for admin functions"""
    action: str  # "all_results"