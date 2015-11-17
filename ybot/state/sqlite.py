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
                      (id integer primary key,
                       updated integer,
                       chat_id integer,
                       key text,
                       value blob
        )''')
        c.execute('''create index if not exists key_kv on kv (key)''')
        c.execute('''create index if not exists chat_id_kv on kv (chat_id)''')
        c.execute('''create unique index if not exists key_chat_id on kv (key, chat_id)''')

        conn.commit()

    def _set(self, name, value):
        value = json.dumps(value).encode('utf-8')
        name = name.encode('utf-8')

        c = conn.cursor()

        c.execute('''insert or replace into
                       kv(updated, chat_id, key, value) values(?, ?, ?, ?)''',
                  (datetime.now().strftime('%s'), self.chat_id, name, value))

        conn.commit()

    def _get(self, name, default=None):
        name = name.encode('utf-8')
        c = conn.cursor()

        c.execute('''select value from kv where key=? and `chat_id`=?''',
                  (name, self.chat_id)
        )
        res = c.fetchone()
        if not res:
            return default
        else:
            return json.loads(res[0])

    def _delete(self, name):
        c = conn.cursor()
        c.execute('''delete from kv where key=? and chat_id=?''',
                  (name, self.chat_id)
        )
        conn.commit()

    def _get_chat_ids(self, name):
        c = conn.cursor()

        c.execute('''select chat_id from kv where key=?''', (name,))
        return [i[0] for i in c.fetchall()]
