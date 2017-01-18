#! /usr/bin/env python
# vim: set fileencoding=utf-8 :
# -*- coding: utf-8 -*-
#
# Copyright (c) InfoTeCS JSC. All rights reserved.
# Licensed under the MIT license. See LICENSE file
# in the project root for full license information.
#
""" get_ldap_users tests """
import os
import tempfile
import unittest
from unittest.mock import patch
from collections import namedtuple
import logging

from domain_tools import get_ldap_users
from domain_tools.settings import Settings


class TestParseBindings(unittest.TestCase):
    """Test parsing field_bindings."""
    def setUp(self):
        """Initialize logger"""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s:%(name)s:%(levelname)s:%(message)s',
            datefmt='%Y-%m-%d %H:%M.%S')

    def test_order(self):
        """Test parser with correct settings."""
        correct_bindings = {
            'login': [3, 'sAMAccountName'],
            'description': [4, 'department'],
            'email': [1, 'mail'],
            'phone': [2, 'extensionAttribute7']
        }
        settings = Settings()
        settings.use_json_bindings(correct_bindings)
        self.assertEqual(len(settings.field_bindings), 4)
        self.assertEqual(list(settings.field_bindings.items())[0][0], 'email')
        self.assertEqual(list(settings.field_bindings.items())[1][0], 'phone')
        self.assertEqual(list(settings.field_bindings.items())[2][0], 'login')
        self.assertEqual(
            list(settings.field_bindings.items())[3][0], 'description')

    def test_invalid_input(self):
        """Test parser with incorrect settings."""
        wrong_bindings = {
            'login': ['sAMAccountName'],
            'description': [4, 'department'],
            'email': [1, 'mail'],
            'phone': [2, 'extensionAttribute7'],
            'aaa': []
        }
        settings = Settings()
        settings.use_json_bindings(wrong_bindings)
        self.assertIsNone(settings.field_bindings)

    def test_missing_elements(self):
        """Test bindings with missed elements."""
        missing_elements = {
            'login': [0, 'sAMAccountName'],
            'description': [10, 'department'],
            'email': [20, 'mail'],
            'phone': [1, 'extensionAttribute7']
        }
        settings = Settings()
        settings.use_json_bindings(missing_elements)
        self.assertEqual(len(settings.field_bindings), 4)
        self.assertEqual(list(settings.field_bindings.items())[0][0], 'login')
        self.assertEqual(list(settings.field_bindings.items())[1][0], 'phone')
        self.assertEqual(
            list(settings.field_bindings.items())[2][0], 'description')
        self.assertEqual(list(settings.field_bindings.items())[3][0], 'email')

    def test_one_element(self):
        """Test bindings with missed elements."""
        one_element = {
            'login': [1000, 'sAMAccountName']
        }
        settings = Settings()
        settings.use_json_bindings(one_element)
        self.assertEqual(len(settings.field_bindings), 1)

    def test_empty_bindings(self):
        """Test empty bindings."""
        empty_bindings = {}
        settings = Settings()
        settings.use_json_bindings(empty_bindings)
        # fields should contain default
        self.assertIsNone(settings.field_bindings)

    def test_none_bindings(self):
        """Test None."""
        settings = Settings()
        settings.use_json_bindings(None)
        # fields should contain default
        self.assertIsNone(settings.field_bindings)


class TestParseSettings(unittest.TestCase):
    """Test parsing settings file."""
    def setUp(self):
        """Initialize logger"""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s:%(name)s:%(levelname)s:%(message)s',
            datefmt='%Y-%m-%d %H:%M.%S')

    def test_empty_file(self):
        """Test empty input file."""
        with tempfile.NamedTemporaryFile('r') as settings_file,\
                tempfile.NamedTemporaryFile('w') as output_file:
            args = namedtuple(
                'Args',
                "domain_user domain_password settings_file output_file")
            parsed_args = args(None, None, settings_file, output_file)
            self.assertFalse(parsed_args.settings_file.closed)
            self.assertFalse(parsed_args.output_file.closed)
            settings = get_ldap_users.parse_settings_file(parsed_args)
        self.assertIsNone(settings)

    def test_invalid_file(self):
        """Test incomplete file."""
        with tempfile.NamedTemporaryFile('w+') as settings_file,\
                tempfile.NamedTemporaryFile('w') as output_file:
            settings_file.write('{"field_bindings":{"email":[1 "mail"],}}')
            settings_file.seek(0)
            args = namedtuple(
                'Args',
                "domain_user domain_password settings_file output_file")
            parsed_args = args('test', 'pass', settings_file, output_file)
            self.assertFalse(parsed_args.settings_file.closed)
            self.assertFalse(parsed_args.output_file.closed)
            settings = get_ldap_users.parse_settings_file(parsed_args)
        self.assertIsNone(settings)

    def test_lost_required_parameters(self):
        """Test incomplete file."""
        with tempfile.NamedTemporaryFile('w+') as settings_file,\
                tempfile.NamedTemporaryFile('w') as output_file:
            settings_file.write('{}')
            settings_file.seek(0)
            args = namedtuple(
                'Args',
                "domain_user domain_password settings_file output_file")
            parsed_args = args('test', 'pass', settings_file, output_file)
            self.assertFalse(parsed_args.settings_file.closed)
            self.assertFalse(parsed_args.output_file.closed)
            settings = get_ldap_users.parse_settings_file(parsed_args)
        self.assertIsNone(settings)

    def test_valid_file(self):
        """Test correct settings file."""
        with tempfile.NamedTemporaryFile('w+') as settings_file,\
                tempfile.NamedTemporaryFile('w') as output_file:
            settings_file.write(
                '{"ldap_server": "192.168.78.12","ldap_port":44445,'
                '"use_ssl":true,"ldap_username":"infotecs\\\\Admin",'
                '"ldap_password":"Qwerty1","search_base":"DC=infotecs",'
                '"field_bindings":{"email":[1,"mail"],'
                '"phone":[2,"extensionAttribute7"],'
                '"login":[3,"sAMAccountName"],'
                '"description":[4,"department"]}}')
            settings_file.seek(0)
            args = namedtuple(
                'Args',
                "domain_user domain_password settings_file output_file")
            parsed_args = args('test', None, settings_file, output_file)
            self.assertFalse(parsed_args.settings_file.closed)
            self.assertFalse(parsed_args.output_file.closed)
            settings = get_ldap_users.parse_settings_file(parsed_args)
        self.assertIsNotNone(settings)
        self.assertEqual(len(settings.field_bindings), 4)
        self.assertEqual(list(settings.field_bindings.items())[0][1], 'mail')
        self.assertEqual(
            list(settings.field_bindings.items())[1][1], 'extensionAttribute7')
        self.assertEqual(
            list(settings.field_bindings.items())[2][1], 'sAMAccountName')
        self.assertEqual(
            list(settings.field_bindings.items())[3][1], 'department')
        self.assertEqual(settings.ldap_server, '192.168.78.12')
        self.assertEqual(settings.ldap_username, 'test')
        self.assertEqual(settings.ldap_password, 'Qwerty1')
        self.assertEqual(settings.ldap_port, 44445)
        self.assertEqual(settings.use_ssl, True)

    def test_print_default_settings(self):
        """Test default settings generator."""
        default_settings = Settings()

        temp_file, temp_path = tempfile.mkstemp()
        with patch('sys.argv', ["1.py", "gen-defaults", temp_path]):
            get_ldap_users.main()

        with open(temp_path) as settings_file:
            args = namedtuple(
                'Args', "domain_user domain_password settings_file")
            parsed_args = args(None, 'pass word', settings_file)
            self.assertFalse(parsed_args.settings_file.closed)
            settings = get_ldap_users.parse_settings_file(parsed_args)
        self.assertIsNotNone(settings)
        self.assertNotEqual(default_settings.__dict__, settings.__dict__)
        self.assertEqual(settings.ldap_password, 'pass word')
        settings.ldap_password = '*'
        self.assertEqual(default_settings.__dict__, settings.__dict__)
        os.close(temp_file)
        os.remove(temp_path)


class TestSave(unittest.TestCase):
    """Test results serializing."""
    def setUp(self):
        """Initialize logger"""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s:%(name)s:%(levelname)s:%(message)s',
            datefmt='%Y-%m-%d %H:%M.%S')

    def test_invalid_output(self):
        """Test invalid output path will be processed correctly."""
        invalid_path = ''
        entries = ()
        total = get_ldap_users.save_records_to_csv(entries, None, invalid_path)
        self.assertEqual(total, 0)

    def test_save_none(self):
        """Test None output."""
        temp_file, temp_path = tempfile.mkstemp()
        entries = ()
        total = get_ldap_users.save_records_to_csv(entries, None, temp_path)
        self.assertEqual(total, 0)
        os.close(temp_file)
        os.remove(temp_path)

    def test_save_special_symbols(self):
        """Test emoji characters."""
        temp_file, temp_path = tempfile.mkstemp()
        settings = Settings()
        bindings = {
            '1': [1, 'sAMAccountName'],
            '2': [4, 'mail'],
        }
        settings.use_json_bindings(bindings)
        entries = ({'attributes':
                    {'mail': 'a@a.a', 'sAMAccountName': 'ad;"min♌💃 '}},)
        total = get_ldap_users.save_records_to_csv(
            entries, settings.field_bindings, temp_path)
        self.assertEqual(total, 1)
        with open(temp_path, encoding='utf-8') as output_file:
            data = output_file.read()
        os.close(temp_file)
        os.remove(temp_path)
        self.assertEqual(data, '"ad;""min♌💃 ";a@a.a\n')

    def test_save_single_record(self):
        """Test single correct record."""
        temp_file, temp_path = tempfile.mkstemp()
        settings = Settings()
        bindings = {
            '1': [1, 'sAMAccountName'],
            '2': [4, 'mail'],
        }
        settings.use_json_bindings(bindings)
        entries = ({'attributes':
                    {'mail': 'a@a.a', 'sAMAccountName': 'admin'}},
                   {'attributes':
                    {'mail': 'a@a.a', 'key_error': 'admin'}})
        total = get_ldap_users.save_records_to_csv(entries,
                                                   settings.field_bindings,
                                                   temp_path)
        self.assertEqual(total, 2)
        with open(temp_path, encoding='utf-8') as output_file:
            data = output_file.read()
        os.close(temp_file)
        os.remove(temp_path)
        self.assertEqual(data, 'admin;a@a.a\n')

    def test_save_two_records(self):
        """Test two correct records."""
        temp_file, temp_path = tempfile.mkstemp()
        settings = Settings()
        bindings = {
            '1': [1, 'sAMAccountName'],
            '2': [4, 'mail'],
        }
        settings.use_json_bindings(bindings)
        entries = ({'attributes':
                    {'mail': 'b@b.b', 'sAMAccountName': 'admin'}},
                   {'attributes':
                    {'mail': 'z@z.z', 'key_error': 'adminok'}},
                   {'attributes':
                    {'mail': 'a@a.a', 'sAMAccountName': 'adminka'}})
        total = get_ldap_users.save_records_to_csv(entries,
                                                   settings.field_bindings,
                                                   temp_path)
        self.assertEqual(total, 3)
        with open(temp_path, encoding='utf-8') as output_file:
            data = output_file.read()
        os.close(temp_file)
        os.remove(temp_path)
        self.assertEqual(data, 'admin;b@b.b\nadminka;a@a.a\n')


class TestParamParser(unittest.TestCase):
    """Test parameters parser."""
    def test_help(self):
        """Test exit when help flag passed."""
        with self.assertRaises(SystemExit):
            with patch('sys.argv', ["1.py", "-h", "-v"]):
                get_ldap_users.main()

    def test_verbose(self):
        """Test exit when only verbose flag passed."""
        try:
            with patch('sys.argv', ["1.py", "-v"]):
                get_ldap_users.main()
        except AssertionError as exp:
            self.fail("Unexpected exception: %s" % exp)

    def test_version(self):
        """Test exit when version flag passed."""
        with self.assertRaises(SystemExit):
            with patch('sys.argv', ["1.py", "--version"]):
                get_ldap_users.main()

    def test_no_args(self):
        """Test exit when no arguments passed."""
        try:
            with patch('sys.argv', ["1.py"]):
                get_ldap_users.main()
        except AssertionError as exp:
            self.fail("Unexpected exception: %s" % exp)


if __name__ == '__main__':
    unittest.main()
