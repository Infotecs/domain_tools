#! /usr/bin/env python
# vim: set fileencoding=utf-8 :
# -*- coding: utf-8 -*-
#
# Copyright (c) InfoTeCS JSC. All rights reserved.
# Licensed under the MIT license. See LICENSE file
# in the project root for full license information.
#
""" Settings keeper implementation """

from collections import OrderedDict
import json


class Settings(object):
    """Settings keeper"""

    def __init__(self):
        self.ldap_username = 'infotecs-jsc\\user42'
        self.ldap_password = '*'
        self.ldap_server = 'infotecs-jsc'
        self.ldap_port = 636
        self.use_ssl = True
        self.search_base = 'OU=Develop Dept,OU=InfoTeCS,OU=Company,DC=infotecs-jsc'
        self.field_bindings = OrderedDict((
            ('domain_name', 'sAMAccountName'),
            ('email', 'mail'),
            ('unit', 'department')
        ))

    def to_json(self):
        temp_dict = self.__dict__
        temp_dict['field_bindings'] = {v[0]: [i, v[1]] for i, v in
                                       enumerate(self.field_bindings.items())}
        return json.dumps(temp_dict, sort_keys=True, indent=4)

    def use_json_bindings(self, bindings):
        """ Parse domain fields bindings from the settings file """
        if bindings is not None and len(bindings) > 0:
            self.field_bindings = OrderedDict((k, v[1]) for k, v in
                                              sorted(bindings.items(),
                                                     key=lambda x: x[1][0]))
