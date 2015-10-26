# coding: utf-8
from __future__ import absolute_import

import logging

import telegram

from ybot.state import State
from ybot.events import subscibe
from .telegram import bot


log = logging.getLogger(__name__)
__dialogs = {}


class Response(object):
    def __init__(self, text, state=None, next=None):
        self.text = text
        self.state = state

        assert(callable(next) or next is None,
               "`next` must be a function, not a %s" % type(next))
        self.next = next


class Dialog(State):
    def __init__(self, chat_id, name):
        super(Dialog, self).__init__(chat_id)
        self.name = name

    def key(self, name):
        return super(Dialog, self).key('.'.join(map(str, [self.name, name])))


def fname(f):
    return '.'.join([f.__module__, f.__name__])


def _reply(chat_id, text, force_reply):
    if force_reply:
        kwargs = {'reply_markup': telegram.ForceReply()}
    else:
        kwargs = {}

    return bot.sendMessage(chat_id=chat_id, text=text, **kwargs)


def get_dialog_dispatcher(conf):
    def _dispatch(name, value):
        entry = conf['']
        dialog_name = entry.command
        entry_command = entry.command.lower()

        dialog = Dialog(value.chat_id, dialog_name)

        privat = False

        # if it's initial command
        if entry_command in value.text.lower():
            state = {}
            handler_name = ''
            store_key = ''

        # dialog continuation in group chat
        elif value.chat.type == 'group':
            reply_to = value.reply_to_message
            if reply_to is None:
                return

            store_key = reply_to.message_id
            handler_name, state = dialog.pop(store_key, (None, {}))

        # dialog continuation in privat chat
        elif value.chat.type == 'private':
            store_key = ''
            handler_name, state = dialog.pop(store_key, (None, {}))
            privat = True
        else:
            return

        if handler_name is None:
            return

        handler = conf[handler_name]
        state = {} if state is None else state

        try:
            result = handler(state, value)
        except Exception:
            log.exception('Exception in dialog handler %s, dialog %s',
                          handler, dialog_name)
            return

        if not isinstance(result, Response):
            raise TypeError('Result of dialog %s, handler %s '
                            'must be `Response` type, not %s' %
                            (dialog_name, handler, type(handler)))

        if result.text is not None:
            force_reply = False if privat else result.next is not None
            msg = _reply(value.chat_id, result.text, force_reply)

            # change store key if we had an update
            store_key = msg.message_id

        if result.next is not None:
            dialog.set(store_key, (fname(result.next), result.state))

    _dispatch.__name__ = conf[''].__name__
    return _dispatch


def create_dialog(config):
    __dialogs[config['command']] = config['description']
    entry = config['entrypoint']
    entry.command = config['command']

    disp_conf = {'': entry}

    for handler in config['handlers']:
        disp_conf[fname(handler)] = handler

    disp = get_dialog_dispatcher(disp_conf)

    subscibe('ybot.telegram.message', disp, _run=False)
