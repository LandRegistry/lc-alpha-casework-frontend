from application import app
from application.http import http_get
from flask import session
import json
import requests
import logging
import re

valid_land_charge = ['A', 'B', 'C(I)', 'C(II)', 'C(III)', 'C(IV)', 'D(I)', 'D(II)', 'D(III)', 'E', 'F', 'PA', 'WO',
                     'DA', 'ANN', 'LC']


# Inconsistent and highly specific validation taken from legacy systems, reimplemented here as-is. This is only to
# prevent more free-format data from blowing up the legacy application.
def validateCountyCouncil(data):
    url = "{}/county_council/{}".format(
        app.config['CASEWORK_API_URL'],
        data['loc_auth_area']
    )
    resp = http_get(url)
    if resp.status_code == 404:
        return False

    # Manchester & London have special rules, but the table based check above will cover those
    if re.match(".*(MANCHESTER|LONDON).*", data['loc_auth'], re.IGNORECASE) is not None:
        return True

    # Not London or Manchester
    word_match = re.match(".*(COUNTY COUNCIL|COUNCIL OF THE COUNTY OF|ADMINISTRATIVE|CYNGOR).*", data['loc_auth'], re.IGNORECASE)
    if word_match is None:
        return False

    return True


def validateRuralCouncil(data):
    word_match = re.match(".*(RURAL DISTRICT|RDC|R D C).*", data['loc_auth'], re.IGNORECASE)
    if word_match is None:
        return False

    return True


def validateParishCouncil(data):
    word_match = re.match(".*(PARISH|COMMUNITY|TOWN).*", data['loc_auth'], re.IGNORECASE)
    if word_match is None:
        return False

    return True


def validateOtherCouncil(data):
    word_match = re.match(".*(BOROUGH|BWRDEISTREF|CITY|DINAS|URBAN|UDC|U D C|METROPOLITAN|DISTRICT).*", data['loc_auth'], re.IGNORECASE)
    if word_match is None:
        return False

    word_match = re.match(".*(CYNGOR|COUNTY COUNCIL|COUNCIL FOR THE COUNTY OF|ADMINISTRATIVE|RURAL DISTRICT|RDC|R D C|PARISH|COMMUNITY|TOWN|DEVELOPMENT|CC|C C).*", data['loc_auth'], re.IGNORECASE)
    if word_match is not None:
        return False

    return True


def validateDevCorp(data):
    word_match = re.match(".*(DEVELOPMENT).*", data['other_name'], re.IGNORECASE)
    if word_match is None:
        return False

    return True


#([('loc_auth', ''), ('loc_auth_area', ''), ('county_0', 'Denbighshire'), ('complex_name', ''), ('continue', 'Continue'),
# ('surname', ''), ('district', 's'), ('priority_notice', ''), ('other_name', ''), ('addl_info', ''), ('short_desc', 's'),
# ('estateOwnerTypes', 'privateIndividual'), ('company', ''), ('complex_number', '0'), ('forename', ''), ('occupation', ''),
# ('class', 'F')])



def validate_land_charge(data):
    errors = []
    logging.info(data)

    if data['class'] != '':
        if data['class'] not in valid_land_charge:
            errors.append('class')
    else:
        errors.append('class')

    # check that any entered counties are valid
    response = requests.get(app.config['CASEWORK_API_URL'] + '/counties', headers={'X-Transaction-ID': session['transaction_id']})
    counties = json.loads(response.content.decode('utf-8'))
    counties_upper = [county.upper() for county in counties]
    cntr = 0
    while 'county_' + str(cntr) in data:
        if data['county_' + str(cntr)].upper() not in counties_upper:
            errors.append('county')
        cntr += 1

    if data['district'] == '':
        errors.append('district')

    if data['short_desc'] == '':
        errors.append('short_desc')

    if data['forename'] == '' and data['surname'] == '' and data['company'] == '' \
            and data['loc_auth'] == '' and data['complex_name'] == '' and data['other_name'] == '':
        errors.append('estate_owner')
    elif data['loc_auth'] != '' and data['loc_auth_area'] == '':
        errors.append('estate_owner')

    eot = data['estateOwnerTypes']
    if eot == 'countyCouncil':
        if not validateCountyCouncil(data):
            errors.append('estate_owner')
    if eot == 'ruralCouncil':
        if not validateRuralCouncil(data):
            errors.append('estate_owner')
    if eot == 'parishCouncil':
        if not validateParishCouncil(data):
            errors.append('estate_owner')
    if eot == 'otherCouncil':
        if not validateOtherCouncil(data):
            errors.append('estate_owner')
    if eot == 'developmentCorporation':
        if not validateDevCorp(data):
            errors.append('estate_owner')

    result = {'class': data['class'], 'error': errors}
    return result
