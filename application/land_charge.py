from application import app
from flask import Response, request, render_template, session, redirect, url_for
import requests
from datetime import datetime
import logging
import json

def build_lc_inputs(data):
    if len(data) == 0:
        result = {'class': '', 'county': [], 'district': '', 'short_description': '', 'estate_owner_ind': '',
                  'estate_owner': {'private': {'forenames': '', 'surname': ''},
                                   'company': '',
                                   'local': {'name': '', 'area': ''},
                                   'complex': '',
                                   'other': ''},
                  'occupation': '',
                  'additional_info': ''}
    else:
        counties = extract_counties(data)

        result = {'class': data['class'], 'county': counties, 'district': data['district'],
                  'short_description': data['short_desc'], 'estate_owner_ind': '',
                  'estate_owner': {'private': {'forenames': data['forename'], 'surname': data['surname']},
                                   'company': data['company'],
                                   'local': {'name': data['loc_auth'], 'area': data['loc_auth_area']},
                                   'complex': data['complex_name'],
                                   'other': data['other_name']},
                  'occupation': data['occupation'],
                  'additional_info': data['addl_info']}

    print(result)

    return result


def extract_counties(data):
    counter = 0
    counties = []
    while True:
        county_counter = "county_" + str(counter)
        if county_counter in data and data[county_counter] != '':
            counties.append(data[county_counter])
        else:
            break
        counter += 1

    return counties


def build_customer_fee_inputs(data):
    print(data)
    customer_fee_details = {'key_number': '244095',
                            'customer_name': 'Mr Conveyancer',
                            'customer_address': '2 New Street',
                            'application_reference': 'reference 11'}

    return customer_fee_details


def submit_lc_registration(reg_data, cust_fee_data):
    url = app.config['CASEWORK_DB_URL'] + '/applications/' + session['regn_no'] + '?action=amend'
    headers = {'Content-Type': 'application/json'}
    response = requests.put(url, json.dumps(application_dict), headers=headers)
    if response.status_code == 200:
        data = response.json()
        reg_list = []
        for item in data['new_registrations']:
            reg_list.append(item)

        session['regn_no'] = reg_list
        delete_from_worklist(session['worklist_id'])
    else:
        err = response.status_code
        logging.error(err)
        return render_template('error.html', error_msg=err), 500