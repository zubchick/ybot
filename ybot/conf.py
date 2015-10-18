# coding: utf-8
import ConfigParser
from collections import OrderedDict
settings = None


def parse(fp):
    global settings

    config = ConfigParser.RawConfigParser()
    config.readfp(fp)
    settings = OrderedDict(
        (s, dict(config.items(s))) for s in config.sections()
    )
    return settings
