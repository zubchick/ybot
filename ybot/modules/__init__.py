# coding: utf-8
from __future__ import absolute_import, unicode_literals

from ybot.events import listener
from ybot.modules.telegram import bot

__commands = {}


def add_command(name, description):
    __commands[name] = description


@listener('ybot.telegram.command')
def help(name, value):
    if '/help' in value.text.lower():
        text = u'You can control me by sending these commands:\n\n%s'
        cmds = []
        for name, description in sorted(__commands.items()):
            cmds.append('%s - %s' % (name, description))

        bot.sendMessage(chat_id=value.chat_id, text=text % '\n'.join(cmds))


add_command('/help', 'Help message')
