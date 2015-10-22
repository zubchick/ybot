# coding: utf-8
from copy import deepcopy
from datetime import datetime

import gevent
from crontab import CronTab

from ybot.events import emitter
from ybot.conf import settings

conf = settings[__name__]

emits = [i['emit'] for i in conf]


@emitter(*emits, multi=True)
def cron():
    cnf = deepcopy(conf)

    for item in cnf:
        item['conf'] = CronTab(item['conf'])

    while cnf:
        now = datetime.now()
        for item in cnf:
            if item['conf'].test(now):
                yield item['emit'], item.get('value')

        next_event = min(cnf, key=lambda x: x['conf'].next())
        gevent.sleep(next_event['conf'].next())
