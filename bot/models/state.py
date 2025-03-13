from aiogram.fsm.state import State, StatesGroup

class SurveyStates(StatesGroup):
    """States for the survey flow"""
    answering = State()
    custom_input = State()