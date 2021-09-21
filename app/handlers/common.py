import asyncio
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import IDFilter

from data.db import db_session
from data.db.models import Users, Posts
from app.__get_admins import get_admins


# Начало взаимодействия с ползователем
async def cmd_start(message: types.Message, state: FSMContext):
    await asyncio.sleep(0.05)
    # обнуляет текущее состояние бота
    await state.finish()

    # занесение в базу данных нового подписчика
    user = Users(message.from_user.id)
    db_sess = db_session.create_session()
    if len(db_sess.query(Users).filter(Users.telegram_id == user.telegram_id).all()) == 0:
        db_sess.add(user)
        db_sess.commit()

    if str(user.telegram_id) in get_admins():
        await message.answer("Вы являетесь администратором бота\nДля перехода в админку введите /admin", reply_markup=types.ReplyKeyboardRemove())
    else:
        # отправка первого сообщения пользователю
        db_sess = db_session.create_session()
        post = db_sess.query(Posts).filter(Posts.first_post == True).first()

        atts = [x.att_telegram_id for x in post.attachments]

        await message.answer(post.post_text, reply_markup=types.ReplyKeyboardRemove())

        for att in atts:
            try:
                await message.answer_photo(att)
            except Exception:
                pass

            try:
                await message.answer_document(att)
            except Exception:
                pass

    db_sess.close()


# Команда толькло для админис тратора
async def admin_start(message: types.Message, state: FSMContext):
    # обнуляет текущее состояние бота
    await state.finish()

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        types.KeyboardButton(text="Сделать рассылку", ),
        types.KeyboardButton(text="Редактировать сообщения"),
        types.KeyboardButton(text="Получить инструкцию")
    ]

    keyboard.add(*buttons)
    await message.answer("Привет, админ, выбери действие!\nДля перехода в начало используйте команду /admin", reply_markup=keyboard)


def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands="start", state="*")
    dp.register_message_handler(admin_start, IDFilter(user_id=get_admins()), commands="admin", state="*")
