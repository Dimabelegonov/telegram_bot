import configparser
from dataclasses import dataclass


@dataclass
class TgBot():
    token: str
    admin_id: int
    db: str


@dataclass
class Config:
    tg_bot: TgBot


def load_config(path: str):
    config = configparser.ConfigParser()
    config.read(path)

    tg_bot = config["tg_bot"]

    return Config(
        tg_bot=TgBot(
            token=tg_bot["token"],
            admin_id=list(map(int, tg_bot["admin_id"].split(", "))),
            db=tg_bot["db"]
        )
    )
