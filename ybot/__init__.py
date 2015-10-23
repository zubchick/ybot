# coding: utf-8
import sys
import logging
from importlib import import_module
from gevent import monkey

from .conf import parse
from .events import run_all, kill_all
from . import state

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)

monkey.patch_all()
log = logging.getLogger(__name__)


def setup(core_opts):
    # logging
    level = core_opts['log_level']
    logging.root.setLevel(level)

    # state backend
    backend = core_opts.get('state_backend', 'ybot.state.sqlite')
    try:
        module = import_module(backend)
    except ImportError:
        log.error("Can't import %s state backend", backend)
        raise

    module.State._setup(core_opts)
    state.State = module.State


def load_modules(modules_conf):
    for module_name, options in modules_conf.items():
        try:
            import_module(module_name)
        except ImportError:
            log.error("Can't import %s module", module_name)
            raise


def main():
    conf = parse(open(sys.argv[1]))
    core_opts = conf.pop('core', {})
    setup(core_opts)
    load_modules(conf)

    try:
        run_all()
    except KeyboardInterrupt:
        log.info('Exit')
    except Exception:
        log.critical('Unhandled exception, exit')
    finally:
        kill_all()

if __name__ == '__main__':
    main()
