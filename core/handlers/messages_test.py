from aiogram import Bot, F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from core.keyboards.keys import service_keyboard, start_keyboard
from core.state.userStates import UserState
from settings import CHANNEL_ID

router = Router()

hello_msg = 'Такси / Доставка.  Нажмите кнопку "начать"'
BOLD = "<b>"
BOLD_END = "</b>"

@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await message.answer(hello_msg, reply_markup=await start_keyboard())


@router.message(F.text == 'Отзывы')
async def start(message: Message, state: FSMContext):
    await message.answer(text='Ознакомиться с отзывами можно в группе: https://t.me/btax1')


@router.message(F.text == 'Начать')
async def start(message: Message, state: FSMContext):
    await message.answer('Напишите пожалуйста название вашего города/населенного пункта.', reply_markup=await start_keyboard())
    await state.set_state(UserState.CITY)


@router.message(UserState.CITY)
async def get_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("Выберите услугу:", reply_markup=await service_keyboard())
    await state.set_state(UserState.SERVICE)


@router.message(UserState.SERVICE)
async def choose_service(message: Message, state: FSMContext):
    choice = message.text.lower()
    if choice == "такси":
        await message.answer("Введите адрес подачи такси:")
        await state.set_state(UserState.TAXI_PICKUP)
    elif choice == "доставка":
        await message.answer("Введите адрес доставки:")
        await state.set_state(UserState.DELIVERY_ADDRESS)
    else:
        await message.answer("Пожалуйста, выберите одну из доступных услуг: Такси или Доставка.")


@router.message(UserState.TAXI_PICKUP)
async def taxi_pickup(message: Message, state: FSMContext):
    await state.update_data(taxi_pickup=message.text)
    await message.answer("Введите адрес назначения:")
    await state.set_state(UserState.TAXI_DESTINATION)


@router.message(UserState.TAXI_DESTINATION)
async def taxi_destination(message: Message, state: FSMContext):
    await state.update_data(taxi_destination=message.text)
    if not message.from_user.username:
        await message.answer("Укажите ваши контактные данные (например, телефон):")
        await state.set_state(UserState.CONTACT)
        return
    await finalize_taxi_order(message, state)


@router.message(UserState.DELIVERY_ADDRESS)
async def delivery_address(message: Message, state: FSMContext):
    await state.update_data(delivery_address=message.text)
    await message.answer("Введите список продуктов для доставки:")
    await state.set_state(UserState.DELIVERY_PRODUCTS)


@router.message(UserState.DELIVERY_PRODUCTS)
async def delivery_products(message: Message, state: FSMContext):
    await state.update_data(delivery_products=message.text)
    if not message.from_user.username:
        await message.answer("Укажите ваши контактные данные (например, телефон):")
        await state.set_state(UserState.CONTACT)
        return
    await finalize_delivery_order(message, state)


@router.message(UserState.CONTACT)
async def get_contact(message: Message, state: FSMContext):
    await state.update_data(contact_info=message.text)
    user_data = await state.get_data()
    if "taxi_pickup" in user_data:  # Это заказ такси
        await finalize_taxi_order(message, state)
    elif "delivery_address" in user_data:  # Это доставка
        await finalize_delivery_order(message, state)


async def finalize_taxi_order(message: Message, state: FSMContext):
    user_data = await state.get_data()
    contact_info = user_data.get("contact_info", f"<a href='https://t.me/{message.from_user.username}'>{message.from_user.full_name}</a>")
    summary = f"""
{BOLD}Ваш заказ:{BOLD_END}
{BOLD}Город:{BOLD_END} {user_data['city']}
{BOLD}Услуга:{BOLD_END} Такси
{BOLD}Адрес подачи:{BOLD_END} {user_data['taxi_pickup']}
{BOLD}Адрес назначения:{BOLD_END} {user_data['taxi_destination']}
{BOLD}Контактные данные:{BOLD_END} {contact_info}
"""
    await message.answer(f"Спасибо за ваш заказ! Он отправлен на обработку.\n\n{summary}",
                         parse_mode='HTML')
    await send_to_channel(summary, message)
    await message.answer("Для создания нового заказа, нажмите /start", reply_markup=await start_keyboard())
    await state.clear()


async def finalize_delivery_order(message: Message, state: FSMContext):
    user_data = await state.get_data()
    contact_info = user_data.get("contact_info", f"<a href='https://t.me/{message.from_user.username}'>{message.from_user.full_name}</a>")
    summary = f"""
{BOLD}Ваш заказ:{BOLD_END}
{BOLD}Город:{BOLD_END} {user_data['city']}
{BOLD}Услуга:{BOLD_END} Доставка
{BOLD}Адрес доставки:{BOLD_END} {user_data['delivery_address']}
{BOLD}Список продуктов:{BOLD_END} {user_data['delivery_products']}
{BOLD}Контактные данные:{BOLD_END} {contact_info}
"""
    await message.answer(f"Спасибо за ваш заказ! Он отправлен на обработку.\n\n{summary}",
                         parse_mode='HTML')
    await send_to_channel(summary, message)
    await message.answer("Для создания нового заказа, нажмите /start", reply_markup=await start_keyboard())
    await state.clear()


async def send_to_channel(summary: str, message: Message):
    channel_id = CHANNEL_ID
    bot = message.bot
    user_data = await message.bot.get_chat(message.from_user.id)
    user_link = f"<a href='https://t.me/{message.from_user.username}'>{message.from_user.full_name}</a>"
    contact_info = user_data.get("contact_info", user_link)
    await bot.send_message(
        channel_id,
        f"Новый заказ:\n\n{summary}\n\nКонтакт: {contact_info}",
        parse_mode="HTML",
    )