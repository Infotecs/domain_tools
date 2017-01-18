#! /usr/bin/env python
# vim: set fileencoding=utf-8 :
# -*- coding: utf-8 -*-
#
# Copyright (c) InfoTeCS JSC. All rights reserved.
# Licensed under the MIT license. See LICENSE file
# in the project root for full license information.
#
""" Settings keeper implementation """

import json
from collections import OrderedDict
import logging
import pprint

logger = logging.getLogger("settings")


class Settings(object):
    """Settings keeper"""

    def __init__(self, ldap_username='infotecs-jsc\\admin', ldap_password='*',
                 ldap_server='infotecs-jsc', ldap_port=636, use_ssl=True,
                 search_base='OU=DevDept,OU=Company,DC=infotecs-jsc',
                 field_bindings=OrderedDict((
                         ('domain_name', 'sAMAccountName'),
                         ('email', 'mail'),
                         ('unit', 'department')))):
        self.ldap_username = ldap_username
        self.ldap_password = ldap_password
        self.ldap_server = ldap_server
        self.ldap_port = ldap_port
        self.use_ssl = use_ssl
        self.search_base = search_base
        self.field_bindings = field_bindings

    def to_json(self):
        """Serialize settings to JSON string."""
        temp_dict = self.__dict__.copy()
        temp_dict['field_bindings'] = {v[0]: [i, v[1]] for i, v in
                                       enumerate(self.field_bindings.items())}
        return json.dumps(temp_dict, sort_keys=True, indent=4)

    def from_json(self, json_settings):
        """Initialize settings from JSON string."""
        self.ldap_username = json_settings['ldap_username']
        self.ldap_password = json_settings['ldap_password']
        self.ldap_server = json_settings['ldap_server']
        self.ldap_port = json_settings['ldap_port']
        self.use_ssl = json_settings['use_ssl']
        self.search_base = json_settings['search_base']
        self.use_json_bindings(json_settings['field_bindings'])
        logger.debug("Use the following settings:\n%s", pprint.pformat(
                     ["%s=%s" % (x, y if x != 'ldap_password' else '******')
                      for x, y in self.__dict__.items()]))

    def use_json_bindings(self, bindings):
        """Parse domain fields bindings from the settings file."""
        self.field_bindings = None
        if bindings is not None and len(bindings):
            try:
                self.field_bindings = OrderedDict(
                    (k, v[1]) for k, v in sorted(bindings.items(),
                                                 key=lambda x: x[1][0]))
            except (IndexError, TypeError):
                pass
