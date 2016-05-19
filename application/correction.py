from application import app
from application.logformat import format_message
from application.headers import get_headers
from application.http import http_put, http_post
from flask import request, render_template, session
from application.land_charge import build_lc_inputs
from application.form_validation import validate_land_charge
import logging
import json


def get_original_data(number, date):
    originals = {"date": date,
                 "number": number}
    url = app.config['CASEWORK_API_URL'] + '/original'
    headers = {'Content-Type': 'application/json', 'X-Transaction-ID': session['transaction_id']}
    response = http_post(url, data=json.dumps(originals), headers=headers)
    return json.loads(response.text), response.status_code


def build_corrections(data):
    date_as_list = data['reg_date'].split("/")  # dd/mm/yyyy
    number = data['reg_no']
    date = '%s-%s-%s' % (date_as_list[2], date_as_list[1], date_as_list[0])
    session['details_entered'] = {'date': date,
                                  'number': number}
    orig_data, status_code = get_original_data(number, date)
    logging.debug("original data for correction" + json.dumps(orig_data))
    logging.debug("status_code: " + str(status_code))

    fatal = False
    is_banks = False
    error_msg = ''
    if status_code == 200:
        if orig_data['class_of_charge'] == 'PAB' or orig_data['class_of_charge'] == 'WOB':
            is_banks = True
            orig_data['regn_type'] = "banks"
        else:
            orig_data['regn_type'] = "lc"

        session['original_regns'] = orig_data

    elif status_code == 404:
        error_msg = 'No details held for registration number and date entered. Please check and re-key.'
    else:
        fatal = True

    return is_banks, error_msg, status_code, fatal


def register_correction():

    applicant = {'name': session['original_regns']['applicant']['name'],
                 'address': session['original_regns']['applicant']['address'],
                 'key_number': session['original_regns']['applicant']['key_number'],
                 'reference': session['original_regns']['applicant']['reference'],
                 'address_type': session['original_regns']['applicant']['address_type'],

                 }

    registration = {'parties': session['parties'],
                    'class_of_charge': session['original_regns']['class_of_charge'],
                    'applicant': applicant,
                    'update_registration': {'type': 'Correction'}
                    }

    application = {'registration': registration,
                   'orig_regn': session['details_entered'],
                   'update_registration': {'type': 'Correction'}}

    if request.form['generate_K22'] == 'yes':
        application['k22'] = True
    else:
        application['k22'] = False

    url = app.config['CASEWORK_API_URL'] + '/applications/0' + '?action=correction'

    headers = get_headers({'Content-Type': 'application/json'})
    headers['X-Transaction-ID'] = session['transaction_id']
    logging.debug("bankruptcy details: " + json.dumps(application))
    response = http_put(url, data=json.dumps(application), headers=headers)
    if response.status_code == 200:
        logging.info(format_message("Registration (bank) submitted to CASEWORK_API"))
        data = response.json()
        reg_list = []

        for item in data['new_registrations']:
            reg_list.append(item['number'])
        session['confirmation'] = {'reg_no': reg_list}
    return response


def lc_correction_capture():

    result = validate_land_charge(request.form)
    entered_fields = build_lc_inputs(request.form)

    entered_fields['class'] = result['class']

    if len(result['error']) == 0:
        session['rectification_details'] = entered_fields
        return render_template('corrections/lc_check.html',
                               data=entered_fields, application=session,
                               transaction=session['transaction_id'])
    else:
        return render_template('corrections/lc_correct_details.html',
                               data=entered_fields, application=session, screen='capture',
                               transaction=session['transaction_id'], errors=result['error'])


def lc_register_correction():

    details = {
    }

    for key in session['details_entered']:
        details[key] = session['details_entered'][key]

    details['estate_owner']['estate_owner_ind'] = details['estate_owner_ind']

    application = {
        'lc_register_details': details,
        'orig_regn': {
            'date': session['original_regns']['registration']['date'],
            'number': str(session['original_regns']['registration']['number']),
        },
        'update_registration': {'type': 'Correction'},
        'customer_name': session['original_regns']['applicant']['name'],
        'customer_address': session['original_regns']['applicant']['address'],
        'key_number': session['original_regns']['applicant']['key_number'],
        'application_ref': session['original_regns']['applicant']['reference'],
        'address_type': session['original_regns']['applicant']['address_type']
    }

    if request.form['generate_K22'] == 'yes':
        application['k22'] = True
        application['print_location'] = request.form['printLocation'];
    else:
        application['k22'] = False

    url = app.config['CASEWORK_API_URL'] + '/applications/0' + '?action=correction'

    headers = get_headers({'Content-Type': 'application/json'})
    headers['X-Transaction-ID'] = session['transaction_id']
    logging.debug("Land charge correction details: " + json.dumps(application))
    response = http_put(url, data=json.dumps(application), headers=headers)
    if response.status_code == 200:
        logging.info(format_message("Registration (Land charge) submitted to CASEWORK_API"))
        data = response.json()
        reg_list = []

        for item in data['new_registrations']:
            reg_list.append(item['number'])
        session['confirmation'] = {'reg_no': reg_list}
    return response