#!/usr/bin/env python

from setuptools import setup

setup(
        name             = 'XenStats',
        version          = '0.1',
        description      = 'write XenServer stats to Graphite',
        author           = 'Sebastian Wiedenroth',
        author_email     = 'sw@core.io',
        url              = 'https://github.com/wiedi/xenstats',
        scripts          = ['xenstats', ],
        install_requires = [
                "XenAPI   == 1.2",
        ],
)