import asyncio
from aiogram.dispatcher.filters.builtin import IDFilter
from data.db import db_session
from aiogram import Dispatcher, types, Bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from data.db.models import Posts, Attachments, Users
from app.__get_admins import get_admins


bot = None


class Mail(StatesGroup):
    wait_for_choose_post = State()


async def start_mailing(message: types.Message, state: FSMContext):
    db_sess = db_session.create_session()
    posts = db_sess.query(Posts).all()
    posts.sort(key=lambda x: x.post_id)
    buttons = []
    answer_text = "Выберите пост для рассылки\n"
    for i, post in enumerate(posts):
        buttons.append(f"Пост №{i + 1}")
        if post.first_post:
            answer_text += f"{str(i + 1)}. {post.post_name}. (Пост первого сообщения)\n"
        else:
            answer_text += f"{str(i + 1)}. {post.post_name}.\n"

    if len(posts) == 0:
        await message.answer("Нет доступных постов")
    else:
        await Mail.wait_for_choose_post.set()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*buttons)
        await message.answer(answer_text, reply_markup=keyboard)

    db_sess.close()


async def do_mailing(message: types.Message, state: FSMContext):
    if message.text.strip() == "":
        await message.answer("Выберите пост для рассылки")
        return

    number = list(message.text.strip().split("№"))[-1]
    if number.isdigit():
        await state.finish()

        # Выбор поста для просмотра
        db_sess = db_session.create_session()
        posts = db_sess.query(Posts).all()
        posts.sort(key=lambda x: x.post_id)
        post = posts[int(number) - 1]

        atts = [x.att_telegram_id for x in post.attachments]

        # выбор всех пользователей для отправки
        users = db_sess.query(Users).filter(Users.is_admin == False).all()
        users = [x.telegram_id for x in users]

        for user in users:
            await asyncio.sleep(0.05)
            user_not_block = True
            try:
                await bot.send_message(user, post.post_text)
            except Exception:
                user_not_block = False
                block_user = db_sess.query(Users).filter(Users.telegram_id == user).one()
                db_sess.delete(block_user)
                db_sess.commit()

            if user_not_block:
                for att in atts:
                    try:
                        await bot.send_photo(user, att)
                    except Exception:
                        pass

                    try:
                        await bot.send_document(user, att)
                    except Exception:
                        pass

        await message.answer("Рассылка успешно выполнена\nДля перехода к началу используйте команду /admin", reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer("Выберите пост для рассылки")

    db_sess.close()


def register_handlers_mailing(dp: Dispatcher, bt: Bot):
    global bot
    bot = bt
    dp.register_message_handler(start_mailing, IDFilter(user_id=get_admins()), Text(equals="Сделать рассылку"), state="*")
    dp.register_message_handler(do_mailing, IDFilter(user_id=get_admins()), state=Mail.wait_for_choose_post)
