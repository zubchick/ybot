# coding: utf-8

from ybot.events import listener
from ybot.modules.comands import add_command
from ..telegram import bot


@listener('ybot.telegram.command')
def pong(event_name, value):
    if value.text and value.text.startswith('/ping'):
        bot.sendMessage(chat_id=value.chat_id, text='pong')

add_command('/ping', 'Checks that bot is still here')
