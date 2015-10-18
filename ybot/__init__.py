# coding: utf-8
import sys
import logging
from gevent import monkey

from .conf import parse
from .events import run_all, kill_all

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)

monkey.patch_all()
log = logging.getLogger(__name__)


def setup(core_opts):
    pass


def load_modules(modules_conf):
    for module_name, options in modules_conf.items():
        try:
            __import__(module_name)
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
        log.exception('Unhandled exception')
    finally:
        kill_all()

if __name__ == '__main__':
    main()
