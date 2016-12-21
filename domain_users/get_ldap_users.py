#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (C) 2016 InfoTeCS JSC. All rights reserved.
# Author: Kirill V. Lyadvinsky <Kirill.Lyadvinsky@infotecs.ru>
#

import logging
import sys
import getpass
import ssl
import csv
from collections import OrderedDict
import argparse
from ldap3 import Server, Connection
import tempfile

def ask_parameters(parsed_args):
    """ Find out missed parameters interactively """
    if parsed_args.ldap_server is None:
        default_domain = 'infotecs-nt'
        domain = input("Domain name [%s]: " % default_domain)
        if domain == '':
            domain = default_domain
        parsed_args.ldap_server = domain

    if parsed_args.domain_user is None:
        detected_username = domain + '\\' + getpass.getuser()
        username = input("Domain user name [%s]: " % detected_username)
        if username == '':
            username = detected_username
        parsed_args.domain_user = username

    if parsed_args.domain_password is None:
        password = getpass.getpass("Domain password: ")
        parsed_args.domain_password = password

    if parsed_args.search_base is None:
        default_base = 'OU=Analytics,OU=TDC,OU=InfoTeCS,OU=Company,DC=infotecs-nt'
        search_base = input("Enter search base [%s]: " % default_base)
        if search_base == '':
            search_base = default_base
        parsed_args.search_base = search_base

def get_ldap_users(parsed_args):
    """ Get users list from LDAPS server """
    ldap_server_cert = ssl.get_server_certificate((parsed_args.ldap_server, 636))
    if parsed_args.interactive:
        print(ldap_server_cert)
    cert_temp_file = tempfile.NamedTemporaryFile('w')
    cert_temp_file.writelines(ldap_server_cert)
    cert_temp_file.close()

    #tls = Tls(#validate=ssl.CERT_REQUIRED,
    #          version=ssl.PROTOCOL_TLSv1_2,
    #          #local_certificate_file=cert_temp_file.name,
    #          #ca_certs_file='./domain_root_ca.pem'
    #          )
    ldap_server = Server(parsed_args.ldap_server, port=636, use_ssl=True)

    connection = Connection(parsed_args.ldap_server,
                            user=parsed_args.domain_user,
                            password=parsed_args.domain_password)

    if not connection.bind():
        print('error in bind', connection.result)
        return

    # Map domain fields to the local structure
    fields = OrderedDict((
        ('sAMAccountName', 'domain_name'),
        ('sn', 'surname'),
        ('givenName', 'name'),
        ('department', 'unit'),
        ('mail', 'email')
        ))
    total_entries = 0
    entry_generator = connection.extend.standard.paged_search(
        search_base=parsed_args.search_base,
        search_filter='(objectClass=person)',
        attributes=list(fields.keys()),
        paged_size=5,
        generator=True)

    csv_file = open('./users.csv', 'w', newline='')
    table = csv.writer(csv_file, delimiter=';')
    table.writerow(list(fields.values()))
    for entry in entry_generator:
        try:
            table.writerow([entry['attributes'][k] for k in fields.keys()])
        except KeyError:
            continue
        total_entries += 1
    csv_file.close()
    print("Total entries retrieved: %d" % total_entries, end='')


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
    parser.add_argument('--ldap-address', dest='ldap_server',
                        help="Address of the LDAP server")
    parser.add_argument('--user', dest='domain_user',
                        help="Domain username for access to the domain")
    parser.add_argument('--password', dest='domain_password',
                        help="Domain user's password")
    parser.add_argument('--base', dest='search_base',
                        help="Search base in the domain")
    parser.add_argument('--bindings', dest='bindings_file', type=argparse.FileType('r', 0),
                        help="JSON file with fields bindings. See bind_template.json for example.")

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

    if args.interactive:
        ask_parameters(args)

    get_ldap_users(args)


if __name__ == "__main__":
    main()
