from aiogram.fsm.state import StatesGroup, State


class UserState(StatesGroup):
    language = State()
    fullname = State()
    phone_number = State()
