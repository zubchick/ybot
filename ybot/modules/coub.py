# coding: utf-8
from ybot.conf import settings
from .telegram import bot
from .cron import cron

conf = settings[__name__]


@cron('ybot.coub_weekly', '0 16 * * fri')
def send_weekly(name, value):
    url = 'https://coub.com/weekly/'

    ids = conf.get('chat_ids', ())
    for chat_id in ids:
        bot.sendMessage(
            chat_id=chat_id,
            text="Thanks god, it's friday! Time to watch some coubs. " + url,
        )
