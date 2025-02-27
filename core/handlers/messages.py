from aiogram.filters import CommandObject 
from aiogram import Bot, F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from core.keyboards.keys import service_keyboard, start_keyboard, phone_request_keyboard, location_keyboard
from core.state.userStates import UserState
from settings import CHANNEL_ID, ADMIN_ID
from sqlalchemy.orm import Session
from core.utils.database import User, engine
from datetime import datetime, timedelta



router = Router()

hello_msg = 'Такси / Доставка. Нажмите кнопку "начать"'
BOLD = "<b>"
BOLD_END = "</b>"

async def is_admin(user_id):
    """Проверяет, является ли пользователь администратором."""
    return user_id in ADMIN_ID


@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    with Session(bind=engine) as db:
        user = db.query(User).filter(User.user_id == message.from_user.id).first()
        if not user:
            db.add(User(user_id=message.from_user.id, username=message.from_user.username))
            db.commit()
        else:
            if user.blocked:
                await message.answer("Извините, вы заблокированы и не можете использовать этого бота.")
                return 
            try:
                if user.last_order_time:
                    time_since_last_order = datetime.now() - user.last_order_time
                    if time_since_last_order < timedelta(minutes=1):  # 1 минута
                        remaining_time = 60 - time_since_last_order.seconds
                        await message.answer(
                            f"Вы недавно подали заявку. Подождите ещё {remaining_time} секунд, чтобы создать новый заказ."
                        )
                        return
            except Exception as e:
                print(e)
    await message.answer(hello_msg, reply_markup=await start_keyboard())



@router.message(F.text == 'Отзывы')
async def reviews(message: Message, state: FSMContext):
    await message.answer(text='Ознакомиться с отзывами можно в группе: https://t.me/btax1')



@router.message(F.text == 'Начать')
async def start_order(message: Message, state: FSMContext):
    with Session(bind=engine) as db:
        user = db.query(User).filter(User.user_id == message.from_user.id).first()
        if user.blocked:
            await message.answer("Извините, вы заблокированы и не можете использовать этого бота.")
            return 
        try:
            if user.last_order_time:
                time_since_last_order = datetime.now() - user.last_order_time
                if time_since_last_order < timedelta(minutes=1):  # 1 минута
                    remaining_time = 60 - time_since_last_order.seconds
                    await message.answer(
                        f"Вы недавно подали заявку. Подождите ещё {remaining_time} секунд, чтобы создать новый заказ."
                    )
                    return
        except Exception as e:
            print(e)

        await message.answer('Нажмите, пожалуйста, кнопку "Местоположение"', reply_markup=await location_keyboard())
        await state.set_state(UserState.CITY)



@router.message(UserState.CITY, F.location)
async def get_city(message: Message, state: FSMContext):
    location = message.location
    latitude = location.latitude
    longitude = location.longitude

    await state.update_data(location=(latitude, longitude))
    await message.answer("Выберите услугу:", reply_markup=await service_keyboard())
    await state.set_state(UserState.SERVICE)



@router.message(UserState.SERVICE)
async def choose_service(message: Message, state: FSMContext):

    choice = message.text.lower()

    if choice == "такси":
        await message.answer("Укажите ваши контактные данные (например, телефон):")
        await state.update_data(taxi = message.text)
        await state.set_state(UserState.CONTACT)

    elif choice == "доставка":
        await message.answer("Укажите ваши контактные данные (например, телефон):")
        await state.update_data(delivery = message.text)
        await state.set_state(UserState.CONTACT)

    else:
        await message.answer("Пожалуйста, выберите одну из доступных услуг: Такси или Доставка.")



@router.message(F.contact)
async def handle_contact(message: Message, state: FSMContext):

    phone_number = message.contact.phone_number

    with Session(bind=engine) as db:
        user = db.query(User).filter(User.user_id == message.from_user.id).first()
        if user:
            user.phone = phone_number
            db.commit()

    await message.answer("Спасибо! Ваш номер телефона сохранен.")

    user_data = await state.get_data()
    
    if "taxi" in user_data:
        await finalize_taxi_order(message, state)
    elif "delivery" in user_data:
        await finalize_delivery_order(message, state)



@router.message(UserState.CONTACT)
async def get_contact(message: Message, state: FSMContext):

    phone_number = message.text

    with Session(bind=engine) as db:
        user = db.query(User).filter(User.user_id == message.from_user.id).first()
        if user:
            user.phone = phone_number
            db.commit()

    await message.answer("Спасибо! Ваш номер телефона сохранен.")

    user_data = await state.get_data()

    if "taxi" in user_data:
        await finalize_taxi_order(message, state)
    elif "delivery" in user_data:
        await finalize_delivery_order(message, state)



async def finalize_taxi_order(message: Message, state: FSMContext):

    user_data = await state.get_data()

    with Session(bind=engine) as db:

        user = db.query(User).filter(User.user_id == message.from_user.id).first()

        if user.phone:
            contact_info = f"<a href='tg://resolve?phone={user.phone}'>{message.from_user.full_name}</a>"
        else:
            contact_info = f"<a href='https://t.me/{message.from_user.username}'>{message.from_user.full_name}</a>"
        summary = f"""
{BOLD}Ваш заказ:{BOLD_END}
{BOLD}Геопозиция:{BOLD_END} {user_data['location']}
{BOLD}Услуга:{BOLD_END} Такси
{BOLD}Контактные данные:{BOLD_END} {contact_info}"""
        
        await message.answer(f"Спасибо за ваш заказ! Он отправлен на обработку.\n\n{summary}", parse_mode='HTML',
                             reply_markup= await start_keyboard())
        await send_to_channel(summary, message)
        user.last_order_time = datetime.now()
        db.commit()
        await state.clear()



async def finalize_delivery_order(message: Message, state: FSMContext):

    user_data = await state.get_data()

    with Session(bind=engine) as db:

        user = db.query(User).filter(User.user_id == message.from_user.id).first()

        if user.phone:
            contact_info = f"<a href='tg://resolve?phone={user.phone}'>{message.from_user.full_name}</a>"
        else:
            contact_info = f"<a href='https://t.me/{message.from_user.username}'>{message.from_user.full_name}</a>"

        summary = f"""
{BOLD}Ваш заказ:{BOLD_END}
{BOLD}Геопозиция:{BOLD_END} {user_data['location']}
{BOLD}Услуга:{BOLD_END} Такси
{BOLD}Контактные данные:{BOLD_END} {contact_info}"""
        
        await message.answer(f"Спасибо за ваш заказ! Он отправлен на обработку.\n\n{summary}", parse_mode='HTML',
                             reply_markup= await start_keyboard())
        
        await send_to_channel(summary, message)

        user.last_order_time = datetime.now()
        db.commit()

        await state.clear()



async def send_to_channel(summary: str, message: Message):

    await message.bot.send_message(
        CHANNEL_ID,
        f"Новый заказ:\n\n{summary}",
        parse_mode="HTML",
    )





@router.message(Command("ban"))
async def ban_user(message: Message, command: CommandObject):
    if not await  is_admin(message.from_user.username):
        await message.answer("Эта команда доступна только администратору.")
        return

    if not command.args:
        await message.answer("Пожалуйста, укажите username или номер телефона для блокировки.")
        return

    identifier = command.args.strip()  
    with Session(bind=engine) as db:
        user = None
        if identifier.startswith("+") or identifier.isdigit():  
            user = db.query(User).filter(User.phone == identifier).first()
        else:  
            user = db.query(User).filter(User.username == identifier).first()

        if not user:
            await message.answer(f"Пользователь с идентификатором '{identifier}' не найден.")
            return

        if user.blocked:
            await message.answer(f"Пользователь с идентификатором '{identifier}' уже заблокирован.")
            return

        user.blocked = True
        db.commit()
        await message.answer(f"Пользователь с идентификатором '{identifier}' успешно заблокирован.")



@router.message(Command("unban"))
async def unban_user(message: Message, command: CommandObject):
    if not await is_admin(message.from_user.username):
        await message.answer("Эта команда доступна только администратору.")
        return

    if not command.args:
        await message.answer("Пожалуйста, укажите username или номер телефона для разблокировки.")
        return

    identifier = command.args.strip()  
    with Session(bind=engine) as db:
        user = None
        if identifier.startswith("+") or identifier.isdigit():  
            user = db.query(User).filter(User.phone == identifier).first()
        else:  
            user = db.query(User).filter(User.username == identifier).first()

        if not user:
            await message.answer(f"Пользователь с идентификатором '{identifier}' не найден.")
            return

        if not user.blocked:
            await message.answer(f"Пользователь с идентификатором '{identifier}' уже разблокирован.")
            return

        user.blocked = False
        db.commit()
        await message.answer(f"Пользователь с идентификатором '{identifier}' успешно разблокирован.")