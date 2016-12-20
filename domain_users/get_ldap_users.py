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

def ask_parameters(parsed_args):
    """ Find out missed parameters interactively """
    print("Hello")


def get_ldap_users(parsed_args):
    """ Get users list from LDAPS server """
    default_domain = 'infotecs-nt'
    domain = input("Domain name [%s]: " % default_domain)
    if domain == '':
        domain = default_domain
    ldap_server_cert = ssl.get_server_certificate((domain, 636))
    print(ldap_server_cert)
    #cert_temp_file = tempfile.NamedTemporaryFile('w')
    #cert_temp_file.writelines(ldap_server_cert)
    #cert_temp_file.close()

    #tls = Tls(#validate=ssl.CERT_REQUIRED,
    #          version=ssl.PROTOCOL_TLSv1_2,
    #          #local_certificate_file=cert_temp_file.name,
    #          #ca_certs_file='./domain_root_ca.pem'
    #          )
    ldap_server = Server(domain, port=636, use_ssl=True)

    detected_username = domain + '\\' + 'Lyadvinsky.Kir' #getpass.getuser()
    username = input("Domain user name [%s]: " % detected_username)

    if username == '':
        username = detected_username
    password = getpass.getpass("Domain password: ")
    connection = Connection(ldap_server, user=username, password=password)

    if not connection.bind():
        print('error in bind', connection.result)
        return 0

    # Map domain fields to the local structure
    fields = OrderedDict((
        ('sAMAccountName', 'domain_name'),
        ('sn', 'surname'),
        ('givenName', 'name'),
        ('department', 'unit'),
        ('mail', 'email')
        ))
    total_entries = 0
    default_base = 'OU=Analytics,OU=TDC,OU=InfoTeCS,OU=Company,DC=infotecs-nt'
    search_base = input("Enter search base [%s]: " % default_base)
    if search_base == '':
        search_base = default_base
    entry_generator = connection.extend.standard.paged_search(
        search_base=search_base,
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
    print('Total entries retrieved: ', end='')

    return total_entries

def create_parser():
    """ Parse command line arguments """
    parser = argparse.ArgumentParser(
        description="Import users from LDAP server to csv file")
    parser.add_argument(
        '-v', '--verbose', help="Increase output verbosity",
        action='store_true')
    parser.add_argument('-i', '--interactive', dest='interactive',
                        help="Ask all parameters interactivly", action='store_true')
    parser.add_argument('--ldap-address', dest='ldap_server',
                        help="Address of the LDAP server")
    parser.add_argument('--user', metavar='domain_user',
                        help="Domain username for access to the domain")
    parser.add_argument('--password', metavar='domain_password',
                        help="Domain user's password")

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


def main(parser):
    """ Entry point implementation """
    args = safe_parse_args(parser, sys.argv[1:])
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if args.interactive:
        ask_parameters(args)

    get_ldap_users(args)


if __name__ == "__main__":
    main(create_parser())
