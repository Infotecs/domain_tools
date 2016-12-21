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
import io
import unittest
from collections import namedtuple
from domain_users import get_ldap_users


class TestParseBindings(unittest.TestCase):
    def test_bindings_parser_order(self):
        # Test parser with correct settings
        correct_bindings = {
            'login': [3, 'sAMAccountName'],
            'description': [4, 'department'],
            'email': [1, 'mail'],
            'phone': [2, 'extensionAttribute7']
            }
        fields = get_ldap_users.parse_bindings(correct_bindings)
        self.assertEqual(len(fields), 4)
        self.assertEqual(list(fields.items())[0][0], 'email')
        self.assertEqual(list(fields.items())[1][0], 'phone')
        self.assertEqual(list(fields.items())[2][0], 'login')
        self.assertEqual(list(fields.items())[3][0], 'description')

    def test_bindings_parser_incorrect_input(self):
        # Test parser with incorrect settings
        wrong_bindings = {
            'login': ['sAMAccountName'],
            'description': [4, 'department'],
            'email': [1, 'mail'],
            'phone': [2, 'extensionAttribute7']
            }
        with self.assertRaises(TypeError):
            fields = get_ldap_users.parse_bindings(wrong_bindings)

    def test_bindings_parser_missing_elements(self):
        # Test bindings with missed elements
        missing_elements = {
            'login': [0, 'sAMAccountName'],
            'description': [10, 'department'],
            'email': [20, 'mail'],
            'phone': [1, 'extensionAttribute7']
            }
        fields = get_ldap_users.parse_bindings(missing_elements)
        self.assertEqual(len(fields), 4)
        self.assertEqual(list(fields.items())[0][0], 'login')
        self.assertEqual(list(fields.items())[1][0], 'phone')
        self.assertEqual(list(fields.items())[2][0], 'description')
        self.assertEqual(list(fields.items())[3][0], 'email')

    def test_bindings_parser_one_element(self):
        # Test bindings with missed elements
        one_element = {
            'login': [1000, 'sAMAccountName']
            }
        fields = get_ldap_users.parse_bindings(one_element)
        self.assertEqual(len(fields), 1)

    def test_empty_bindings(self):
        # Test empty bindings
        empty_bindings = {}
        fields = get_ldap_users.parse_bindings(empty_bindings)
        # fields should contain default
        self.assertEqual(len(fields), 3)
        self.assertEqual(list(fields.items())[0][0], 'domain_name')
        self.assertEqual(list(fields.items())[1][0], 'unit')
        self.assertEqual(list(fields.items())[2][0], 'email')

    def test_none_bindings(self):
        # Test None
        fields = get_ldap_users.parse_bindings(None)
        # fields should contain default
        self.assertEqual(len(fields), 3)
        self.assertEqual(list(fields.items())[0][0], 'domain_name')
        self.assertEqual(list(fields.items())[1][0], 'unit')
        self.assertEqual(list(fields.items())[2][0], 'email')


class TestParseSettings(unittest.TestCase):
    def test_empty_file(self):
        test_file = io.BytesIO()
        args = namedtuple('Args', "output_file")
        parsed_args = args(test_file)
        get_ldap_users.parse_settings_file(parsed_args)

if __name__ == '__main__':
    unittest.main()
