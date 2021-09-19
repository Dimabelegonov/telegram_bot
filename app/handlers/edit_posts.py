from aiogram.dispatcher.filters.builtin import IDFilter
from data.db import db_session
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from data.db.models import Posts, Attachments
from app.__get_admins import get_admins


class EditPosts(StatesGroup):
    wait_for_choose_act = State()
    wait_for_choose_post_delete = State()
    wait_for_choose_post_view = State()
    wait_for_name = State()
    wait_for_text = State()
    wait_for_photo = State()
    wait_for_docs = State()
    wait_for_first = State()


async def start_edit(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*["Удалить пост", "Добавить пост", "Просмотреть пост"])

    db_sess = db_session.create_session()
    posts = db_sess.query(Posts).all()
    posts.sort(key=lambda x: x.post_id)
    answer_text = ""
    for i, post in enumerate(posts):
        if post.first_post:
            answer_text += f"{str(i + 1)}. {post.post_name}. (Пост первого сообщения)\n"
        else:
            answer_text += f"{str(i + 1)}. {post.post_name}.\n"

    if len(posts) == 0:
        await message.answer("Нет доступных постов", reply_markup=keyboard)
    else:
        await message.answer(answer_text, reply_markup=keyboard)

    await EditPosts.wait_for_choose_act.set()

    db_sess.close()


async def add_post(message: types.Message, state: FSMContext):
    await message.answer("Введите название поста (Оно показываться не будет, нужно для навигации)", reply_markup=types.ReplyKeyboardRemove())
    await EditPosts.wait_for_name.set()


async def choose_delete_post(message: types.Message, state: FSMContext):
    db_sess = db_session.create_session()
    posts = db_sess.query(Posts).all()
    posts.sort(key=lambda x: x.post_id)
    buttons = []
    answer_text = "Выберите пост для удаления\n"
    for i, post in enumerate(posts):
        buttons.append(f"Пост №{i + 1}")
        if post.first_post:
            answer_text += f"{str(i + 1)}. {post.post_name}. (Пост первого сообщения)\n"
        else:
            answer_text += f"{str(i + 1)}. {post.post_name}.\n"

    if len(posts) == 0:
        await message.answer("Нет доступных постов")
    else:
        await EditPosts.wait_for_choose_post_delete.set()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*buttons)
        await message.answer(answer_text, reply_markup=keyboard)

    db_sess.close()


async def delete_post(message: types.Message, state: FSMContext):
    if message.text.strip() == "":
        await message.answer("Выберите пост для удаления")
        return

    number = list(message.text.strip().split("№"))[-1]
    if number.isdigit():
        await state.finish()

        # Удаление поста
        db_sess = db_session.create_session()
        posts = db_sess.query(Posts).all()
        posts.sort(key=lambda x: x.post_id)
        if len(posts) == 1:
            await message.answer("Вы не можете удалить последний пост.\nДля перехода к началу используйте команду /admin", reply_markup=types.ReplyKeyboardRemove())
            db_sess.close()
            return
        else:
            post = posts[len(posts) - int(number)]
            post.first_post = True
            db_sess.delete(posts[int(number) - 1])
            db_sess.commit()

        await message.answer("Пост успешно удален\nДля перехода к началу используйте команду /admin", reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer("Выберите пост для удаления")

    db_sess.close()


async def choose_view_post(message: types.Message, state: FSMContext):
    db_sess = db_session.create_session()
    posts = db_sess.query(Posts).all()
    posts.sort(key=lambda x: x.post_id)
    buttons = []
    answer_text = "Выберите пост для просмотра\n"
    for i, post in enumerate(posts):
        buttons.append(f"Пост №{i + 1}")
        if post.first_post:
            answer_text += f"{str(i + 1)}. {post.post_name}. (Пост первого сообщения)\n"
        else:
            answer_text += f"{str(i + 1)}. {post.post_name}.\n"

    if len(posts) == 0:
        await message.answer("Нет доступных постов")
    else:
        await EditPosts.wait_for_choose_post_view.set()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*buttons)
        await message.answer(answer_text, reply_markup=keyboard)

    db_sess.close()


async def view_post(message: types.Message, state: FSMContext):
    if message.text.strip() == "":
        await message.answer("Выберите пост для просмотра")
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

        await message.answer(post.post_text)

        for att in atts:
            try:
                await message.answer_photo(att)
            except Exception:
                pass

            try:
                await message.answer_document(att)
            except Exception:
                pass

        await message.answer("Для перехода к началу используйте команду /admin", reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer("Выберите пост для просмотра")

    db_sess.close()


async def save_post_name(message: types.Message, state: FSMContext):
    if message.text == "" or message.text.strip() == "":
        await message.answer("Название не должно являться пустой строкой!")
        return
    await state.update_data(post_name=message.text)

    await message.answer("Введите текст поста:", reply_markup=types.ReplyKeyboardRemove())
    await EditPosts.wait_for_text.set()


async def save_post_text(message: types.Message, state: FSMContext):
    if message.text.strip() == "":
        await message.answer("Введите текст поста:", reply_markup=types.ReplyKeyboardRemove())
        return
    await state.update_data(post_text=message.text)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Не загружать фото")
    await message.answer("Загрузите фото для поста\n(Это обязательно должен быть файл фотографии)", reply_markup=keyboard)
    await EditPosts.wait_for_photo.set()


async def save_post_photo(message: types.Message, state: FSMContext):
    if message.text and message.text.strip().lower() == "Не загружать фото".lower() or message.text and message.text.strip().lower() == "Не добавлять фото".lower():
        await EditPosts.wait_for_docs.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Не загружать документ")
        await message.answer("Загрузите документ для поста\n(Это обязательно должен быть файл документа)", reply_markup=keyboard)
        return

    post_data = await state.get_data()

    if message.photo:
        if "images" not in post_data.keys():
            await state.update_data(images=[message.photo[-1].file_id])
            post_data["images"] = [message.photo[-1].file_id]
        else:
            post_data["images"].append(message.photo[-1].file_id)
            await state.update_data(images=post_data["images"])

    if "images" in post_data.keys():
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Не добавлять фото")
        await message.answer("Фото загруженно успешно\nМожете загрузить ещё фото", reply_markup=keyboard)
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Не загружать фото")
        await message.answer("Загрузите фото для поста", reply_markup=keyboard)


async def save_post_docs(message: types.Message, state: FSMContext):
    if message.text and message.text.strip().lower() == "Не загружать документ".lower() or message.text and message.text.strip().lower() == "Не добавлять документ".lower():
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*["Да", "Нет"])
        await message.answer("Сделать пост первым сообщением?", reply_markup=keyboard)
        await EditPosts.wait_for_first.set()
        return

    post_data = await state.get_data()

    if message.document:
        if "docs" not in post_data.keys():
            await state.update_data(docs=[message.document.file_id])
            post_data["docs"] = [message.document.file_id]
        else:
            post_data["docs"].append(message.document.file_id)
            await state.update_data(docs=post_data["docs"])

    if "docs" in post_data.keys():
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Не добавлять документ")
        await message.answer("Документ успешно загружен\nМожете загрузить ещё документы", reply_markup=keyboard)
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Не загружать документ")
        await message.answer("Загрузите документ для поста", reply_markup=keyboard)


async def save_post(message: types.Message, state: FSMContext):
    f_p = message.text.strip().lower() == "Да".lower()

    db_sess = db_session.create_session()
    data = await state.get_data()

    # Добавление поста
    if f_p and db_sess.query(Posts).filter(Posts.first_post == True).all():
        f_post = db_sess.query(Posts).filter(Posts.first_post == True).all()[0]
        db_sess.delete(f_post)
        db_sess.commit()
        new_post = Posts(
            f_post.post_name,
            f_post.post_text,
            False
        )
        db_sess.add(new_post)
        db_sess.commit()

    post = Posts(
        data["post_name"],
        data["post_text"],
        f_p
    )
    db_sess.add(post)
    db_sess.commit()

    # Добавление вложений
    try:
        for file_id in data["images"]:
            att = Attachments(file_id, post.post_id)
            db_sess.add(att)
            db_sess.commit()
    except Exception:
        pass

    try:
        for file_id in data["docs"]:
            att = Attachments(file_id, post.post_id)
            db_sess.add(att)
            db_sess.commit()
    except Exception:
        pass

    await state.finish()
    await message.answer("Пост успешно добавлен\nДля перехода к началу используйте команду /admin", reply_markup=types.ReplyKeyboardRemove())

    db_sess.close()


def register_handlers_edit_posts(dp: Dispatcher):
    dp.register_message_handler(start_edit, IDFilter(user_id=get_admins()), Text(equals="Редактировать сообщения"), state="*")
    dp.register_message_handler(add_post, IDFilter(user_id=get_admins()), Text(equals="Добавить пост"), state=EditPosts.wait_for_choose_act)
    dp.register_message_handler(choose_delete_post, IDFilter(user_id=get_admins()), Text(equals="Удалить пост"), state=EditPosts.wait_for_choose_act)
    dp.register_message_handler(delete_post, IDFilter(user_id=get_admins()), state=EditPosts.wait_for_choose_post_delete)
    dp.register_message_handler(choose_view_post, IDFilter(user_id=get_admins()), Text(equals="Просмотреть пост"), state=EditPosts.wait_for_choose_act)
    dp.register_message_handler(view_post, IDFilter(user_id=get_admins()), state=EditPosts.wait_for_choose_post_view)
    dp.register_message_handler(save_post_name , IDFilter(user_id=get_admins()), state=EditPosts.wait_for_name)
    dp.register_message_handler(save_post_text , IDFilter(user_id=get_admins()), state=EditPosts.wait_for_text)
    dp.register_message_handler(save_post_photo , IDFilter(user_id=get_admins()), content_types=["photo", "text"], state=EditPosts.wait_for_photo)
    dp.register_message_handler(save_post_docs , IDFilter(user_id=get_admins()), content_types=["document", "text"], state=EditPosts.wait_for_docs)
    dp.register_message_handler(save_post , IDFilter(user_id=get_admins()), state=EditPosts.wait_for_first)