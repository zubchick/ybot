# coding: utf-8
from datetime import datetime, timedelta

from ybot.events import listener
from ybot.conf import settings
from .telegram import bot

conf = settings[__name__]


@listener('ybot.coub_weekly')
def send_weekly(name, value):
    last_fiday = datetime.now() - timedelta(7)
    url = 'https://coub.com/weekly/{year}/{week}'
    year, week, _ = last_fiday.isocalendar()

    ids = conf.get('chat_ids', ())
    for chat_id in ids:
        bot.sendMessage(
            chat_id=chat_id,
            text=("Thanks god, it's friday! Time to watch some coubs. " +
                  url.format(year=year, week=week)
              )
        )
