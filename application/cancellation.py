from application import app
from flask import session
import requests
import logging
import json


def submit_lc_cancellation(data):

    application = {'update_registration': {'type': 'Cancellation'},
                   'applicant': {
                       'key_number': data['key_number'],
                       'name': data['customer_name'],
                       'address': data['customer_address'],
                       'reference': data['customer_ref']},
                   'registration_no': session['regn_no'],
                   'document_id': session['document_id'],
                   'registration': {'date': session['reg_date']}}
    if 'addl_info' in session:
            application['additional_information'] = session['addl_info']
    url = app.config['CASEWORK_API_URL'] + '/applications/' + session['worklist_id'] + '?action=cancel'
    headers = {'Content-Type': 'application/json'}
    response = requests.put(url, data=json.dumps(application), headers=headers)
    if response.status_code == 200:
        logging.info("200 response here")
        data = response.json()
        if 'cancellations' in data:
            reg_list = []
            for item in data['cancellations']:
                reg_list.append(item['number'])
            session['confirmation'] = {'reg_no': reg_list}
        else:
            session['confirmation'] = {'reg_no': []}

    return response
