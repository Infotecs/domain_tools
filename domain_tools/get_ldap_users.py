#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 InfoTeCS JSC. All rights reserved.
# Author: Kirill V. Lyadvinsky <Kirill.Lyadvinsky@infotecs.ru>
#
# Licensed under the MIT license.
# See LICENSE file in the project root for full license information.
#
""" Import users' info from the domain server to the csv file. """

import logging
import sys
import getpass
import ssl
import csv
import argparse
import json
from ldap3 import Server, Connection
from ldap3.core.exceptions import LDAPExceptionError, LDAPOperationResult

from domain_tools import __version__
from domain_tools.settings import Settings


def parse_settings_file(parsed_args):
    """ Parse JSON file with settings """
    logger = logging.getLogger('parse_settings_file')
    logger.debug("Passed JSON file with settings: %s",
                 parsed_args.settings_file.name)
    settings = Settings()
    try:
        json_settings = json.load(parsed_args.settings_file)
    except ValueError as exp:
        logger.error("Failed to parse settings: %s", exp)
        return settings
    try:
        if parsed_args.domain_user is None:
            settings.ldap_username = json_settings['ldap_username']
        else:
            settings.ldap_username = parsed_args.domain_user
        logger.debug("ldap_username is %s", settings.ldap_username)
        if parsed_args.domain_password is None:
            settings.ldap_password = json_settings['ldap_password']
            logger.debug("Use ldap_password from file.")
        else:
            settings.ldap_password = parsed_args.domain_password
            logger.debug("Use ldap_password from command line parameters.")
        settings.ldap_server = json_settings['ldap_server']
        logger.debug("ldap_server is %s", settings.ldap_server)
        settings.ldap_port = json_settings['ldap_port']
        logger.debug("ldap_port is %s", settings.ldap_port)
        settings.use_ssl = json_settings['use_ssl']
        logger.debug("use_ssl is %s", settings.use_ssl)
        settings.search_base = json_settings['search_base']
        logger.debug("search_base is %s", settings.search_base)
        settings.use_json_bindings(json_settings['field_bindings'])
        logger.debug("field_bindings is ok")
    except KeyError as exp:
        logger.warning("Can't find %s in JSON file.", exp)
    return settings


def ask_password(username):
    """ Ask password interactively """
    return getpass.getpass("Please, enter domain password for %s: " % username)


def get_ldap_users(settings):
    """ Get users list from LDAPS server """
    logger = logging.getLogger('get_ldap_users')
    if settings.use_ssl:
        try:
            ldap_server_cert = ssl.get_server_certificate((settings.ldap_server,
                                                           settings.ldap_port))
            logger.info(ldap_server_cert)
        except (ssl.SSLError, ConnectionError) as exp:
            logger.warning("While trying to get the server certificate: %s", exp)
    ldap_server = Server(settings.ldap_server,
                         port=settings.ldap_port,
                         use_ssl=settings.use_ssl)
    connection = Connection(ldap_server,
                            user=settings.ldap_username,
                            password=settings.ldap_password,
                            raise_exceptions=True)

    try:
        connection.bind()
    except (LDAPExceptionError, LDAPOperationResult) as exp:
        logger.error("Failed to connect to the server: %s", exp)
        return None

    entry_generator = connection.extend.standard.paged_search(
        search_base=settings.search_base,
        search_filter='(objectClass=person)',
        attributes=list(settings.field_mapping.values()),
        paged_size=10,
        generator=True)
    return entry_generator


def save_records_to_csv(entries, mappings, output_path):
    """Save LDAP records to the CSV file"""
    logger = logging.getLogger('save_records_to_csv')
    with open(output_path, 'w+', newline='', encoding='utf-8') as output_file:
        table = csv.writer(output_file, delimiter=';')
        total_entries = 0
        saved_entries = 0
        try:
            for entry in entries:
                total_entries += 1
                try:
                    table.writerow(
                        [entry['attributes'][k] if entry['attributes'][k]
                         else '' for k in mappings.values()])
                except KeyError:
                    continue
                saved_entries += 1
            logger.info("%d entries found.", total_entries)
            print("%d record(s) saved to %s file." %
                  (saved_entries, output_path))
        except (LDAPExceptionError, LDAPOperationResult) as exp:
            logger.error("Failed to retrieve domain entries: %s", exp)
        output_file.close()
        return total_entries


def create_parser():
    """ Parse command line arguments """
    parser = argparse.ArgumentParser(
        description="Import users from LDAP server to csv file")
    parser.add_argument(
        '-v', '--verbose', help="Increase output verbosity",
        action='store_true')
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + __version__,
                        help="Show script version and exit.")

    subparsers = parser.add_subparsers(help="Available commands")
    import_parser = subparsers.add_parser(
        'import',
        help="Import users from domain.")
    import_parser.add_argument(
        '--user', dest='domain_user',
        help="Override domain username for access to the domain.")
    import_parser.add_argument(
        '--password', dest='domain_password',
        help="Override domain user's password.")
    import_parser.add_argument(
        'settings_file', metavar='SETTINGS-FILE',
        type=argparse.FileType('r', encoding='utf-8'),
        help="JSON file with settings. See users_bind_template.json for example"
        ". Other parameters are have priority over settings file.")
    import_parser.add_argument(
        'output_file', metavar='OUTPUT-CSV-FILE',
        help="Path to the output csv file.")
    import_parser.set_defaults(func=import_users)

    generate_parser = subparsers.add_parser(
        'gen-defaults',
        help="Generate sample settings file.")
    generate_parser.add_argument(
        dest='output_file', metavar='OUTPUT-JSON-FILE', nargs='?',
        type=argparse.FileType('w', encoding='utf-8'), default=sys.stdout,
        help="Path to the output JSON file. settings.json, for instance.")
    generate_parser.set_defaults(func=print_sample_json)
    return parser


def safe_parse_args(parser, args):
    """Safely parse arguments"""
    try:
        if len(args) == 0:
            raise ValueError
        options = parser.parse_args(args)
    except ValueError:
        parser.print_help()
        sys.exit(0)
    return options


def import_users(args):
    """Import users from domain"""
    settings = parse_settings_file(args)
    if settings.ldap_password == '*':
        settings.ldap_password = ask_password(settings.ldap_username)

    entries = get_ldap_users(settings)
    if entries is not None:
        save_records_to_csv(entries, settings.field_mapping, args.output_file)


def print_sample_json(args):
    """Print sample JSON file"""
    settings = Settings()
    print(settings.toJSON(), file=args.output_file)


def main():
    """ Entry point implementation """
    args = safe_parse_args(create_parser(), sys.argv[1:])
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    args.func(args)


if __name__ == "__main__":
    main()
