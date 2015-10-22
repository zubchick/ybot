# coding: utf-8
from ybot.events import emitter
from gevent.backdoor import BackdoorServer

server = BackdoorServer(('127.0.0.1', 5001),
                        banner="Hello from gevent backdoor!",
                        locals={})

@emitter()
def backdoor():
    server.serve_forever()
    yield None
