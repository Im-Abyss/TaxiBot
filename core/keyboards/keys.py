from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


async def start_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Начать")
    builder.button(text="Отзывы")
    builder.adjust(2) 
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


async def location_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Местоположение", request_location=True))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


async def service_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Такси")
    builder.button(text="Доставка")
    builder.adjust(2) 
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


async def phone_request_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Отправить номер телефона", request_contact=True)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

async def confirm_phone_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Верно", callback_data="confirm_phone"),
            InlineKeyboardButton(text="Нет, изменить", callback_data="change_phone")
        ]
    ])
    return keyboard