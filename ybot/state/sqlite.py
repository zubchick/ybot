# coding: utf-8
import sqlite3
import json
from datetime import datetime

from ybot.state import BaseState

conn = None


class State(BaseState):
    @staticmethod
    def _setup(core_opts):
        global conn

        path = core_opts['ybot.state.sqlite'].get('db_path', ':memory:')
        conn = sqlite3.connect(path)

        c = conn.cursor()

        c.execute('''create table if not exists kv
                      (updated text, key text primary key, value text)''')

        conn.commit()

    def _set(self, name, value):
        value = json.dumps(value).encode('utf-8')
        name = name.encode('utf-8')

        c = conn.cursor()

        c.execute('''insert or replace into
                       kv(updated, key, value) values(?, ?, ?)''',
                  (datetime.now().isoformat(), name, value))

        conn.commit()

    def _get(self, name, default=None):
        name = name.encode('utf-8')
        c = conn.cursor()

        c.execute('''select value from kv where key=?''', (name,))
        res = c.fetchone()
        if not res:
            return default
        else:
            return json.loads(res[0])

    def _delete(self, name):
        c = conn.cursor()
        c.execute('''delete from kv where key=?''', (name,))
        conn.commit()
