#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 InfoTeCS JSC. All rights reserved.
# Author: Kirill V. Lyadvinsky <Kirill.Lyadvinsky@infotecs.ru>
#
# Licensed under the MIT license.
# See LICENSE file in the project root for full license information.
#
""" Settings keeper implementation """

from collections import OrderedDict


class Settings(object):
    """Settings keeper"""
    def __init__(self):
        self.ldap_username = ''
        self.ldap_password = ''
        self.ldap_server = ''
        self.ldap_port = 636
        self.search_base = ''
        self.field_mapping = OrderedDict((
                ('domain_name', 'sAMAccountName'),
                ('unit', 'department'),
                ('email', 'mail')
                ))
       
    def __repr__(self, **kwargs):
        return super().__repr__(**kwargs)

    def use_json_bindings(self, bindings):
        """ Parse domain fields bindings from the settings file """
        if bindings is not None and len(bindings) > 0:
            self.field_mapping = OrderedDict((k, v[1]) for k, v in
                                        sorted(bindings.items(),
                                               key=lambda x: x[1][0]))
