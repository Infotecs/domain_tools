#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import getpass
from ldap3 import Server, Connection, Tls
import ssl


def get_ldap_users():
    tls = Tls(validate=ssl.CERT_REQUIRED,
              version=ssl.PROTOCOL_TLSv1_2,
              local_certificate_file='./infotecs_ldap.crt',
              ca_certs_file='./infotecs_root_ca.pem')
    s = Server('infotecs-nt', port=636, use_ssl=True, tls=tls)

    password = getpass.getpass("Please enter the ldap password: ")
    c = Connection(s, user="infotecs-nt\\Lyadvinsky.Kir", password=password)

    if not c.bind():
        print('error in bind', c.result)
        return 0

    fields = {'sAMAccountName': 'domain_name',
              'sn': 'surname',
              'givenName': 'name',
              'department': 'unit',
              'mail': 'email'}
    total_entries = 0
    entry_generator = c.extend.standard.paged_search(
        # search_base is vary from
        search_base='OU=Analytics,OU=TDC,OU=InfoTeCS,OU=Company,DC=infotecs-nt',
        search_filter='(objectClass=person)',
        attributes=list(fields.keys()),
        paged_size=5,
        generator=True)

    for entry in entry_generator:
        user = {}
        try:
            for key in fields.keys():
                user[fields[key]] = entry['attributes'][key][0]
        except KeyError:
            continue
        print(user)
        total_entries += 1
    print('Total entries retrieved:', total_entries)

    return 0


def main():
    ldap_users = get_ldap_users()
    print(ldap_users)


if __name__ == "__main__":
    sys.exit(main())
