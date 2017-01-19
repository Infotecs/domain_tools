#! /usr/bin/env python
# vim: set fileencoding=utf-8 :
# -*- coding: utf-8 -*-
#
# Copyright (c) InfoTeCS JSC. All rights reserved.
# Licensed under the MIT license. See LICENSE file
# in the project root for full license information.
#
""" Import users' info from the domain server to the csv file. """

import argparse
import csv
import getpass
import json
import logging
import ssl
import sys

from ldap3 import Server, Connection
from ldap3.core.exceptions import LDAPExceptionError, LDAPOperationResult

from domain_tools import __version__
from domain_tools.settings import Settings

logger = logging.getLogger("get_ldap_users")


def parse_settings_file(parsed_args):
    """ Parse JSON file with settings """
    logger.debug("Passed JSON file with settings: %s",
                 parsed_args.settings_file.name)
    settings = Settings()
    try:
        json_settings = json.load(parsed_args.settings_file)
    except ValueError as exp:
        logger.error("Failed to parse %s: %s",
                     parsed_args.settings_file.name, exp)
        return None

    try:
        settings.from_json(json_settings)
    except KeyError as exp:
        logger.warning("Can't find %s in %s.",
                       exp, parsed_args.settings_file.name)
        return None

    if parsed_args.domain_user is not None:
        settings.ldap_username = parsed_args.domain_user
        logger.debug("Using ldap_username from command line parameters.")
    if parsed_args.domain_password is not None:
        settings.ldap_password = parsed_args.domain_password
        logger.debug("Using ldap_password from command line parameters.")
    return settings


def ask_password(username):
    """ Ask password interactively """
    return getpass.getpass("Please, enter domain password for %s: " % username)


def get_ldap_users(settings):
    """ Get users list from LDAPS server """
    if settings.use_ssl:
        try:
            ldap_server_cert = ssl.get_server_certificate(
                (settings.ldap_server, settings.ldap_port))
            logger.info(ldap_server_cert)
        except (ssl.SSLError, ConnectionError) as exp:
            logger.warning("While trying to get the server certificate: %s",
                           exp)
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
        attributes=list(settings.field_bindings.values()),
        paged_size=10,
        generator=True)
    return entry_generator


def save_records_to_csv(entries, mappings, output_path):
    """Save LDAP records to the CSV file"""
    try:
        with open(output_path, 'w+', newline='', encoding='utf-8') as out_file:
            table = csv.writer(out_file, delimiter=';')
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
            return total_entries
    except (IOError, OSError) as exp:
        logger.error('Failed to open the output file: %s', exp)
        return 0


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
        help="JSON file with settings. See users_bind_template.json for"
             "example. Other parameters are have priority over settings file.")
    import_parser.add_argument(
        'output_file', metavar='OUTPUT-CSV-FILE',
        help="Path to the output csv file.")
    import_parser.add_argument(
        '--preview', dest='preview_result',
        action='store_true',
        help="Preview and edit the result before exporting to a file.")
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


def import_users(args):
    """Import users from domain"""
    settings = parse_settings_file(args)
    if settings is not None:
        if settings.ldap_password == '*':
            settings.ldap_password = ask_password(settings.ldap_username)

        entries = get_ldap_users(settings)
        if entries is not None:
            save_records_to_csv(entries,
                                settings.field_bindings,
                                args.output_file)


def print_sample_json(args):
    """Print sample JSON file"""
    settings = Settings()
    print(settings.to_json(), file=args.output_file)


def main():
    """ Entry point implementation """
    parser = create_parser()
    args = parser.parse_args(sys.argv[1:])
    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s:%(name)s:%(levelname)s:%(message)s',
            datefmt='%Y-%m-%d %H:%M.%S')
        logger.debug("Verbose mode is On.")

    if hasattr(args, 'func'):
        logger.debug(args.func)
        args.func(args)
    else:
        logger.debug("No valid commands so show help.")
        parser.print_help()


if __name__ == "__main__":
    main()
