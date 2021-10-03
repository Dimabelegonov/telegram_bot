import asyncio
import logging
import aioschedule

from openpyxl import load_workbook
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from app.config_reader import load_config

from app.handlers.common import register_handlers_common
from app.handlers.edit_posts import register_handlers_edit_posts
from app.handlers.mailing import register_handlers_mailing

from data.db import db_session
from data.db.models import Users


async def save_subscribers():
    fn = r"data/files/subscribers.xlsx"
    wb = load_workbook(fn)
    ws = wb["Sheet1"]

    db_sess = db_session.create_session()
    subs = len(db_sess.query(Users).all())

    row = (datetime.now(), subs)
    ws.append(row)

    wb.save(fn)
    wb.close()
    db_sess.close()


async def subscribers_scheduler():
    aioschedule.every().day.at("14:43").do(save_subscribers)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Начать"),
    ]

    await bot.set_my_commands(commands)


async def main():
    # Настройка логировния в stdout
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    logger.info("Starting bot!")

    asyncio.create_task(subscribers_scheduler())

    # Объявление и инициализация объекта диспечера
    dp = Dispatcher(bot, storage=MemoryStorage())

    # Регистрация хэндлеров
    register_handlers_common(dp)
    register_handlers_edit_posts(dp)
    register_handlers_mailing(dp, bot)

    # Установка команд бота
    await set_commands(bot)

    # запуск бота
    await dp.skip_updates()
    await dp.start_polling()


if __name__ == "__main__":
    # Парсинг файла конфигурации
    # config = load_config("config/release_config.ini")
    config = load_config("config/bot.ini")

    # загрузка базы данных
    db_session.global_init(config.tg_bot.db)

    # добавление администраторов
    db_sess = db_session.create_session()
    for i in config.tg_bot.admin_id:
        admin = Users(i, is_ad=1)
        if len(db_sess.query(Users).filter(Users.telegram_id == admin.telegram_id).all()) == 0:
            db_sess.add(admin)
            db_sess.commit()

    db_sess.close()

    # объявление объекта бота
    bot = Bot(token=config.tg_bot.token)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
