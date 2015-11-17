# coding: utf-8
from __future__ import absolute_import, unicode_literals

import re
from collections import defaultdict
from datetime import datetime
from functools import partial

import requests
from gevent.pool import Pool

from ybot.events import emitter, listener
from ybot.modules.dialog import create_dialog, Response
from ybot.modules.telegram import bot
from ybot.state import State
from ybot.conf import settings, get_chat_conf, set_chat_conf, get_module_chat_ids


repo_name = re.compile(r'(?P<organization>[\w_-]+)/(?P<repository>[\w_-]+)')
module_name = __name__
error_msg = ('This is not a github repository, please use this format: '
             '`organization_or_user/repo_name`')

default_options = {
    'watch_list': (),
}
conf = settings[module_name]

session = requests.Session()
if 'token' in conf:
    session.headers = {'Authorization': 'token ' + conf['token']}


def get_repo(text):
    res = repo_name.search(text or '')
    if res:
        return res.groups()
    else:
        return None


def get_new_pr(since, repo):
    date_format = '%Y-%m-%dT%H:%M:%SZ'
    owner, name = repo
    url = 'https://{host}/api/v3/repos/{owner}/{repo}/pulls'.format(
        host=conf['host'], owner=owner, repo=name)
    res = session.get(url)

    if not res.ok:
        return (repo, None)

    new_prs = []
    for pr in res.json():
        if datetime.strptime(pr['created_at'], date_format) > since:
            new_prs.append(pr)

    return new_prs


@emitter('ybot.github.newpr', sleep=30)
def watch_pr():
    state_key = 'github_pr.last_updated'
    date_format = '%Y-%m-%dT%H:%M:%SZ'

    st = State()
    last_updated = st.get(state_key)
    st.set(state_key, datetime.utcnow().strftime(date_format))

    if last_updated is None:
        # first run
        return
    else:
        last_updated = datetime.strptime(last_updated, date_format)

    watched = defaultdict(list)
    for chat_id in get_module_chat_ids(module_name):
        wl = get_chat_conf(chat_id, module_name, default_options)['watch_list']
        for repo in wl:
            watched[tuple(repo)].append(chat_id)

    if not watched:
        return

    pool = Pool(10)
    res = pool.imap_unordered(partial(get_new_pr, last_updated), watched)

    for prs in res:
        for pr in prs:
            repo = get_repo(pr['base']['repo']['full_name'])
            pr['chat_ids'] = watched[repo]
            yield pr


@listener('ybot.github.newpr')
def notify_about_new_pr(name, pr):
    text = 'Github. %s new pull request %s:\n%s (by %s)' % (
        pr['base']['repo']['full_name'],
        pr['html_url'],
        pr['title'],
        pr['user']['login'],
    )

    for chat_id in pr.get('chat_ids', []):
        bot.sendMessage(chat_id, text=text)


def github(state, value):
    text = '''Watch for new pull requests in your github repository
    and notify about them.

    Usage:
    /add <org/repo_name> to add new repository to watchlist
    /remove <org/repo_name> to remove repository from watchlist
    /list for list of watching repositories
    '''
    return Response(text=text, next=select_subcomand)


def select_subcomand(state, value):
    text = value.text.lower()
    if '/add' in text:
        return add_handler(state, value)
    elif '/remove' in text:
        return remove_handler(state, value)
    elif '/list' in text:
        return list_handler(state, value)
    else:
        return Response(text='Unknown comand')


def add_handler(state, value):
    repo = get_repo(value.text)
    if repo:
        conf = get_chat_conf(value.chat_id, module_name, default_options)
        watch_list = list(conf['watch_list'])
        watch_list.append(repo)
        set_chat_conf(value.chat_id, module_name, watch_list=watch_list)

        msg = ('I will notify about all pull requests in %s repository'
               % '/'.join(repo))

        return Response(text=msg)
    else:
        return Response(text=error_msg, next=add_handler)


def remove_handler(state, value):
    repo = get_repo(value.text)
    if repo:
        conf = get_chat_conf(value.chat_id, module_name, default_options)
        watch_list = set(conf['watch_list'])
        if repo in watch_list:
            watch_list.remove(repo)
            set_chat_conf(value.chat_id, module_name, watch_list=list(watch_list))
            return Response(text='Deleted.')
        else:
            return Response(text='Repository not in watchlist.')
    else:
        return Response(text=error_msg)


def list_handler(state, value):
    conf = get_chat_conf(value.chat_id, module_name, default_options)
    watch_list = conf['watch_list']
    url = 'https://%s/' % conf['host']

    if watch_list:
        msg = 'Watched:\n%s' % '\n'.join(url + '/'.join(r) for r in watch_list)
        return Response(text=msg)
    else:
        return Response(text="Your watchlist is empty")


create_dialog({
    'entrypoint': github,
    'command': '/github',
    'description': 'Send notifications about new pull requests',

    'handlers': [
        select_subcomand,
        add_handler,
    ],
})
