from application import app
from flask import Response, session
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
                   'regn_no': session['regn_no'],
                   'registration': {'date': session['reg_date']},
                   'document_id': session['document_id']}

    url = app.config['CASEWORK_API_URL'] + '/applications/' + session['worklist_id'] + '?action=cancel'
    headers = {'Content-Type': 'application/json'}
    response = requests.put(url, data=json.dumps(application), headers=headers)
    if response.status_code == 200:
        logging.info("200 response here")
        data = response.json()

        if 'new_registrations' in data:
            reg_list = []
            for item in data['new_registrations']:
                reg_list.append(item['number'])
            session['confirmation'] = {'reg_no': reg_list}
        else:
            session['confirmation'] = {'reg_no': []}

    return Response(status=200)
