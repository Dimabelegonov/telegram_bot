from data.db import db_session
from data.db.models import Users


def get_admins():
    db_sess = db_session.create_session()
    admins = db_sess.query(Users).filter(Users.is_admin == True).all()
    admins = [x.telegram_id for x in admins]
    return admins