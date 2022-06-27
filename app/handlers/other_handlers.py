from aiogram import Dispatcher, types, Bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters.builtin import IDFilter
from aiogram.dispatcher.filters import Text

from data.db.models import Posts, Attachments, Users, Deferred
from data.db import db_session
from app.__get_admins import get_admins


class Optional(StatesGroup):
    wait_for_choose_delete_dfr = State()


async def get_manual(message: types.Message, state: FSMContext):
    manual = open("data/files/manual.png", "rb")
    await message.answer_photo(manual, reply_markup=types.ReplyKeyboardRemove())
    await message.answer("Для перехода к началу используйте команду /admin")


async def get_subscribers(message: types.Message, state: FSMContext):
    subs = open("data/files/subscribers.xlsx", "rb")
    await message.answer_document(subs, reply_markup=types.ReplyKeyboardRemove())
    db_sess = db_session.create_session()
    subs = len(db_sess.query(Users).all())
    await message.answer(f"Сейчас на бота подписано {subs} человек")
    await message.answer("Для перехода к началу используйте команду /admin")
    db_sess.close()


async def show_dfr(message: types.Message, state: FSMContext):
    db_sess = db_session.create_session()
    dfrs = db_sess.query(Deferred).all()
    dfrs.sort(key=lambda x: x.dfr_id)
    buttons = []
    answer_text = "Выберите отложенное сообщение, которое необходимо удалить\n"
    for i, dfr in enumerate(dfrs):
        post = db_sess.query(Posts).filter(Posts.post_id == dfr.dfr_post_id).first()
        buttons.append(f"Сообщение №{i + 1}")
        answer_text += f"{str(i + 1)}) Название поста: {post.post_name}; Время отправки поста: {dfr.dfr_date}\n"

    if len(dfrs) == 0:
        await message.answer("Нет отложенных сообщений")
    else:
        await Optional.wait_for_choose_delete_dfr.set()
        keyword = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyword.add(*buttons)
        await message.answer(answer_text, reply_markup=keyword)


async def delete_dfr(message: types.Message, state: FSMContext):
    if message.text.lower() == "":
        await message.answer("Выберите отложенное сообщение, отправку которого нужно отменить")
        return
    number = list(message.text.strip("№"))[-1]
    if number.isdigit():
        await state.finish()

        # Удаление отложенного сообщения
        db_sess = db_session.create_session()
        dfrs = db_sess.query(Deferred).all()
        dfrs.sort(key=lambda x: x.dfr_id)
        db_sess.delete(dfrs[int(number) - 1])
        db_sess.commit()
        db_sess.close()

        await message.answer("Отправка отложенного сообщения успешно отменена\n"
                             "Для перехода к началу используйте команду /admin",
                             reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer("Выберите отложенное сообщение, которое необходимо удалить")


def register_handlers_optional(dp: Dispatcher, bt: Bot):
    global bot
    bot = bt
    dp.register_message_handler(get_manual, IDFilter(user_id=get_admins()), Text(equals="Получить инструкцию"),
                                state="*")
    dp.register_message_handler(get_subscribers, IDFilter(user_id=get_admins()), Text(equals="Количество подписчиков"),
                                state="*")
    dp.register_message_handler(show_dfr, IDFilter(user_id=get_admins()),
                                Text(equals="Посмотреть список отложенных сообщений"))
    dp.register_message_handler(delete_dfr, IDFilter(user_id=get_admins()),
                                state=Optional.wait_for_choose_delete_dfr)
