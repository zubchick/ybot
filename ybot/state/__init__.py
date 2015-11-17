# coding: utf-8
State = None


class BaseState(object):
    def __init__(self, chat_id=''):
        self.chat_id = chat_id

    def set(self, name, value):
        return self._set(self._key(name), value)

    def get(self, name, default=None):
        return self._get(self._key(name), default=default)

    def delete(self, name):
        return self._delete(self._key(name))

    def pop(self, name, default=None):
        return self._pop(self._key(name), default)

    def get_chat_ids(self, name):
        ''' all chat ids with key == name '''
        return self._get_chat_ids(self._key(name)) or []

    # methods to override
    @staticmethod
    def _setup(core_opts):
        raise NotImplementedError

    def _key(self, name):
        return str(name)

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

    def _get_chat_ids(self, name):
        raise NotImplementedError
