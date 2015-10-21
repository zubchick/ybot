# coding: utf-8
from __future__ import absolute_import
from datetime import datetime, timedelta

from ybot.events import emitter, listener
from ybot.conf import settings
from .telegram import bot

conf = settings[__name__]


@emitter('ybot.coub_weekly', sleep=60)
def weekly():
    day = int(conf.get('day_number', 5))
    hour = int(conf.get('hour', 16))
    minute = int(conf.get('minute', 16))
    now = datetime.now()
    year, _, day = now.isocalendar()

    url = 'https://coub.com/weekly/{year}/{week}'
    if day == day:
        if now.hour == hour and now.minute == minute:
            _, week, _ = (now - timedelta(7)).isocalendar()

            yield url.format(year=year, week=week - 1)


@listener('ybot.coub_weekly')
def send_weekly(name, value):
    ids = conf.get('chat_ids', None)
    ids = ids.split(',') if ids else ()
    for chat_id in ids:
        bot.sendMessage(chat_id=int(chat_id), text=value)
