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
from collections import OrderedDict
import argparse
import tempfile
import json
from ldap3 import Server, Connection


def parse_settings_file(parsed_args):
    """ Parse JSON file with settings """
    logger = logging.getLogger('parse_settings_file')
    if parsed_args.settings_file is not None:
        logger.debug("Passed JSON file with settings: %s",
                     parsed_args.settings_file.name)
        settings = json.load(parsed_args.settings_file)
        # Parse standard parameters
        if parsed_args.ldap_server is None:
            try:
                parsed_args.ldap_server = settings['ldap_server']
                logger.debug("Use ldap_server from JSON file: %s",
                             parsed_args.ldap_server)
            except KeyError:
                logger.warning("Can't find ldap_server in JSON file.")
        else:
            logger.debug("Use ldap_server from command line: %s",
                         parsed_args.ldap_server)

        if parsed_args.domain_user is None:
            try:
                parsed_args.domain_user = settings['ldap_username']
                logger.debug("Use domain_user from JSON file: %s",
                             parsed_args.domain_user)
            except KeyError:
                logger.warning("Can't find ldap_username in JSON file.")
        else:
            logger.debug("Use domain_user from command line: %s",
                         parsed_args.domain_user)

        if parsed_args.domain_password is None:
            try:
                parsed_args.domain_password = settings['ldap_password']
                logger.debug("Use domain_password from JSON file,"
                             " but not showing you.")
            except KeyError:
                logger.warning("Can't find domain_password in JSON file.")
        else:
            logger.debug("Use domain_password from command line,"
                         " but not showing you.")

        if parsed_args.search_base is None:
            try:
                parsed_args.search_base = settings['search_base']
                logger.debug("Use search_base from JSON file: %s",
                             parsed_args.search_base)
            except KeyError:
                logger.warning("Can't find search_base in JSON file.")
        else:
            logger.debug("Use search_base from command line: %s",
                         parsed_args.search_base)

        if parsed_args.ldap_port is None:
            try:
                parsed_args.ldap_port = settings['ldap_port']
                logger.debug("Use ldap_port from JSON file: %s",
                             parsed_args.ldap_port)
            except KeyError:
                logger.warning("Can't find ldap_port in JSON file.")
        else:
            logger.debug("Use ldap_port from command line: %s",
                         parsed_args.search_base)

        # Parse domain fields bindings
        try:
            bindings = settings['user_bindings']
            return bindings
        except KeyError:
            logger.warning("Can't find user_bindings in JSON file.")


def parse_bindings(bindings):
    """ Parse domain fields bindings from the settings file """
    if bindings is None:
        # Use default bindings if were not set
        fields = OrderedDict((
            ('domain_name', 'sAMAccountName'),
            ('unit', 'department'),
            ('email', 'mail')
            ))
    else:
        fields = OrderedDict((k, v[1]) for k, v in
                             sorted(bindings.items(), key=lambda x: x[1][0]))

    return fields


def ask_parameters(parsed_args):
    """ Find out missed parameters interactively """
    if parsed_args.ldap_server is None:
        default_domain = 'infotecs-nt'
        domain = input("Domain name [%s]: " % default_domain)
        if domain == '':
            domain = default_domain
        parsed_args.ldap_server = domain

    if parsed_args.ldap_port is None:
        default_port = '636'
        domain_port = input("Domain port [%s]: " % default_port)
        if domain_port == '':
            domain_port = default_port
        parsed_args.ldap_port = domain_port

    if parsed_args.domain_user is None:
        detected_username = parsed_args.ldap_server + '\\' + getpass.getuser()
        username = input("Domain user name [%s]: " % detected_username)
        if username == '':
            username = detected_username
        parsed_args.domain_user = username

    if parsed_args.domain_password is None:
        password = getpass.getpass("Domain password: ")
        parsed_args.domain_password = password

    if parsed_args.search_base is None:
        default_base = 'OU=Company,DC=%s' % parsed_args.ldap_server
        search_base = input("Enter search base [%s]: " % default_base)
        if search_base == '':
            search_base = default_base
        parsed_args.search_base = search_base


def get_ldap_users(parsed_args, bindings):
    """ Get users list from LDAPS server """
    logger = logging.getLogger('get_ldap_users')

    ldap_server_cert = ssl.get_server_certificate((parsed_args.ldap_server,
                                                   parsed_args.ldap_port))
    logger.info(ldap_server_cert)
    cert_temp_file = tempfile.NamedTemporaryFile('w')
    cert_temp_file.writelines(ldap_server_cert)
    cert_temp_file.close()
    logger.info("LDAPS server certificate was saved to %s file.",
                cert_temp_file.name)

    # TODO: verify server certificate
    #tls = Tls(#validate=ssl.CERT_REQUIRED,
    #          version=ssl.PROTOCOL_TLSv1_2,
    #          #local_certificate_file=cert_temp_file.name,
    #          #ca_certs_file='./domain_root_ca.pem'
    #          )
    ldap_server = Server(parsed_args.ldap_server,
                         port=parsed_args.ldap_port,
                         use_ssl=True)
    connection = Connection(ldap_server,
                            user=parsed_args.domain_user,
                            password=parsed_args.domain_password)

    if not connection.bind():
        logger.error("Error connecting server: %s", connection.result)
        return

    total_entries = 0
    fields = parse_bindings(bindings)
    entry_generator = connection.extend.standard.paged_search(
        search_base=parsed_args.search_base,
        search_filter='(objectClass=person)',
        attributes=list(fields.values()),
        paged_size=5,
        generator=True)

    table = csv.writer(parsed_args.output_file, delimiter=';')
    for entry in entry_generator:
        try:
            table.writerow([entry['attributes'][k] for k in fields.values()])
        except KeyError:
            continue
        total_entries += 1
    parsed_args.output_file.close()
    print("%d record(s) saved to %s file." %
          (total_entries, parsed_args.output_file.name))


def create_parser():
    """ Parse command line arguments """
    parser = argparse.ArgumentParser(
        description="Import users from LDAP server to csv file")
    parser.add_argument(
        '-v', '--verbose', help="Increase output verbosity",
        action='store_true')
    parser.add_argument('-i', '--interactive', dest='interactive',
                        help="Ask all parameters interactivly",
                        action='store_true')
    parser.add_argument('--ldap-server', dest='ldap_server',
                        help="Address of the LDAP server.")
    parser.add_argument('--ldap-port', dest='ldap_port',
                        help="LDAP server port.")
    parser.add_argument('--user', dest='domain_user',
                        help="Domain username for access to the domain.")
    parser.add_argument('--password', dest='domain_password',
                        help="Domain user's password.")
    parser.add_argument('--base', dest='search_base',
                        help="Search base in the domain.")
    parser.add_argument('output_file', metavar='output-file',
                        type=argparse.FileType('w', encoding="utf-8"),
                        help="Path to the output csv file.")
    parser.add_argument('--settings', dest='settings_file',
                        type=argparse.FileType('r', encoding="utf-8"),
                        help="JSON file with settigns. See users_bind_template"
                        ".json for example. Other parameters are have priority"
                        " over settings file.")

    return parser


def safe_parse_args(parser, args):
    """Safely parse arguments"""
    try:
        options = parser.parse_args(args)
        if (options.ldap_server is None or
                options.domain_user is None or
                options.domain_password is None) and not options.interactive:
            raise ValueError
    except ValueError:
        parser.print_help()
        sys.exit(0)

    return options


def main():
    """ Entry point implementation """
    args = safe_parse_args(create_parser(), sys.argv[1:])
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    bindings = parse_settings_file(args)

    if args.interactive:
        ask_parameters(args)

    get_ldap_users(args, bindings)


if __name__ == "__main__":
    main()
