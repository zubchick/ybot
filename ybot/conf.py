# coding: utf-8
import yaml
settings = None


def parse(fp):
    global settings
    settings = yaml.load(fp)
    return settings
