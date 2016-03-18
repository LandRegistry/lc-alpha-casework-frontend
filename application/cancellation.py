from application import app
from application.logformat import format_message
from application.headers import get_headers
from flask import session
import requests
import logging
import json


def submit_lc_cancellation(data):
    cust_address = data['customer_address'].replace("\r\n", ", ").strip()
    application = {'update_registration': {'type': 'Cancellation'},
                   'applicant': {
                       'key_number': data['key_number'],
                       'name': data['customer_name'],
                       'address': data['customer_address'],
                       'address_type': data['address_type'],
                       'reference': data['customer_ref']},
                   'registration_no': session['regn_no'],
                   'document_id': session['document_id'],
                   'registration': {'date': session['reg_date']},
                   'fee_details': {'type': data['payment'],
                                   'fee_factor': 1,
                                   'delivery': session['application_dict']['delivery_method']}}
    if "class_of_charge" in session:
        application["class_of_charge"] = session["class_of_charge"]
    # if plan attached selected then pass the part_cans_text into that field
    if 'cancellation_type' in session:
        application['update_registration'] = {'type': session['cancellation_type']}
        if 'plan_attached' in session:
            if session['plan_attached'] == 'true':
                application['update_registration']['plan_attached'] = session['part_cans_text']
        elif 'part_cans_text' in session:
            application['update_registration']['part_cancelled'] = session['part_cans_text']
    url = app.config['CASEWORK_API_URL'] + '/applications/' + session['worklist_id'] + '?action=cancel'
    headers = get_headers({'Content-Type': 'application/json'})
    response = requests.put(url, data=json.dumps(application), headers=headers)
    if response.status_code == 200:
        logging.info(format_message("Cancellation submitted to CASEWORK_API"))
        data = response.json()
        if 'cancellations' in data:
            reg_list = []
            for item in data['cancellations']:
                reg_list.append(item['number'])
            session['confirmation'] = {'reg_no': reg_list}
        else:
            session['confirmation'] = {'reg_no': []}

    return response
