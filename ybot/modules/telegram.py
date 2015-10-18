# coding: utf-8
from __future__ import absolute_import

import telegram
from ybot.events import emitter
from ybot.conf import settings

conf = settings[__name__]     # 'ybot.modules.telegram'
bot = telegram.Bot(token=conf['token'])


@emitter('ybot.telegram.message')
def updates():
    timeout = conf.get('polling_timeout', 60)
    offset = None

    while True:
        updates = bot.getUpdates(offset=offset, timeout=timeout) or []
        for update in updates:
            offset = update.update_id + 1
            if update.message:
                yield update.message
