# coding: utf-8
import yaml
import state as st

settings = None


def parse(fp):
    global settings
    settings = yaml.load(fp)
    return settings


def merge(*dcts):
    start = {}
    for d in dcts:
        start.update(d)

    return start


def _key(module):
    return 'config.' + module


def get_chat_conf(chat_id, module_name, defaults=None):
    """
    Get configuration for module, with chat specifics
    """
    if defaults is None:
        defaults = {}

    state = st.State(chat_id)
    global_conf = settings.get(module_name, {})

    if defaults is None:
        defaults = {}

    state_conf = state.get(_key(module_name), {})
    return merge(defaults, global_conf, state_conf)


def set_chat_conf(chat_id, module_name, **options):
    """
    Set chat specific options for module in state storage
    """
    state = st.State(chat_id)
    key = _key(module_name)
    conf = state.get(key, {})

    for opt_key, opt_value in options.iteritems():
        conf[opt_key] = opt_value

    state.set(key, conf)


def get_module_chat_ids(module_name):
    return st.State().get_chat_ids(_key(module_name))
