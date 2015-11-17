# coding: utf-8
import signal
import logging
import time
from functools import wraps
from collections import defaultdict
from itertools import chain

import gevent
from gevent.queue import Queue

log = logging.getLogger(__name__)

__events = Queue()
__listeners = defaultdict(list)
__emitters = set()
__jobs = []


class Actor(gevent.Greenlet):
    def __init__(self, f):
        super(Actor, self).__init__()
        self.running = False
        self.events = Queue()
        self.f = f

    def _run(self):
        self.running = True
        raise NotImplementedError

    def on_event(self, name, value):
        try:
            return self.f(name, value)
        except Exception:
            log.exception('Exception on event %s in %s listener. Value %s',
                          name, self.f.__name__, value)

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.f.__name__)


def emit(event_name, value):
    """ Emit event with event_name and value """
    log.info('Event %s emited', event_name)
    __events.put((event_name, value))


class Listener(Actor):
    def _run(self):
        self.running = True

        while self.running:
            name, value = self.events.get()
            self.on_event(name, value)
            gevent.sleep(0)


class Splitter(Actor):
    def __init__(self, f, emit_events=(), check=True):
        super(Splitter, self).__init__(f)
        self.emit_events = set(emit_events)
        self.check = check

    def _run(self):
        self.running = True

        while self.running:
            name, value = self.events.get()
            try:
                for event_name, value in self.on_event(name, value):
                    if not self.check or event_name in self.emit_events:
                        emit(event_name, value)
                    else:
                        log.warning("%s emited unknown event %s, on args %s",
                                    self, event_name, (name, value))
            except Exception:
                log.exception('Exception in splitter %s, event %s', self, name)

            gevent.sleep(0)


def listener(*event_names):
    """ Decorator for listener functions

    event_names - names of events, that listener can handle
    """
    def wrapper(f):
        obj = Listener(f)

        for event in set(event_names):
            subscibe(event, obj, _run=False)

        return obj

    return wrapper


def subscibe(event_name, listener_func, _run=True):
    """ Make Listener from listener_func, and subscribe to event_name """
    if not isinstance(listener_func, (Listener, Splitter)):
        listener = Listener(listener_func)
    else:
        listener = listener_func

    __listeners[event_name].append(listener)

    log.info('Lisnter %s subscribed to event %s', listener, event_name)

    if _run:
        listener.start()
        __jobs.append(listener)


def emitter(*event_names, **kwargs):
    """ Decorator for event generators

    event_names - names of events, that generator emits, if multi=False (default)
                  it must be only one event_name, and generator must return only
                  event values

    multi       - optional, default False, if True generator must yields tuples:
                  (event_name, value), all posible event names must be listed
                  in event_names decorator parameter

    sleep       - optional, default 0, timeout between emitter restarts
    check       - optional, default True, check that emited events in event_names
    """
    sleep = kwargs.get('sleep', 0)
    multi = kwargs.get('multi', False)
    event_names = set(event_names)
    check = kwargs.get('check', True)

    def wrapper(f):
        def run():
            start_time = time.time()

            while True:
                try:
                    for item in f():
                        if multi:
                            event_name, value = item
                        else:
                            event_name = list(event_names)[0]
                            value = item

                        if not check or event_name in event_names:
                            emit(event_name, value)
                        else:
                            log.warning(
                                "%s emited unknown event %s",
                                f.__name__, event_name
                            )
                except Exception:
                    if time.time() - start_time < 10:
                        log.critical("Can't run emitter \"%s\" from module %s",
                                     f.__name__, f.__module__)
                        raise
                    else:
                        log.exception("Exception in emitter %s", f.__name__)

                gevent.sleep(sleep)

        gr = gevent.Greenlet(run)
        return __emitters.add(gr)

    return wrapper


def splitter(listen_events, emit_events=(), check=True):
    """ Decorator for event splitter
    decorated function must take two parameters like any listener:
    <event_name> and <value>

    and return generator of tuples like multi emitter:
    (new_event_name, value)

    """
    def wrapper(f):
        obj = Splitter(f, emit_events, check)

        for event in listen_events:
            subscibe(event, obj, _run=False)

        return obj
    return wrapper


def run_emitters():
    for emitter in __emitters:
        gr = emitter
        gr.start()
        __jobs.append(gr)


def run_listeners():
    for listener in set(chain(*__listeners.values())):
        listener.start()
        __jobs.append(listener)


def run_eventloop():
    while True:
        event_name, value = __events.get()

        for listener in __listeners[event_name]:
            log.debug('Send event %s to %s', event_name, listener)
            listener.events.put((event_name, value))

        gevent.sleep(0)


def run_all():
    gevent.signal(signal.SIGQUIT, gevent.kill)
    run_emitters()
    run_listeners()
    eventloop = gevent.spawn(run_eventloop)
    __jobs.append(eventloop)
    gevent.joinall(__jobs, raise_error=True)


def kill_all():
    for job in __jobs:
        if isinstance(job, Actor):
            job.running = False

    gevent.killall(__jobs, block=True)
