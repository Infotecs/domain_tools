#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Kirill V. Lyadvinsky
# http://www.codeatcpp.com
#
# Licensed under the BSD 3-Clause license.
# See LICENSE file in the project root for full license information.
#
""" Setup script """

import re

from os.path import join, dirname

from setuptools import setup, find_packages

with open(join(dirname(__file__), 'domain_users', '__init__.py'), 'r') as f:
    VERSION_INFO = re.match(r".*__version__ = '(.*?)'", f.read(), re.S).group(1)

with open('README.rst') as f:
    LONG_README = f.read()

DEV_REQUIRES = [
    'pytest>=2.8',
    'coverage>=3.7.1',
]

INSTALL_REQ = [
    'ldap3>=2.1.1',
]

setup(
    name='domain_tools',
    version=VERSION_INFO,
    description='Parse and import domain structure',
    keywords='ldap domain import users windows ldaps',
    long_description=LONG_README,
    author='Kirill V. Lyadvinsky',
    author_email='mail@codeatcpp.com',
    download_url='https://github.com/jia3ep/domain_tools',
    url='http://www.codeatcpp.com',
    license='BSD-3-Clause',
    packages=find_packages(exclude=('test', 'docs')),
    tests_require=['mock'],
    extras_require={
        'test': DEV_REQUIRES,
    },
    install_requires=INSTALL_REQ,
    test_suite='test',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
    entry_points={
        'console_scripts': [
            'get_ldap_users = domain_users.get_ldap_users:main',
        ],
    },
)
