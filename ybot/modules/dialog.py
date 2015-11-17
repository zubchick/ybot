# coding: utf-8
from __future__ import absolute_import

import logging
from functools import wraps

import telegram

from ybot.state import State
from ybot.events import subscibe, splitter, Listener
from ybot.modules import add_command
from ybot.modules.telegram import bot

log = logging.getLogger(__name__)
__dialogs = []


class Response(object):
    def __init__(self, text, state=None, next=None):
        self.text = text
        self.state = state

        assert callable(next) or next is None, "`next` must be a function, not a %s" % type(next)
        self.next = next


class Dialog(State):
    def key(self, name):
        return super(Dialog, self).key('.'.join(map(str, ['dialog', name])))


def wrap_handler(f):
    @wraps(f)
    def inner(name, value):
        state, store_key, value = value
        dialog = Dialog(value.chat_id)

        try:
            result = f(state, value)
        except Exception:
            log.exception('Exception in dialog handler %s', f)
            return

        if not isinstance(result, Response):
            raise TypeError(
                'Result of handler %s, event %s must be `Response` type, not %s' %
                (f, name, type(f))
            )

        if result.text is not None:
            private = value.chat.type == 'private'
            force_reply = False if private else result.next is not None
            msg = _reply(value.chat_id, result.text, force_reply)

            # change store key if we had an update on group chat
            if not private:
                store_key = msg.message_id

        if result.next is not None:
            state = result.state if result.state is not None else {}
            dialog.set(store_key, (_fname(result.next), state))

    return inner


class DialogHandler(Listener):
    def __init__(self, f):
        super(DialogHandler, self).__init__(wrap_handler(f))


def _fname(f):
    return '.'.join([f.__module__, f.__name__])


def _reply(chat_id, text, force_reply):
    if force_reply:
        kwargs = {'reply_markup': telegram.ForceReply()}
    else:
        kwargs = {}

    return bot.sendMessage(chat_id=chat_id, text=text, **kwargs)


@splitter(['ybot.telegram.message'], check=False)
def dialog_dispatcher(name, value):
    dialog = Dialog(value.chat_id)
    handler_name = None
    state = {}
    store_key = ''

    # trying initial commands
    text = value.text.lower()
    for handler_name, cmd in __dialogs:
        if cmd.lower() in text:
            yield handler_name, (state, store_key, value)
            return

    # dialog continuation in group chat
    if value.chat.type == 'group':
        reply_to = value.reply_to_message
        if reply_to is not None:
            store_key = reply_to.message_id
            handler_name, state = dialog.pop(store_key, (None, {}))

    # dialog continuation in private chat
    elif value.chat.type == 'private':
        store_key = ''
        handler_name, state = dialog.pop(store_key, (None, {}))
    else:
        log.error('Unexpected chat type %s', value.chat.type)
        return

    if handler_name is None:
        return

    yield handler_name, (state, store_key, value)


def create_dialog(config):
    add_command(config['command'], config['description'])

    entry = _fname(config['entrypoint'])
    __dialogs.append((entry, config['command']))
    subscibe(entry, DialogHandler(config['entrypoint']), _run=False)

    for handler in config['handlers']:
        subscibe(_fname(handler), DialogHandler(handler), _run=False)
