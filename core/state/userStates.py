from aiogram.fsm.state import StatesGroup, State



class UserState(StatesGroup):

    CITY = State()
    SERVICE = State()
    CONTACT = State()
    CONFIRM = State()