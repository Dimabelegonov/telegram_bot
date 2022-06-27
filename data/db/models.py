from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from .db_session import SqlAlchemyBase


class Users(SqlAlchemyBase):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String)
    is_admin = Column(Boolean, default=False)

    def __init__(self, tl_id, is_ad=False) -> SqlAlchemyBase:
        super().__init__()
        self.telegram_id = tl_id
        self.is_admin = is_ad


class Posts(SqlAlchemyBase):
    __tablename__ = "posts"

    post_id = Column(Integer, primary_key=True, autoincrement=True)
    post_name = Column(String)
    post_text = Column(Text)
    post_link = Column(String)
    label_link = Column(String)
    first_post = Column(Boolean)
    attachments = relationship("Attachments", backref="post", cascade="all, delete, delete-orphan")
    deferred_ = relationship("Deferred", backref="post", cascade="all, delete, delete-orphan")

    def __init__(self, p_name, p_text, p_link, lb_link, f_post) -> SqlAlchemyBase:
        super().__init__()
        self.post_name = p_name
        self.post_text = p_text
        self.first_post = f_post
        self.post_link = p_link
        self.label_link = lb_link


class Attachments(SqlAlchemyBase):
    __tablename__ = "attachments"

    att_id = Column(Integer, primary_key=True, autoincrement=True)
    att_telegram_id = Column(String)
    post_id = Column(Integer, ForeignKey("posts.post_id"))

    def __init__(self, file_id, post) -> SqlAlchemyBase:
        super().__init__()
        self.att_telegram_id = file_id
        self.post_id = post


class Deferred(SqlAlchemyBase):
    __tablename__ = "deferred"

    dfr_id = Column(Integer, primary_key=True, autoincrement=True)
    dfr_post_id = Column(Integer, ForeignKey("posts.post_id"))
    dfr_date = Column(DateTime(timezone=True), server_default=func.now())

    def __init__(self, post_id, time) -> SqlAlchemyBase:
        super(Deferred, self).__init__()
        self.dfr_post_id = post_id
        self.dfr_date = time

