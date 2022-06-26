from data.db.models import Posts, Attachments, Users
from aiogram import Bot


async def do_send(post: Posts, bot: Bot, user: Users):
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
