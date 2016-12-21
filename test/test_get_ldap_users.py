#! /usr/bin/env python
# vim: set fileencoding=utf-8 :
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Kirill V. Lyadvinsky
# http://www.codeatcpp.com
#
# Licensed under the BSD 3-Clause license.
# See LICENSE file in the project root for full license information.
#
""" get_ldap_users tests """

import unittest

from domain_users import get_ldap_users

class Test_test_parse_bindings(unittest.TestCase):
    def test_bingings_parser(self):
        bindings = {
            'login': [3, 'sAMAccountName'],
            'description': [4, 'department'],
            'email': [1, 'mail'],
            'phone': [2, 'extensionAttribute7']
            }
        fields = get_ldap_users.parse_bindings(bindings)
        self.assertEqual(fields[0], 'email')


if __name__ == '__main__':
    unittest.main()
