# coding: utf-8
from setuptools import setup, find_packages

setup(
    name='ybot',
    version='0.1',
    description='Extensible telegram bot',

    author='Nikita Zubkov',
    author_email='zubchick@yandex.ru',
    packages=find_packages(),
    install_requires=['gevent>=1.0.2', 'PyYAML>=3.11'],

    entry_points={
        'console_scripts': [
            'ybot = ybot:main',
        ],
    },
)
