from core.handlers.messages import router as cmd_router
from aiogram import Bot, Dispatcher, Router
from settings import BOT_TOKEN
import asyncio
# import logging

# logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)

router = Router()

async def start():
    """Запуск приложения"""
    bot = Bot(token = BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(cmd_router)

    try:
        await dp.start_polling(bot,skip_updates=True)
    finally:
        await bot.session.close()

if  __name__ == '__main__':
    try:
        asyncio.run(start())
    except KeyboardInterrupt:
        print("Бот остановлен")