from flask import session


def format_message(message):
    transid = ''
    if 'transaction_id' in session:
        transid = "T:{}".format(session['transaction_id'])

    userstr = ''
    if 'username' in session:
        userstr = "U:{}".format(session['username'])

    return "{} {} {}".format(transid, userstr, message)
