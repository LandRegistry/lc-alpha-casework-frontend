from application import app
from application.logformat import format_message
from flask import Response, request, render_template, session, redirect, url_for
import requests
from datetime import datetime
import logging
import json


def get_original_data(number, date):
    originals = {"date": date,
                 "number": number}
    url = app.config['CASEWORK_API_URL'] + '/original'
    headers = {'Content-Type': 'application/json', 'X-Transaction-ID': session['transaction_id']}
    response = requests.post(url, data=json.dumps(originals), headers=headers)
    return json.loads(response.text), response.status_code


def build_original_data(data):
    wob_originals = []
    pab_originals = []
    if data['wob_ref'] != '':
        wob_date_as_list = data['wob_date'].split("/")  # dd/mm/yyyy
        number = data['wob_ref']
        date = '%s-%s-%s' % (wob_date_as_list[2], wob_date_as_list[1], wob_date_as_list[0])
        session['wob_entered'] = {'date': date,
                                  'number': number}
        wob_data, wob_status_code = get_original_data(number, date)
        if wob_status_code == 200:
            if wob_data['class_of_charge'] != 'WOB':
                wob_status_code = 404
                wob_data = {}
            else:
                wob_originals = wob_data['parties'][0]['names']
    else:
        wob_data = {}
        wob_status_code = 200

    if data['pab_ref'] != '':

        pab_date_as_list = data['pab_date'].split("/")  # dd/mm/yyyy
        number = data['pab_ref']
        date = '%s-%s-%s' % (pab_date_as_list[2], pab_date_as_list[1], pab_date_as_list[0])
        session['pab_entered'] = {'date': date,
                                  'number': number}

        pab_data, pab_status_code = get_original_data(number, date)
        if pab_status_code == 200:
            if pab_data['class_of_charge'] != 'PAB':
                pab_status_code = 404
                pab_data = {}
            else:
                pab_originals = pab_data['parties'][0]['names']

    else:
        pab_data = {}
        pab_status_code = 200

    if len(wob_data) > 0:
        session['original_regns'] = wob_data
    else:
        session['original_regns'] = pab_data
        # form type needs to be set to PAB to ensure class of charge set correctly.
        session['application_dict']['form'] = 'PA(B) Amend'

    curr_data = {'wob': {'date': data['wob_date'],
                         'number': data['wob_ref'],
                         'originals': wob_originals},
                 'pab': {'date': data['pab_date'],
                         'number': data['pab_ref'],
                         'originals': pab_originals}
                 }

    fatal = False
    error_msg = ''
    status_code = wob_status_code

    if wob_status_code == 200 and pab_status_code == 200:
        error_msg = ''
    elif wob_status_code == 404 and pab_status_code == 404:
        error_msg = 'No details held for the PAB and WOB entered, please check and re-key.'
    elif wob_status_code == 404:
        if pab_status_code == 200:
            error_msg = 'No details held for WOB entered, please check and re-key.'
        else:
            fatal = True
            status_code = pab_status_code
    elif pab_status_code == 404:
        if wob_status_code == 200:
            error_msg = 'No details held for PAB entered, please check and re-key.'
        else:
            fatal = True
            status_code = wob_status_code
    else:
        fatal = True

    return curr_data, error_msg, status_code, fatal


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
    error_msg = ''
    if status_code == 200:
        if orig_data['class_of_charge'] == 'PAB' or orig_data['class_of_charge'] == 'WOB':
            session['original_regns'] = orig_data
        else:
            error_msg = 'This is not a bankruptcy application. Please check and re-key.'
    elif status_code == 404:
        error_msg = 'No details held for registration number and date entered. Please check and re-key.'
    else:
        fatal = True

    return error_msg, status_code, fatal


def get_debtor_details(data):
    logging.debug("Start of get debtor details " + json.dumps(data))
    counter = 1
    names = []
    while True:
        forenames = "forenames_" + str(counter)
        surname = "surname_" + str(counter)
        if surname in data and data[surname] != ' ':
            private = {'forenames': data[forenames].split(),
                       'surname': data[surname]}
            names.append({'type': 'Private Individual',
                          'private': private})
        else:
            break
        counter += 1
    counter = 1
    addresses = []
    # TODO: what if the residence is witheld????
    while True:
        addr1_counter = "add_" + str(counter) + "_line1"
        addr2_counter = "add_" + str(counter) + "_line2"
        addr3_counter = "add_" + str(counter) + "_line3"
        addr4_counter = "add_" + str(counter) + "_line4"
        addr5_counter = "add_" + str(counter) + "_line5"
        county_counter = "county_" + str(counter)
        postcode_counter = "postcode_" + str(counter)
        address = {'address_lines': []}
        if addr1_counter in data and data[addr1_counter] != '':
            address['address_lines'].append(data[addr1_counter])
        else:
            break
        if addr2_counter in data and data[addr2_counter] != '':
            address['address_lines'].append(data[addr2_counter])
        if addr3_counter in data and data[addr3_counter] != '':
            address['address_lines'].append(data[addr3_counter])
        if addr4_counter in data and data[addr4_counter] != '':
            address['address_lines'].append(data[addr4_counter])
        if addr5_counter in data and data[addr5_counter] != '':
            address['address_lines'].append(data[addr5_counter])

        address['county'] = data[county_counter]
        address['postcode'] = data[postcode_counter]
        address['type'] = 'Residence'
        address['address_string'] = ' '.join(address['address_lines']) + ' ' + data[county_counter] + ' ' + \
                                    data[postcode_counter]
        addresses.append(address)
        counter += 1

    if 'court' in data:
        session['court_info'] = {'legal_body': data['court'],
                                 'legal_body_ref_no': data['ref_no'],
                                 'legal_body_ref_year': data['ref_year']}

    case_reference = session['court_info']['legal_body'] + ' ' + session['court_info']['legal_body_ref_no'] + \
        ' of ' + session['court_info']['legal_body_ref_year']

    parties = [
        {
            'type': 'Debtor',
            'names': names,
            'addresses': addresses,
            'occupation': data['occupation'],
            'residence_withheld': False,
            'trading_name': ' ',
            'case_reference': case_reference,
            'legal_body': session['court_info']['legal_body'],
            'legal_body_ref_no': session['court_info']['legal_body_ref_no'],
            'legal_body_ref_year': session['court_info']['legal_body_ref_year']
        }
    ]

    return parties


def register_bankruptcy(key_number=None):
    if key_number is None:
        applicant = {'name': session['original_regns']['customer_details']['customer_name'],
                     'address': session['original_regns']['customer_details']['customer_address'],
                     'key_number': session['original_regns']['customer_details']['key_number'],
                     'reference': session['original_regns']['customer_details']['application_ref']}
    else:
        url = app.config['CASEWORK_API_URL'] + '/keyholders/' + key_number
        response = requests.get(url, headers={'X-Transaction-ID': session['transaction_id']})
        text = json.loads(response.text)
        if response.status_code == 200:
            cust_address = ' '.join(text['address']['address_lines']) + ' ' + text['address']['postcode']
            cust_name = ' '.join(text['name'])
            applicant = {'name': cust_name,
                         'address': cust_address,
                         'key_number': key_number,
                         'reference': ' '}
        else:
            return response

    if session['application_dict']['form'] == 'PA(B)' or session['application_dict']['form'] == 'PA(B) Amend':
        class_of_charge = 'PAB'
    elif session['application_dict']['form'] == 'WO(B)' or session['application_dict']['form'] == 'WO(B) Amend':
        class_of_charge = 'WOB'
    else:
        class_of_charge = session['application_dict']['form']

    registration = {'parties': session['parties'],
                    'class_of_charge': class_of_charge,
                    'applicant': applicant
                    }

    application = {'registration': registration,
                   'application_data': session['application_dict']['application_data'],
                   'form': session['application_dict']['form']}

    if session['application_type'] == 'bank_amend':
        # TODO: update registration added twice to get around bad structure for rectifications which needs changing!
        application['update_registration'] = {'type': 'Amendment'}
        application['registration']['update_registration'] = {'type': 'Amendment'}
        if 'wob_entered' in session:
            application['wob_original'] = session['wob_entered']
        if 'pab_entered' in session:
            application['pab_original'] = session['pab_entered']
        url = app.config['CASEWORK_API_URL'] + '/applications/' + session['worklist_id'] + '?action=amend'
    else:
        url = app.config['CASEWORK_API_URL'] + '/applications/' + session['worklist_id'] + '?action=complete'

    headers = {'Content-Type': 'application/json', 'X-Transaction-ID': session['transaction_id']}
    logging.debug("bankruptcy details: " + json.dumps(application))
    response = requests.put(url, data=json.dumps(application), headers=headers)
    if response.status_code == 200:
        logging.info(format_message("Registration (bank) submitted to CASEWORK_API"))
        data = response.json()
        reg_list = []

        for item in data['new_registrations']:
            reg_list.append(item['number'])
        session['confirmation'] = {'reg_no': reg_list}

    return response