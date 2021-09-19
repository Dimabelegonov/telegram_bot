from sqlalchemy import Column, Integer, String, Boolean, Text
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
    first_post = Column(Boolean, default=False)
    attachments = relationship("Attachments", backref="post", cascade = "all, delete, delete-orphan" )

    def __init__(self, p_name, p_text, f_post, p_id=None) -> SqlAlchemyBase:
        super().__init__()
        self.post_name = p_name
        self.post_text = p_text
        self.first_post = f_post

        if p_id and p_id.__class__ == int:
            self.post_id = p_id

class Attachments(SqlAlchemyBase):
    __tablename__ = "attachments"

    att_id = Column(Integer, primary_key=True, autoincrement=True)
    att_telegram_id = Column(String)
    post_id = Column(Integer, ForeignKey("posts.post_id"))

    def __init__(self, file_id, post) -> SqlAlchemyBase:
        super().__init__()
        self.att_telegram_id = file_id
        self.post_id = post
