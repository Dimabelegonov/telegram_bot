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
        post = db_sess.query(Posts).filter(Posts.first_post == True).first()
        user_not_block = True
        try:
            if post.post_link != "":
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                button = types.InlineKeyboardButton(text=post.label_link, url=post.post_link)
                keyboard.add(button)
            await message.answer(post.post_text, reply_markup=keyboard)

        except Exception:
            user_not_block = False
            block_user = db_sess.query(Users).filter(Users.telegram_id == user).one()
            db_sess.delete(block_user)
            db_sess.commit()

        if user_not_block:
            try:
                atts = [x.att_telegram_id for x in post.attachments]
                for att in atts:
                    try:
                        await message.answer_photo(att)
                    except Exception:
                        pass

                    try:
                        await message.answer_document(att)
                    except Exception:
                        pass
            except Exception:
                pass

    db_sess.close()


# Команда толькло для админис тратора
async def admin_start(message: types.Message, state: FSMContext):
    # обнуляет текущее состояние бота
    await state.finish()

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton(text="Сделать рассылку", ),
        types.KeyboardButton(text="Редактировать сообщения"),
        types.KeyboardButton(text="Получить инструкцию"),
        types.KeyboardButton(text="Количество подписчиков")
    ]

    keyboard.add(*buttons)
    await message.answer("Привет, админ, выбери действие!\nДля перехода в начало используйте команду /admin", reply_markup=keyboard)


def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands="start", state="*")
    dp.register_message_handler(admin_start, IDFilter(user_id=get_admins()), commands="admin", state="*")
