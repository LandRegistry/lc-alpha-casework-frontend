from application import app
from flask import Response, request, render_template, session, redirect, url_for
import requests
from datetime import datetime
import logging
import json


def build_lc_inputs(data):
    if len(data) == 0:
        result = {'class': '', 'county': [], 'district': '', 'short_description': '',
                  'estate_owner_ind': 'privateIndividual',
                  'estate_owner': {'private': {'forenames': '', 'surname': ''},
                                   'company': '',
                                   'local': {'name': '', 'area': ''},
                                   'complex': {"name": '', "number": ''},
                                   'other': ''},
                  'occupation': '',
                  'additional_info': ''}
    else:
        counties = extract_counties(data)

        result = {'class': data['class'], 'county': counties, 'district': data['district'],
                  'short_description': data['short_desc'], 'estate_owner_ind': data['estateOwnerTypes'],
                  'estate_owner': {'private': {'forenames': data['forename'], 'surname': data['surname']},
                                   'company': data['company'],
                                   'local': {'name': data['loc_auth'], 'area': data['loc_auth_area']},
                                   # 'complex': {"name": data['complex_name'], "number": data['complex_number']},
                                   'complex': {"name": '', "number": 0},
                                   'other': data['other_name']},
                  'occupation': data['occupation'],
                  'additional_info': data['addl_info']}

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
    customer_fee_details = {'key_number': '244095',
                            'customer_name': 'Mr Conveyancer',
                            'customer_address': '2 New Street',
                            'application_reference': 'reference 11'}

    return customer_fee_details


def submit_lc_registration(cust_fee_data):
    application = session['application_dict']
    application['application_ref'] = cust_fee_data['application_reference']
    application['key_number'] = cust_fee_data['key_number']
    today = datetime.now().strftime('%Y-%m-%d')
    application['date'] = today
    application['residence_withheld'] = False
    application['date_of_birth'] = "1980-01-01"  # TODO: what are we doing about the DOB??
    application['document_id'] = session['document_id']
    session['register_details']['estate_owner']['estate_owner_ind'] = \
        convert_estate_owner_ind(session['register_details']['estate_owner_ind'])
    application['lc_register_details'] = session['register_details']
    application['lc_register_details']['complex'] = {"name": "", "number": 0}
    application['cust_fee_data'] = cust_fee_data

    url = app.config['CASEWORK_DB_URL'] + '/applications/' + session['worklist_id'] + '?action=complete'
    headers = {'Content-Type': 'application/json'}
    response = requests.put(url, data=json.dumps(application), headers=headers)
    if response.status_code == 200:
        data = response.json()
        reg_list = []
        for item in data['new_registrations']:
            reg_list.append(item)
        session['regn_no'] = reg_list
        return redirect('/confirmation', code=302, Response=None)
    else:
        # error = response.status_code
        # logging.error(error)
        # return render_template('error.html', error_msg=error), 500
        return response.status_code


def convert_estate_owner_ind(data):
    estate_ind = {
        "privateIndividual": "Private individual",
        "limitedCompany": "Company",
        "localAuthority": "Local Authority",
        "complexName": "Complex name",
        "other": "other"
    }

    return estate_ind.get(data)
