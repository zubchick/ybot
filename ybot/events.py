# coding: utf-8
import signal
import logging
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

    def __str__(self):
        return "%s: %s" % (self.__class__.__name__, self.f.__name__)

    def __repr__(self):
        return '<' + str(self) + '>'


class Listener(Actor):
    def _run(self):
        self.running = True

        while self.running:
            name, value = self.events.get()
            self.on_event(name, value)
            gevent.sleep(0)


class Splitter(Actor):
    def __init__(self, f, emit_events=()):
        super(Splitter, self).__init__(f)
        self.emit_events = set(emit_events)

    def _run(self):
        self.running = True

        while self.running:
            name, value = self.events.get()
            for event_name, value in self.on_event(name, value):
                if event_name in self.emit_events:
                    emit(event_name, value)
                else:
                    log.warning("%s emited unknown event %s, on args %s",
                                self, event_name, (name, value))

            gevent.sleep(0)


def listener(*event_names):
    """ Decorator for listener functions

    event_names - names of events, that listener can handle
    """
    def wrapper(f):
        obj = Listener(f)

        for event in set(event_names):
            __listeners[event].append(obj)

        return obj

    return wrapper


def emitter(*event_names, **kwargs):
    """ Decorator for event generators

    event_names - names of events, that generator emits, if multi=False (defalt)
                  it must be only one event_name, and generator must return only
                  event values

    multi       - optional, default False, if True generator must yields tuples:
                  (event_name, value), all posible event names must be listed
                  in event_names decorator parameter

    sleep       - optional, default 0, timeout between emitter restarts
    """
    sleep = kwargs.get('sleep', 0)
    multi = kwargs.get('multi', False)
    event_names = set(event_names)

    def wrapper(f):
        @wraps(f)
        def inner():
            def run():
                first_time = True

                while True:
                    try:
                        for item in f():
                            if multi:
                                event_name, value = item
                            else:
                                event_name = list(event_names)[0]
                                value = item

                            if event_name in event_names:
                                emit(event_name, value)
                            else:
                                log.warning(
                                    "%s emited unknown event %s",
                                    f.__name__, event_name
                                )
                    except Exception, e:
                        if first_time:
                            log.critical("Can't run emitter \"%s\" from module %s",
                                         f.__name__, f.__module__)
                            raise e
                        else:
                            log.exception("Exception in emitter %s", f.__name__)
                    else:
                        first_time = False

                    gevent.sleep(sleep)

            return gevent.Greenlet(run)

        __emitters.add(inner)
        return inner
    return wrapper


def splitter(listen_events, emit_events=()):
    """ Decorator for event splitter
    decorated function must take two parameters like any listener:
    <event_name> and <value>

    and return generator of tuples like multi emitter:
    (new_event_name, value)

    """
    def wrapper(f):
        obj = Splitter(f, emit_events)

        for event in listen_events:
            __listeners[event].append(obj)

        return obj
    return wrapper


def run_emitters():
    for emitter in __emitters:
        gr = emitter()
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


def emit(event_name, value):
    """ Emit event with event_name and value """
    log.debug('Event %s emited', event_name)
    __events.put((event_name, value))
