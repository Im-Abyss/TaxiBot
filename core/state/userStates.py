from aiogram.fsm.state import StatesGroup, State

class UserState(StatesGroup):
    CITY = State()
    SERVICE = State()
    DELIVERY_PRODUCTS = State()
    TAXI_DESTINATION = State()
    CONTACT = State()
    CONFIRM = State()

