==========================================
Tools to parse and import domain structure
==========================================

.. image:: https://img.shields.io/travis/Infotecs/domain_tools/master.svg?style=flat
   :target: https://travis-ci.org/Infotecs/domain_tools

.. image:: https://codecov.io/gh/Infotecs/domain_tools/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/Infotecs/domain_tools

.. image:: https://img.shields.io/github/release/Infotecs/domain_tools.svg?style=flat
   :target: https://github.com/Infotecs/domain_tools/releases

.. image:: https://img.shields.io/github/issues/Infotecs/domain_tools.svg
   :target: https://github.com/Infotecs/domain_tools/issues

Here's a utility to import users from the specified LDAP server.
The usage is a pretty simple:

   $ get_ldap_users import settings.json output.csv

Use the following command for more info:

   $ get_ldap_users -h

All settings and domain fields' bindings could be customized using settings
file which should be in a JSON format. Run the following to save defaults to
the `settings.json` file:

   $ get_ldap_users gen-defaults settings.json

Parameter `field_bindings` should contain values in the following format:

   {field_internal_name}: [ {field-order}, {domain-field-name} ]

Note, that you can override username/password from the command line. If the
password is `*` (whether in the settings file or in command line parameter) it
will be requested interactively.
