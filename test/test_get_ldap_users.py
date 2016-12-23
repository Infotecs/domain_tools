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
from collections import namedtuple
import tempfile
from mock import patch

from domain_tools import get_ldap_users
from domain_tools.settings import Settings


class TestParseBindings(unittest.TestCase):
    def test_bindings_parser_order(self):
        # Test parser with correct settings
        correct_bindings = {
            'login': [3, 'sAMAccountName'],
            'description': [4, 'department'],
            'email': [1, 'mail'],
            'phone': [2, 'extensionAttribute7']
            }
        settings = Settings()
        settings.use_json_bindings(correct_bindings)
        self.assertEqual(len(settings.field_mapping), 4)
        self.assertEqual(list(settings.field_mapping.items())[0][0], 'email')
        self.assertEqual(list(settings.field_mapping.items())[1][0], 'phone')
        self.assertEqual(list(settings.field_mapping.items())[2][0], 'login')
        self.assertEqual(list(settings.field_mapping.items())[3][0], 'description')

    def test_bindings_parser_incorrect_input(self):
        # Test parser with incorrect settings
        wrong_bindings = {
            'login': ['sAMAccountName'],
            'description': [4, 'department'],
            'email': [1, 'mail'],
            'phone': [2, 'extensionAttribute7']
            }
        settings = Settings()
        with self.assertRaises(TypeError):
            settings.use_json_bindings(wrong_bindings)

    def test_bindings_parser_missing_elements(self):
        # Test bindings with missed elements
        missing_elements = {
            'login': [0, 'sAMAccountName'],
            'description': [10, 'department'],
            'email': [20, 'mail'],
            'phone': [1, 'extensionAttribute7']
            }
        settings = Settings()
        settings.use_json_bindings(missing_elements)
        self.assertEqual(len(settings.field_mapping), 4)
        self.assertEqual(list(settings.field_mapping.items())[0][0], 'login')
        self.assertEqual(list(settings.field_mapping.items())[1][0], 'phone')
        self.assertEqual(list(settings.field_mapping.items())[2][0], 'description')
        self.assertEqual(list(settings.field_mapping.items())[3][0], 'email')

    def test_bindings_parser_one_element(self):
        # Test bindings with missed elements
        one_element = {
            'login': [1000, 'sAMAccountName']
            }
        settings = Settings()
        settings.use_json_bindings(one_element)
        self.assertEqual(len(settings.field_mapping), 1)

    def test_empty_bindings(self):
        # Test empty bindings
        empty_bindings = {}
        settings = Settings()
        settings.use_json_bindings(empty_bindings)
        # fields should contain default
        self.assertEqual(len(settings.field_mapping), 3)
        self.assertEqual(list(settings.field_mapping.items())[0][0], 'domain_name')
        self.assertEqual(list(settings.field_mapping.items())[1][0], 'unit')
        self.assertEqual(list(settings.field_mapping.items())[2][0], 'email')

    def test_none_bindings(self):
        # Test None
        settings = Settings()
        settings.use_json_bindings(None)
        # fields should contain default
        self.assertEqual(len(settings.field_mapping), 3)
        self.assertEqual(list(settings.field_mapping.items())[0][0], 'domain_name')
        self.assertEqual(list(settings.field_mapping.items())[1][0], 'unit')
        self.assertEqual(list(settings.field_mapping.items())[2][0], 'email')


class TestParseSettings(unittest.TestCase):
    def test_empty_file(self):
        settings_file = tempfile.NamedTemporaryFile('r')
        output_file = tempfile.NamedTemporaryFile('w')
        args = namedtuple('Args', "domain_user domain_password settings_file output_file")
        parsed_args = args(None, None, settings_file, output_file)
        get_ldap_users.parse_settings_file(parsed_args)
        settings_file.close()
        output_file.close()

    def test_invalid_file(self):
        """Test incomplete file"""
        settings_file = tempfile.NamedTemporaryFile('w+')
        settings_file.write('{}')
        settings_file.seek(0)
        output_file = tempfile.NamedTemporaryFile('w')
        args = namedtuple('Args', "domain_user domain_password settings_file output_file")
        parsed_args = args('test', 'pass', settings_file, output_file)
        get_ldap_users.parse_settings_file(parsed_args)
        settings_file.close()
        output_file.close()

    def test_valid_file(self):
        """Test correct settings file"""
        settings_file = tempfile.NamedTemporaryFile('w+')
        settings_file.write(
            '{"ldap_server": "192.168.78.12","ldap_port":44445,"use_ssl":true,'
            '"ldap_username":"rollout\\\\Admin","ldap_password":"Qwerty1",'
            '"search_base":"DC=rollout","user_bindings":{"email":[1,"mail"],'
            '"phone":[2,"extensionAttribute7"],"login":[3,"sAMAccountName"],'
            '"description":[4,"department"]}}')
        settings_file.seek(0)
        output_file = tempfile.NamedTemporaryFile('w')
        args = namedtuple('Args', "domain_user domain_password settings_file output_file")
        parsed_args = args('test', None, settings_file, output_file)
        settings = get_ldap_users.parse_settings_file(parsed_args)
        settings_file.close()
        output_file.close()
        self.assertEqual(len(settings.field_mapping), 4)
        self.assertEqual(list(settings.field_mapping.items())[0][1], 'mail')
        self.assertEqual(list(settings.field_mapping.items())[1][1], 'extensionAttribute7')
        self.assertEqual(list(settings.field_mapping.items())[2][1], 'sAMAccountName')
        self.assertEqual(list(settings.field_mapping.items())[3][1], 'department')
        self.assertEqual(settings.ldap_server, '192.168.78.12')
        self.assertEqual(settings.ldap_username, 'test')
        self.assertEqual(settings.ldap_password, 'Qwerty1')
        self.assertEqual(settings.ldap_port, 44445)
        self.assertEqual(settings.use_ssl, True)


class TestSave(unittest.TestCase):
    def test_save_none(self):
        with tempfile.NamedTemporaryFile('w') as output_file:
            entries = ()
            get_ldap_users.save_records_to_csv(entries, None, output_file)

    def test_save_single_record(self):
        with tempfile.NamedTemporaryFile('w+') as output_file:
            settings = Settings()
            bindings = {
                '1': [1, 'sAMAccountName'],
                '2': [4, 'mail'],
            }
            settings.use_json_bindings(bindings)

            entries = ({'attributes': {'mail': 'a@a.a', 'sAMAccountName': 'admin'}},
                       {'attributes': {'mail': 'a@a.a', 'key_error': 'admin'}},)
            total = get_ldap_users.save_records_to_csv(entries, settings.field_mapping, output_file)
            self.assertEquals(total, 2)
            output_file.seek(0)
            data = output_file.readline()
            self.assertEquals(data, 'admin;a@a.a\n')


class TestParamParser(unittest.TestCase):
    def test_help(self):
        with self.assertRaises(SystemExit):
            with patch('sys.argv', ["1.py", "-h", "-v"]):
                get_ldap_users.main()

    def test_version(self):
        with self.assertRaises(SystemExit):
            with patch('sys.argv', ["1.py", "--version"]):
                get_ldap_users.main()


if __name__ == '__main__':
    unittest.main()
