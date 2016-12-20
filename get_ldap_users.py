#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (C) 2016 InfoTeCS JSC. All rights reserved.
# Author: Kirill V. Lyadvinsky <Kirill.Lyadvinsky@infotecs.ru>
#

import sys
import getpass
from ldap3 import Server, Connection, Tls
import ssl
from ssl import SSLContext
import csv
import tempfile


def get_ldap_users():
    default_domain = 'infotecs-nt'
    domain = input("Domain name [%s]: " % default_domain)
    if domain == '':
        domain = default_domain
    ldap_server_cert = ssl.get_server_certificate((domain, 636))
    print(ldap_server_cert)
    cert_temp_file = tempfile.NamedTemporaryFile('w', delete=False)
    cert_temp_file.writelines(ldap_server_cert)
    cert_temp_file.close()

    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(cert_temp_file.name)
    
    tls = Tls(#validate=ssl.CERT_REQUIRED,
              version=ssl.PROTOCOL_TLSv1_2,
              local_certificate_file=cert_temp_file.name,
              #ca_certs_file='./domain_root_ca.pem'
              )
    s = Server(domain, port=636, use_ssl=True, tls=tls)

    detected_username = domain + '\\' + 'Lyadvinsky.Kir' #getpass.getuser()
    username = input("Domain user name [%s]: " % detected_username)

    if username == '':
        username = detected_username
    password = getpass.getpass("Domain password: ")
    c = Connection(s, user=username, password=password)

    if not c.bind():
        print('error in bind', c.result)
        return 0

    # Map domain fields to the local structure
    fields = {'sAMAccountName': 'domain_name',
              'sn': 'surname',
              'givenName': 'name',
              'department': 'unit',
              'mail': 'email'}
    total_entries = 0
    default_base = 'OU=Analytics,OU=TDC,OU=InfoTeCS,OU=Company,DC=infotecs-nt'
    search_base = input("Enter search base [%s]: " % default_base)
    if search_base == '':
        search_base = default_base
    entry_generator = c.extend.standard.paged_search(
        # search_base is vary from
        search_base=search_base,
        search_filter='(objectClass=person)',
        attributes=list(fields.keys()),
        paged_size=5,
        generator=True)

    csv_file = open('./users.csv', 'w', newline='')
    table = csv.writer(csv_file, delimiter=';')
    for entry in entry_generator:
        user = {}
        try:
            for key in fields.keys():
                user[fields[key]] = entry['attributes'][key]
        except KeyError:
            continue
        table.writerow(list(user.values()))
        total_entries += 1
    csv_file.close()
    print('Total entries retrieved: ', end='')

    return total_entries


def main():
    ldap_users = get_ldap_users()
    print(ldap_users)


if __name__ == "__main__":
    sys.exit(main())
