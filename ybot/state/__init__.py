# coding: utf-8
State = None


class BaseState(object):
    def __init__(self, chat_id):
        self.chat_id = chat_id

    def key(self, name):
        return "%s.%s" % (self.chat_id, name)

    def set(self, name, value):
        return self._set(self.key(name), value)

    def get(self, name):
        return self._get(self.key(name))

    @staticmethod
    def _setup(core_opts):
        raise NotImplementedError

    def _set(self, name, value):
        raise NotImplementedError

    def _get(self, name, default=None):
        raise NotImplementedError
