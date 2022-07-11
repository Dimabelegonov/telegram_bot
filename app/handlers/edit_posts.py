from aiogram.dispatcher.filters.builtin import IDFilter
from data.db import db_session
from aiogram import Dispatcher, types, Bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from data.db.models import Posts, Attachments, Users
from app.__get_admins import get_admins


class EditPosts(StatesGroup):
    wait_for_choose_act = State()
    wait_for_choose_post_delete = State()
    wait_for_choose_post_view_or_edit = State()
    wait_for_start_edit_post = State()
    wait_for_name = State()
    wait_for_edit_name = State()
    wait_for_text = State()
    wait_for_edit_text = State()
    wait_for_photo = State()
    wait_for_edit_photo = State()
    wait_for_docs = State()
    wait_for_edit_docs = State()
    wait_for_link = State()
    wait_for_edit_link = State()
    wait_for_label_link = State()
    wait_for_edit_label_link = State()
    wait_for_edit_first = State()
    wait_for_first = State()


async def start_edit(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*["Удалить пост", "Добавить пост", "Просмотреть или редактировать пост"])

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
    await message.answer("Введите название поста (Оно показываться не будет, нужно для навигации)",
                         reply_markup=types.ReplyKeyboardRemove())
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
    db_sess = db_session.create_session()
    if message.text.strip() == "":
        await message.answer("Выберите пост для удаления")
        return

    number = list(message.text.strip().split("№"))[-1]
    if number.isdigit():
        await state.finish()

        # Удаление поста
        posts = db_sess.query(Posts).all()
        posts.sort(key=lambda x: x.post_id)
        if len(posts) == 1:
            await message.answer("Вы не можете удалить последний пост.\n \
            Для перехода к началу используйте команду /admin",
                                 reply_markup=types.ReplyKeyboardRemove())
            return
        else:
            if posts[int(number) - 1].first_post:
                post = posts[len(posts) - int(number)]
                post.first_post = True

            db_sess.delete(posts[int(number) - 1])
            db_sess.commit()

        await message.answer("Пост успешно удален\nДля перехода к началу используйте команду /admin",
                             reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer("Выберите пост для удаления")

    db_sess.close()


async def choose_view_or_edit_post(message: types.Message, state: FSMContext):
    db_sess = db_session.create_session()
    posts = db_sess.query(Posts).all()
    posts.sort(key=lambda x: x.post_id)
    buttons = []
    answer_text = "Выберите пост для просмотра или редактирования\n"
    for i, post in enumerate(posts):
        buttons.append(f"Пост №{i + 1}")
        if post.first_post:
            answer_text += f"{str(i + 1)}. {post.post_name}. (Пост первого сообщения)\n"
        else:
            answer_text += f"{str(i + 1)}. {post.post_name}.\n"

    if len(posts) == 0:
        await message.answer("Нет доступных постов")
    else:
        await EditPosts.wait_for_choose_post_view_or_edit.set()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*buttons)
        await message.answer(answer_text, reply_markup=keyboard)

    db_sess.close()


async def view_or_edit_post(message: types.Message, state: FSMContext):
    db_sess = db_session.create_session()
    if message.text.strip() == "":
        await message.answer("Выберите пост для просмотра или редактирования")
        return

    number = list(message.text.strip().split("№"))[-1]
    if number.isdigit():
        await state.finish()

        # Выбор поста для просмотра или редактирования
        posts = db_sess.query(Posts).all()
        posts.sort(key=lambda x: x.post_id)
        post = posts[int(number) - 1]

        keyboard = types.ReplyKeyboardRemove()

        if post.post_link:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            button = types.InlineKeyboardButton(text=post.label_link, url=post.post_link)
            keyboard.add(button)

        await message.answer(post.post_text, reply_markup=keyboard)

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
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Редактировать данный пост")
        await EditPosts.wait_for_start_edit_post.set()
        await state.update_data(post_id=post.post_id)
        await message.answer("Для перехода к началу используйте команду /admin\n" +
                             "Или отредактируйте данный пост.",
                             reply_markup=keyboard)

    else:
        await message.answer("Выберите пост для просмотра или редактирования")

    db_sess.close()


async def start_edit_post(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Не редактировать эту часть поста")
    await message.answer("Введите название поста (Оно показываться не будет, нужно для навигации)",
                         reply_markup=keyboard)
    await EditPosts.wait_for_edit_name.set()


async def edit_post_name(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Не редактировать эту часть поста")

    db_sess = db_session.create_session()

    if message.text.strip() == "":
        await message.answer("Название не должно являться пустой строкой!", reply_markup=keyboard)
        return
    else:
        if not (message.text.strip() == "Не редактировать эту часть поста"):
            data = await state.get_data()
            post_id = data["post_id"]
            post = db_sess.query(Posts).filter(Posts.post_id == post_id).first()
            post.post_name = message.text.strip()
            db_sess.commit()

    await message.answer("Введите текст поста:", reply_markup=keyboard)
    await EditPosts.wait_for_edit_text.set()

    db_sess.close()


async def edit_post_text(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Не редактировать эту часть поста")

    if message.text.strip() == "":
        await message.answer("Введите текст поста:", reply_markup=keyboard)
        return
    else:
        if not (message.text.strip() == "Не редактировать эту часть поста"):
            db_sess = db_session.create_session()
            data = await state.get_data()
            post_id = data["post_id"]
            post = db_sess.query(Posts).filter(Posts.post_id == post_id).first()
            post.post_text = message.text.strip()
            db_sess.commit()
            db_sess.close()

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*["Не редактировать эту часть поста", "Удалить все фотографии"])
    await message.answer("Загрузите фото для поста\n(Это обязательно должен быть файл фотографии)",
                         reply_markup=keyboard)
    await EditPosts.wait_for_edit_photo.set()


async def edit_post_photo(message: types.Message, state: FSMContext):
    post_data = await state.get_data()
    post_id = post_data["post_id"]
    db_sess = db_session.create_session()

    if message.text:
        if message.text.strip().lower() == "Не добавлять фото".lower() or \
                message.text.strip().lower() == "Не редактировать эту часть поста".lower() or \
                message.text.strip().lower() == "Удалить все фотографии".lower():

            if message.text.strip().lower() == "Удалить все фотографии".lower():
                atts = db_sess.query(Attachments).filter(Attachments.post_id == post_id).all()
                for att in atts:
                    if att.photo:
                        db_sess.delete(att)
                        db_sess.commit()

            await EditPosts.wait_for_edit_docs.set()

            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(*["Не редактировать эту часть поста", "Удалить все документы"])
            await message.answer("Загрузите документ для поста\n(Это обязательно должен быть файл документа)",
                                 reply_markup=keyboard)
            return

    if message.photo:
        atts = db_sess.query(Attachments).filter(Attachments.post_id == post_id).all()
        for att in atts:
            if att.photo:
                db_sess.delete(att)
                db_sess.commit()

        att = Attachments(message.photo[-1].file_id, post_id, True)
        db_sess.add(att)
        db_sess.commit()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Не добавлять фото")
        await message.answer("Фото загруженно успешно\nМожете загрузить ещё фото", reply_markup=keyboard)

    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*["Не редактировать эту часть поста", "Удалить все фотографии"])
        await message.answer("Загрузите фото для поста", reply_markup=keyboard)
    db_sess.close()


async def edit_post_docs(message: types.Message, state: FSMContext):
    post_data = await state.get_data()
    post_id = post_data["post_id"]
    db_sess = db_session.create_session()

    if message.text:
        if message.text.strip().lower() == "Не добавлять документ".lower() or \
                message.text.strip().lower() == "Не редактировать эту часть поста".lower() or \
                message.text.strip().lower() == "Удалить все документы".lower():

            if message.text.strip().lower() == "Удалить все документы".lower():
                atts = db_sess.query(Attachments).filter(Attachments.post_id == post_id).all()
                for att in atts:
                    if not att.photo:
                        db_sess.delete(att)
                        db_sess.commit()

            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(*["Не редактировать эту часть поста", "Удалить ссылку"])
            await message.answer("Прикрепите ссылку к посту.\nПоддерживаются только протоколы HTTP(S) и tg://",
                                 reply_markup=keyboard)
            await EditPosts.wait_for_edit_link.set()
            return

    if message.document:
        atts = db_sess.query(Attachments).filter(Attachments.post_id == post_id).all()
        for att in atts:
            if not att.photo:
                db_sess.delete(att)
                db_sess.commit()

        att = Attachments(message.document.file_id, post_id, False)
        db_sess.add(att)
        db_sess.commit()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Не добавлять документ")
        await message.answer("Документ успешно загружен\nМожете загрузить ещё документы", reply_markup=keyboard)
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*["Не редактировать эту часть поста", "Удалить все фотографии"])
        await message.answer("Загрузите документ для поста", reply_markup=keyboard)


async def edit_post_link(message: types.Message, state: FSMContext):

    if message.text:
        if message.text.strip().lower() == "Не редактировать эту часть поста".lower() or \
                message.text.strip().lower() == "Удалить ссылку".lower():

            if message.text.strip().lower() == "Удалить ссылку".lower():
                db_sess = db_session.create_session()
                data = await state.get_data()
                post_id = data["post_id"]
                post = db_sess.query(Posts).filter(Posts.post_id == post_id).first()
                post.post_link = ""
                post.label_link = ""
                db_sess.commit()
                db_sess.close()

            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(*["Да", "Не редактировать эту часть поста"])
            await message.answer("Сделать пост первым сообщением?", reply_markup=keyboard)
            await EditPosts.wait_for_edit_first.set()

            return

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Не редактировать эту часть поста")

    if message.text and message.text.strip().lower() != "":
        if message.text.split("//")[0].lower() in ["https:", "tg:"]:
            db_sess = db_session.create_session()
            data = await state.get_data()
            post_id = data["post_id"]
            post = db_sess.query(Posts).filter(Posts.post_id == post_id).first()
            post.post_link = message.text.strip()
            db_sess.commit()
            db_sess.close()

            await message.answer("Введите название ссылки.", reply_markup=keyboard)
            await EditPosts.wait_for_edit_label_link.set()
            return

    await message.answer("Прикрепите ссылку к посту\nПоддерживаются только протоколы HTTP(S) и tg://",
                         reply_markup=keyboard)
    await EditPosts.wait_for_edit_link.set()
    return


async def edit_post_label_link(message: types.Message, state: FSMContext):
    if message.text:
        if message.text.strip() == "":
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add("Не редактировать эту часть поста")
            await message.answer("Введите название ссылки.", reply_markup=keyboard)
            await EditPosts.wait_for_edit_label_link.set()
            return
        else:
            db_sess = db_session.create_session()
            data = await state.get_data()
            post_id = data["post_id"]
            post = db_sess.query(Posts).filter(Posts.post_id == post_id).first()
            post.label_link = message.text.strip()
            db_sess.commit()
            db_sess.close()

            await message.answer("Ссылка успешно добавлена!")
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(*["Да", "Не редактировать эту часть поста"])
            await message.answer("Сделать пост первым сообщением?", reply_markup=keyboard)
            await EditPosts.wait_for_edit_first.set()
            return


async def edit_first(message: types.Message, state: FSMContext):
    if message.text.strip().lower() == "Да".lower():
        db_sess = db_session.create_session()
        data = await state.get_data()
        post_id = data["post_id"]

        f_post = db_sess.query(Posts).filter(Posts.first_post).first()
        f_post.first_post = False
        db_sess.commit()

        post = db_sess.query(Posts).filter(Posts.post_id == post_id).first()
        post.first_post = True
        db_sess.commit()
        db_sess.close()

    await state.finish()
    await message.answer("Пост успешно отредактирован\nДля перехода к началу используйте команду /admin",
                         reply_markup=types.ReplyKeyboardRemove())


async def save_post_name(message: types.Message, state: FSMContext):
    if message.text.strip() == "":
        await message.answer("Название не должно являться пустой строкой!")
        return
    await state.update_data(post_name=message.text.strip())

    await message.answer("Введите текст поста:", reply_markup=types.ReplyKeyboardRemove())
    await EditPosts.wait_for_text.set()


async def save_post_text(message: types.Message, state: FSMContext):
    if message.text.strip() == "":
        await message.answer("Введите текст поста:", reply_markup=types.ReplyKeyboardRemove())
        return
    await state.update_data(post_text=message.text.strip())

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Не загружать фото")
    await message.answer("Загрузите фото для поста\n(Это обязательно должен быть файл фотографии)",
                         reply_markup=keyboard)
    await EditPosts.wait_for_photo.set()


async def save_post_photo(message: types.Message, state: FSMContext):
    if message.text and message.text.strip().lower() == "Не загружать фото".lower() or message.text and \
            message.text.strip().lower() == "Не добавлять фото".lower():
        await EditPosts.wait_for_docs.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Не загружать документ")
        await message.answer("Загрузите документ для поста\n(Это обязательно должен быть файл документа)",
                             reply_markup=keyboard)
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
    if message.text and message.text.strip().lower() == "Не загружать документ".lower() or message.text and \
            message.text.strip().lower() == "Не добавлять документ".lower():
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Не прикреплять ссылку к посту.")
        await message.answer("Прикрепите ссылку к посту.\nПоддерживаются только протоколы HTTP(S) и tg://",
                             reply_markup=keyboard)
        await EditPosts.wait_for_link.set()
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


async def save_post_link(message: types.Message, state: FSMContext):
    if message.text and message.text.strip().lower() == "Не прикреплять ссылку к посту.".lower():
        post_data = await state.get_data()

        if "post_link" not in post_data.keys():
            await state.update_data(post_link="")
            await state.update_data(label_link="")

            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(*["Да", "Нет"])
            await message.answer("Сделать пост первым сообщением?", reply_markup=keyboard)
            await EditPosts.wait_for_first.set()

        return

    if message.text and message.text.strip().lower() != "":
        if message.text.split("//")[0].lower() in ["https:", "tg:"]:
            await state.update_data(post_link=message.text.strip())

            await message.answer("Введите название ссылки.", reply_markup=types.ReplyKeyboardRemove())
            await EditPosts.wait_for_label_link.set()
            return

    keyboard = types.ReplyKeyboardMarkup()
    keyboard.add("Не прикреплять ссылку к посту.")
    await message.answer("Прикрепите ссылку к посту\nПоддерживаются только протоколы HTTP(S) и tg://",
                         reply_markup=keyboard)
    await EditPosts.wait_for_link.set()
    return


async def save_post_label_link(message: types.Message, state: FSMContext):
    if message.text:
        if message.text.strip() == "":
            await message.answer("Введите название ссылки.", reply_markup=types.ReplyKeyboardRemove())
            await EditPosts.wait_for_label_link.set()
            return
        else:
            await state.update_data(label_link=message.text.strip())

            await message.answer("Ссылка успешно добавлена!")
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(*["Да", "Нет"])
            await message.answer("Сделать пост первым сообщением?", reply_markup=keyboard)
            await EditPosts.wait_for_first.set()
            return


async def save_post(message: types.Message, state: FSMContext):
    f_p = message.text.strip().lower() == "Да".lower()

    db_sess = db_session.create_session()
    data = await state.get_data()

    # Добавление поста
    if f_p and db_sess.query(Posts).filter(Posts.first_post).all():
        f_post = db_sess.query(Posts).filter(Posts.first_post).all()[0]
        f_post.first_post = False
        db_sess.commit()

    post = Posts(
        data["post_name"],
        data["post_text"],
        data["post_link"],
        data["label_link"],
        f_p
    )
    db_sess.add(post)
    db_sess.commit()

    # Добавление вложений
    try:
        for file_id in data["images"]:
            att = Attachments(file_id, post.post_id, True)
            db_sess.add(att)
            db_sess.commit()
    except Exception:
        pass

    try:
        for file_id in data["docs"]:
            att = Attachments(file_id, post.post_id, False)
            db_sess.add(att)
            db_sess.commit()
    except Exception:
        pass

    await state.finish()
    await message.answer("Пост успешно добавлен\nДля перехода к началу используйте команду /admin",
                         reply_markup=types.ReplyKeyboardRemove())

    db_sess.close()


def register_handlers_edit_posts(dp: Dispatcher, bt: Bot):
    global bot
    bot = bt
    dp.register_message_handler(start_edit, IDFilter(user_id=get_admins()), Text(equals="Редактировать сообщения"),
                                state="*")
    dp.register_message_handler(add_post, IDFilter(user_id=get_admins()), Text(equals="Добавить пост"),
                                state=EditPosts.wait_for_choose_act)
    dp.register_message_handler(choose_delete_post, IDFilter(user_id=get_admins()), Text(equals="Удалить пост"),
                                state=EditPosts.wait_for_choose_act)
    dp.register_message_handler(delete_post, IDFilter(user_id=get_admins()),
                                state=EditPosts.wait_for_choose_post_delete)
    dp.register_message_handler(choose_view_or_edit_post, IDFilter(user_id=get_admins()),
                                Text(equals="Просмотреть или редактировать пост"),
                                state=EditPosts.wait_for_choose_act)
    dp.register_message_handler(view_or_edit_post, IDFilter(user_id=get_admins()),
                                state=EditPosts.wait_for_choose_post_view_or_edit)
    dp.register_message_handler(start_edit_post, IDFilter(user_id=get_admins()),
                                Text(equals="Редактировать данный пост"), state=EditPosts.wait_for_start_edit_post)
    dp.register_message_handler(save_post_name, IDFilter(user_id=get_admins()), state=EditPosts.wait_for_name)
    dp.register_message_handler(edit_post_name, IDFilter(user_id=get_admins()), state=EditPosts.wait_for_edit_name)
    dp.register_message_handler(save_post_text, IDFilter(user_id=get_admins()), state=EditPosts.wait_for_text)
    dp.register_message_handler(edit_post_text, IDFilter(user_id=get_admins()), state=EditPosts.wait_for_edit_text)
    dp.register_message_handler(save_post_photo, IDFilter(user_id=get_admins()), content_types=["photo", "text"],
                                state=EditPosts.wait_for_photo)
    dp.register_message_handler(edit_post_photo, IDFilter(user_id=get_admins()), content_types=["photo", "text"],
                                state=EditPosts.wait_for_edit_photo)
    dp.register_message_handler(save_post_docs, IDFilter(user_id=get_admins()), content_types=["document", "text"],
                                state=EditPosts.wait_for_docs)
    dp.register_message_handler(edit_post_docs, IDFilter(user_id=get_admins()), content_types=["document", "text"],
                                state=EditPosts.wait_for_edit_docs)
    dp.register_message_handler(save_post_link, IDFilter(user_id=get_admins()), content_types=["text"],
                                state=EditPosts.wait_for_link)
    dp.register_message_handler(edit_post_link, IDFilter(user_id=get_admins()), content_types=["text"],
                                state=EditPosts.wait_for_edit_link)
    dp.register_message_handler(save_post_label_link, IDFilter(user_id=get_admins()), content_types=["text"],
                                state=EditPosts.wait_for_label_link)
    dp.register_message_handler(edit_post_label_link, IDFilter(user_id=get_admins()), content_types=["text"],
                                state=EditPosts.wait_for_edit_label_link)
    dp.register_message_handler(save_post, IDFilter(user_id=get_admins()), state=EditPosts.wait_for_first)
    dp.register_message_handler(edit_first, IDFilter(user_id=get_admins()), state=EditPosts.wait_for_edit_first)
