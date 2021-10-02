import asyncio
from aiogram.dispatcher.filters.builtin import IDFilter
from aiogram.types import reply_keyboard
from data.db import db_session
from aiogram import Dispatcher, types, Bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from data.db.models import Posts, Attachments, Users
from app.__get_admins import get_admins

from datetime import datetime


bot = None


class Mail(StatesGroup):
    wait_for_choose_post = State()
    wait_for_choose_date_for_send_post = State()


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


async def choose_post(message: types.Message, state: FSMContext):
    if message.text.strip() == "":
        await message.answer("Выберите пост для рассылки")
        return

    number = list(message.text.strip().split("№"))[-1]
    if number.isdigit():
        await Mail.wait_for_choose_date_for_send_post.set()

        # Получаем пост для рассылки из базы данных
        db_sess = db_session.create_session()
        posts = db_sess.query(Posts).all()
        posts.sort(key=lambda x: x.post_id)
        post = posts[int(number) - 1]

        await state.update_data(post=post)

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Отправить сейчас")
        await message.answer("Вы можете выбрать дату и время отправки сообщения пользователям\nили отправить данное сообщение прямо сейчас.\nФормат для ввода даты и времени: дд.мм.гггг чч:мм", reply_markup=keyboard)
    else:
        await message.answer("Выберите пост для рассылки")

    db_sess.close()


async def do_mailing(message: types.Message, state: FSMContext):
    if message.text.strip() == "":
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Отправить сейчас")
        await message.answer("Вы можете выбрать дату и время отправки сообщения пользователям\nили отправить данное сообщение прямо сейчас.\nФормат для ввода даты и времени: дд.мм.гггг чч:мм", reply_markup=keyboard)
        return

    if message.text.strip().lower() == "Отправить сейчас".lower():
        post = await state.get_data()
        await send_post(post["post"])
        await message.answer("Рассылка успешно выполнена\nДля перехода к началу используйте команду /admin", reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        return

    try:
        date = message.text.strip().split()
        d, m, y = map(int, date[0].split("."))
        minutes, hours = map(int, date[1].split(":"))
        date = datetime(y, m, d, minutes, hours)

        inter = (date - datetime.now()).total_seconds()
        post = await state.get_data()

        if inter > 0:
            await message.answer("Рассылка успешно зарегистрирована\nДля перехода к началу используйте команду /admin", reply_markup=types.ReplyKeyboardRemove())
            await state.finish()

            await asyncio.sleep(inter)
            await send_post(post["post"])
            return

        else:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add("Отправить сейчас")
            await message.answer("Неправльный ввод даты или времени")
            await message.answer("Вы можете выбрать дату и время отправки сообщения пользователям\nили отправить данное сообщение прямо сейчас.\nФормат для ввода даты и времени: дд.мм.гггг чч:мм", reply_markup=keyboard)
            return

    except Exception:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Отправить сейчас")
        await message.answer("Неправльный ввод даты или времени")
        await message.answer("Вы можете выбрать дату и время отправки сообщения пользователям\nили отправить данное сообщение прямо сейчас.\nФормат для ввода даты и времени: дд.мм.гггг мм:чч", reply_markup=keyboard)
        return


async def send_post(post: Posts):
    db_sess = db_session.create_session()

    # Уведомление админов об отправке сообщения
    admins = db_sess.query(Users).filter(Users.is_admin == True).all()
    admins = [x.telegram_id for x in admins]

    for admin in admins:
        await asyncio.sleep(0.05)

        try:
            text = "Пост " + post.post_name + " успешно отправлен подписчикам"
            await bot.send_message(admin, text)
        except Exception:
            pass

    # выбор всех пользователей для отправки
    users = db_sess.query(Users).all()
    users = [x.telegram_id for x in users]

    for user in users:
        await asyncio.sleep(0.05)
        user_not_block = True

        try:
            if post.post_link != "":
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                button = types.InlineKeyboardButton(text=post.label_link, url=post.post_link)
                keyboard.add(button)
            await bot.send_message(user, post.post_text, reply_markup=keyboard)

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
                        await bot.send_photo(user, att)
                    except Exception:
                        pass

                    try:
                        await bot.send_document(user, att)
                    except Exception:
                        pass
            except Exception:
                pass


def register_handlers_mailing(dp: Dispatcher, bt: Bot):
    global bot
    bot = bt
    dp.register_message_handler(start_mailing, IDFilter(user_id=get_admins()), Text(equals="Сделать рассылку"), state="*")
    dp.register_message_handler(choose_post, IDFilter(user_id=get_admins()), state=Mail.wait_for_choose_post)
    dp.register_message_handler(do_mailing, IDFilter(user_id=get_admins()), state=Mail.wait_for_choose_date_for_send_post)
