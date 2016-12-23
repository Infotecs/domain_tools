==========================================
Tools to parse and import domain structure
==========================================

Here's a utility to import users from the specified LDAP server.
The usage is a pretty simple:

   $ get_ldap_users import settings.json output.csv

Use the following command for more info:

   $ get_ldap_users -h

All settings and domain fields' bindings are could be placed in a settings file
which should be in a JSON format. See `users_bind_template.json` for an example.
Parameter `user_bindings` should contain values in the following format:

   {field_iternal_name}: [ {field-order}, {domain-field-name} ]

Note, that you can override username/password from the command line. If the
password is * (whether in the settings file or in command line parameter) it
will be requested interactively.