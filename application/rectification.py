from application import app
from application.logformat import format_message
from application.headers import get_headers
from flask import Response, session
import requests
import logging
import json

def convert_response_data(api_data):

    result = {'class': convert_class_of_charge(api_data['class_of_charge']),
              'county': api_data['particulars']['counties'],
              'district': api_data['particulars']['district'],
              'short_description': api_data['particulars']['description'],
              'estate_owner': get_estate_owner(api_data['parties'][0]['names'][0]),
              'estate_owner_ind': api_data['parties'][0]['names'][0]['type'],
              'occupation': get_occupation(api_data['parties'][0]),
              'additional_info': get_additional_info(api_data)
              }

    return result


def convert_class_of_charge(type):
    charge_class = {
        "C1": "C(I)", "C2": "C(II)", "C3": "C(III)", "C4": "C(IV)",
        "D1": "D(I)", "D2": "D(II)", "D3": "D(III)",
        "C(I)": "C1", "C(II)": "C2", "C(III)": "C3", "C(IV)": "C4",
        "D(I)": "D1", "D(II)": "D2", "D(III)": "D3"
    }

    if type in charge_class:
        return charge_class.get(type)
    else:
        return type


def get_additional_info(response):
    info = ''
    if 'additional_information' in response:
        info = response['additional_information']

    return info


def get_occupation(party):
    occupation = ''
    if 'occupation' in party:
        occupation = party['occupation']

    return occupation


def get_estate_owner(name):
    name_for_screen = {'private': {'forenames': [''], 'surname': ''},
                       'company': '',
                       'local': {'name': '', 'area': ''},
                       'complex': {"name": '', "number": ''},
                       'other': ''}

    if name['type'] == 'Private Individual':
        name_for_screen['private'] = {'forenames': name['private']['forenames'], 'surname': name['private']['surname']}
    elif name['type'] == 'Limited Company':
        name_for_screen['company'] = name['company']
    elif name['type'] == 'County Council':
        name_for_screen['local'] = {'name': name['local']['name'], 'area': name['local']['area']}
    elif name['type'] == 'Parish Council':
        name_for_screen['local'] = {'name': name['local']['name'], 'area': name['local']['area']}
    elif name['type'] == 'Other Council':
        name_for_screen['local'] = {'name': name['local']['name'], 'area': name['local']['area']}
    elif name['type'] == 'Development Corporation':
        name_for_screen['other'] = name['other']
    elif name['type'] == 'Complex Name':
        name_for_screen['complex'] = {"name": name['complex']['name'], "number": name['complex']['number']}
    elif name['type'] == 'Other':
        name_for_screen['company'] = name['company']

    return name_for_screen


def get_party_name(data):

        party = {
            "type": "Estate Owner",
            "names": []}

        name = {"type": data['estate_owner_ind']}

        if name['type'] == 'Private Individual':
            name['private'] = {
                'forenames': data['estate_owner']['private']['forenames'],
                'surname': data['estate_owner']['private']['surname']}
        elif name['type'] == "County Council" or name['type'] == "Parish Council" or name['type'] == "Other Council":
            name['local'] = {
                'name': data['estate_owner']['local']['name'],
                'area': data['estate_owner']['local']['area']}
        elif name['type'] == "Development Corporation" or name['type'] == "Other":
            name['other'] = data['estate_owner']['other']
        elif name['type'] == "Limited Company":
            name['company'] = data['estate_owner']['company']
        elif name['type'] == "Complex Name":
            name['complex'] = {
                'name': data['estate_owner']['complex']['name'],
                'number': data['estate_owner']['complex']['number']}
        else:
            raise RuntimeError("Unexpected name type: {}".format(name['type']))

        party['names'].append(name)
        party['occupation'] = data['occupation']

        return party


def submit_lc_rectification(form):

    rect_details = (session['rectification_details'])
    cust_address = form['customer_address'].replace("\r\n", ", ").strip()
    application = {'update_registration': {'type': 'Rectification'},
                   'applicant': {
                       'key_number': form['key_number'],
                       'name': form['customer_name'],
                       'address': cust_address,
                       'reference': form['customer_ref']},
                   'parties': [get_party_name(rect_details)],
                   'particulars': {'counties': rect_details['county'], 'district': rect_details['district'],
                                   'description': rect_details['short_description']},
                   'class_of_charge': convert_class_of_charge(rect_details['class']),
                   'regn_no': session['regn_no'],
                   'registration': {'date': session['reg_date']},
                   'document_id': session['document_id'],
                   'fee_details': {'type': form['payment'],
                                   'fee_factor': 1,
                                   'delivery': session['application_dict']['delivery_method']}
                   }

    url = app.config['CASEWORK_API_URL'] + '/applications/' + session['worklist_id'] + '?action=rectify'
    headers = get_headers({'Content-Type': 'application/json'})
    response = requests.put(url, data=json.dumps(application), headers=headers)
    if response.status_code == 200:
        logging.info(format_message("Rectification submitted to CASEWORK_API"))
        data = response.json()

        if 'new_registrations' in data:
            reg_list = []
            for item in data['new_registrations']:
                reg_list.append(item['number'])
            session['confirmation'] = {'reg_no': reg_list}
        else:
            session['confirmation'] = {'reg_no': []}

    return Response(status=200)
