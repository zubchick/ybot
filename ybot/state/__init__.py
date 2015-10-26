# coding: utf-8
State = None


class BaseState(object):
    def __init__(self, chat_id):
        self.chat_id = chat_id

    def key(self, name):
        return "%s.%s" % (self.chat_id, name)

    def set(self, name, value):
        return self._set(self.key(name), value)

    def get(self, name, default=None):
        return self._get(self.key(name), default=default)

    def delete(self, name):
        return self._delete(self.key(name))

    def pop(self, name, default=None):
        return self._pop(self.key(name), default)

    # methods to override
    @staticmethod
    def _setup(core_opts):
        raise NotImplementedError

    def _set(self, name, value):
        raise NotImplementedError

    def _get(self, name, default=None):
        raise NotImplementedError

    def _delete(self, name):
        raise NotImplementedError

    def _pop(self, name, default=None):
        res = self._get(name)
        if res is not None:
            self._delete(name)
        else:
            res = default

        return res
