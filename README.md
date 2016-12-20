To get LDAPS certificate use `retrieve_cert.sh` util as follows:

   $ ./retrieve_cert.sh dc01.infotecs-nt:636 > domain_ldap.crt

Also you need to download the root certificate and save it as `domain_root_ca.pem`.

Then use `get_ldap_users.py` to get all domain users. The result will be automatically saved in the `./users.csv` file.
You can modify `get_ldap_users.py` to select fields you need to save.
