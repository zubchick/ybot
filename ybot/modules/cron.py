# coding: utf-8
from copy import deepcopy
from datetime import datetime

import gevent
from crontab import CronTab

from ybot.events import emitter, listener
from ybot.conf import settings

conf = settings.get(__name__, [])


@emitter(multi=True, check=False)
def cron_scheduler():
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


def cron(event_name, schedule, value=None):
    """Special decorator for simple cron events listeners

    event_name - name of event that will be emited and handled by
    decorated function
    schedule - string in cron format ("*/2 * * * *", "0 16 * * fri", etc.)
    value - default: None, value that will be passed to decorated function

    """
    conf.append({'emit': event_name, 'conf': schedule, 'value': value})
    return listener(event_name)
