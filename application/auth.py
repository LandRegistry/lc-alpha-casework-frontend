import os
from ldap3 import Connection, Server, SIMPLE, SYNC
import logging


def authenticate(username, password):
    host = os.getenv('LDAP_HOST', "DEV")

    if host == 'DEV':  # Fake LDAP specified, allow any old nonsense on login (DEV ONLY!)
        logging.warning('No authentication host specified - using DEV mode')
        return {'username': username, 'display_name': 'Test User', 'primary_group': 'blah'}

    port = os.getenv('LDAP_PORT', "")
    domain = os.getenv('LDAP_DOMAIN', "")
    search_dn = os.getenv('LDAP_SEARCH_DN', "")
    caseworkers = os.getenv('CASEWORKER_GROUP', 'not specified')
    administrators = os.getenv('ADMIN_GROUP', 'not specified')
    reprinters = os.getenv('REPRINT_GROUP', 'not specified')

    try:
        logging.info('Logging in %s', username)
        server = Server(host, port=int(port))
        connection = Connection(server, auto_bind=True, client_strategy=SYNC, user=username + domain, password=password,
                                authentication=SIMPLE, check_names=True)
        connection.search(search_dn, '(sAMAccountName=' + username + ")", attributes=['displayName', 'memberOf'])

        display_name = connection.entries[0].displayname
        logging.debug('Display name is %s', display_name)
        primary_group = ''

        admin_match = [g for g in connection.entries[0].memberof if 'CN=' + administrators in g]
        casework_match = [g for g in connection.entries[0].memberof if 'CN=' + caseworkers in g]
        print_match = [g for g in connection.entries[0].memberof if 'CN=' + reprinters in g]

        if len(admin_match) > 0:
            primary_group = administrators
        elif len(casework_match) > 0:
            primary_group = casework_match
        elif len(print_match) > 0:
            primary_group = reprinters

        if display_name != '' and primary_group != '':
            return {'username': username, 'display_name': str(display_name), 'primary_group': primary_group}  # User authenticated and we know their role
        else:
            return None  # None == not authenticated

    except Exception as e:
        logging.error(str(e))
        return None  # None == not authenticated

