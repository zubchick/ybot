# coding: utf-8

from ybot.events import listener


@listener('ybot.telegram.message')
def echo(event_name, value):
    assert event_name == 'ybot.telegram.message'
    print value.text
