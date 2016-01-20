from application import app
from flask import Response, request, render_template, session, redirect, url_for
import requests
from datetime import datetime
import logging
import json


def build_lc_inputs(data):
    type_of_form = session['application_dict']['form']
    result = {'class': 'C(I)', 'county': [], 'district': '', 'short_description': '',
              'estate_owner_ind': 'privateIndividual',
              'estate_owner': {'private': {'forenames': '', 'surname': ''},
                               'company': '',
                               'local': {'name': '', 'area': ''},
                               'complex': {"name": '', "number": ''},
                               'other': ''},
              'occupation': '',
              'additional_info': ''}

    if len(data) > 0:
        if type_of_form == 'K1':
            result['class'] = data['class']
            result['district'] = data['district']
            result['short_description'] = data['short_desc']
            result['estate_owner_ind'] = data['estateOwnerTypes']
            result['occupation'] = data['occupation']
            result['additional_info'] = data['addl_info']

            add_counties(result, data)

            add_estate_owner_details(result, data)

    return result


def add_estate_owner_details(result, data):
    result['estate_owner']['private']['forenames'] = data['forename']
    result['estate_owner']['private']['surname'] = data['surname']

    result['estate_owner']['company'] = data['company']
    result['estate_owner']['local']['name'] = data['loc_auth']
    result['estate_owner']['local']['area'] = data['loc_auth_area']
    result['estate_owner']['complex']['name'] = data['complex_name']

    if data['complex_number'] == "":
        result['estate_owner']['complex']['number'] = 0
    else:
        result['estate_owner']['complex']['number'] = int(data['complex_number'])

    result['estate_owner']['other'] = data['other_name']


def add_counties(result, data):
    counter = 0
    counties = []
    while True:
        county_counter = "county_" + str(counter)
        if county_counter in data and data[county_counter] != '':
            counties.append(data[county_counter])
        else:
            break
        counter += 1

    result['county'] = counties


def build_customer_fee_inputs(data):
    customer_fee_details = {'key_number': '244095',
                            'customer_name': 'Mr Conveyancer',
                            'customer_address': '2 New Street',
                            'application_reference': 'reference 11'}

    return customer_fee_details


def submit_lc_registration(cust_fee_data):
    application = session['application_dict']
    application['application_type'] = convert_application_type(session['application_type'])
    application['application_ref'] = cust_fee_data['application_reference']
    application['key_number'] = cust_fee_data['key_number']
    application['customer_name'] = cust_fee_data['customer_name']
    application['customer_address'] = cust_fee_data['customer_address']
    today = datetime.now().strftime('%Y-%m-%d')
    application['date'] = today
    application['residence_withheld'] = False
    application['date_of_birth'] = "1980-01-01"  # TODO: what are we doing about the DOB??
    application['document_id'] = session['document_id']
    session['register_details']['estate_owner']['estate_owner_ind'] = \
        convert_estate_owner_ind(session['register_details']['estate_owner_ind'])
    application['lc_register_details'] = session['register_details']

    url = app.config['CASEWORK_API_URL'] + '/applications/' + session['worklist_id'] + '?action=complete'
    headers = {'Content-Type': 'application/json'}
    response = requests.put(url, data=json.dumps(application), headers=headers)
    if response.status_code == 200:
        logging.info("200 response here")
        data = response.json()
        reg_list = []
        for item in data['new_registrations']:
            reg_list.append(item)
        session['regn_no'] = reg_list
        #return redirect('/confirmation', code=302, Response=None)
        return response.status_code
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


def convert_application_type(type):
    app_type = {
        "lc_regn": "New Registration",
        "banks": "New Registration",
        "cancel": "Cancellation",
        "amend": "Amendment",
        "oc": "Official Copy",
        "search": "Search"
    }

    return app_type.get(type)
