from flask import session


def get_headers(headers=None):
    if headers is None:
        headers = {}

    if 'transaction-id' in session:
        headers['X-Transaction-ID'] = session['transaction-id']

    if 'username' in session:
        headers['X-LC-Username'] = session['username']

    return headers
