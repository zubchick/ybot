# coding: utf-8
from ybot.events import emitter
from ybot.conf import settings
from gevent.backdoor import BackdoorServer

port = settings[__name__].get('port', 5001)

server = BackdoorServer(('127.0.0.1', port),
                        banner="Hello from gevent backdoor!",
                        locals={})


@emitter()
def backdoor():
    server.serve_forever()
    yield None
