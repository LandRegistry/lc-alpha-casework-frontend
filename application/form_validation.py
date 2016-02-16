from application import app
import json
import requests

valid_land_charge = ['A', 'B', 'C(I)', 'C(II)', 'C(III)', 'C(IV)', 'D(I)', 'D(II)', 'D(III)', 'E', 'F', 'PA', 'WO',
                     'DA', 'ANN', 'LC']


def validate_land_charge(data):
    errors = []
    if data['class'] != '':
        if data['class'] not in valid_land_charge:
            errors.append('class')
    else:
        errors.append('class')

    # check that any entered counties are valid
    response = requests.get(app.config['CASEWORK_API_URL'] + '/counties')
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

    result = {'class': data['class'], 'error': errors}
    return result
