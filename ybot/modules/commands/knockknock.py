# coding: utf-8
from __future__ import absolute_import

from ..dialog import Response, create_dialog


def knockknock(state, value):
    return Response(text="Who's there?", next=who_there)


def who_there(state, value):
    who = value.text
    state['who'] = who
    return Response(text='%s who?' % who, state=state, next=finish)


def finish(state, value):
    return Response(text='Okay, "%s". Bye.' % state['who'])


create_dialog({
    'entrypoint': knockknock,
    'command': '/knockknock',
    'description': 'Dialog example',

    'handlers': [
        who_there,
        finish,
    ]
})
