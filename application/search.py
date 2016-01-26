from application import app
from flask import Response, request, render_template, session, redirect, url_for
import requests
from datetime import datetime
from application.land_charge import add_counties
import logging
import json


def process_search_criteria(data, search_type):
    counties = []
    parameters = {
        'counties': counties,
        'search_type': "banks" if search_type == 'search_bank' else 'full',
        'search_items': []
    }
    counter = 1

    print(data)
    while True:

        name_type = 'nameType_{}'.format(counter)
        if name_type not in data:
            break

        name_extracted = False

        if data[name_type] == 'privateIndividual' \
                and data['forename_{}'.format(counter)] != '' \
                and data['surname_{}'.format(counter)] != '':

            forename = 'forename_{}'.format(counter)
            surname = 'surname_{}'.format(counter)
            search_item = {
                'name_type': 'Private Individual',
                'name': {
                    'forenames': data[forename],
                    'surname': data[surname]
                }
            }
            name_extracted = True

        elif data[name_type] == 'limitedCompany' \
                and data['company_{}'.format(counter)] != '':

            company = 'company_{}'.format(counter)
            search_item = {
                'name_type': 'Company',
                'name': {
                    'company_name': data[company]
                }
            }
            name_extracted = True

        elif data[name_type] == 'localAuthority' \
                and data['loc_auth_{}'.format(counter)] != '' \
                and data['loc_auth_area_{}'.format(counter)] != '':

            loc_auth = 'loc_auth_{}'.format(counter)
            loc_auth_area = 'loc_auth_area_{}'.format(counter)
            search_item = {
                'name_type': 'Local Authority',
                'name': {
                    'local_authority_name': data[loc_auth],
                    'local_authority_area': data[loc_auth_area]
                }
            }
            name_extracted = True

        elif data[name_type] == 'complexName' \
                and data['complex_name_{}'.format(counter)] != '' \
                and data['complex_number_{}'.format(counter)] != '':

            complex_name = 'complex_name_{}'.format(counter)
            complex_number = 'complex_number_{}'.format(counter)
            search_item = {
                'name_type': 'Complex',
                'name': {
                    'complex_name': data[complex_name],
                    'complex_number': int(data[complex_number]),
                    'complex_variations': []
                }
            }
            url = app.config['CASEWORK_API_URL'] + '/complex_names/search'
            headers = {'Content-Type': 'application/json'}
            comp_name = {
                'name': data[complex_name]
            }
            response = requests.post(url, data=json.dumps(comp_name), headers=headers)
            logging.info('POST {} -- {}'.format(url, response))
            result = response.json()

            for item in result:
                search_item['name']['complex_variations'].append({'complex_name': item['name'],
                                                                  'complex_number': int(item['number'])})
            name_extracted = True

        elif data[name_type] == 'other' and data['other_name_{}'.format(counter)] != '':
            # name_type is other
            other_name = 'other_name_{}'.format(counter)
            search_item = {
                'name_type': 'Other',
                'name': {
                    'company_name': data[other_name]
                }
            }
            name_extracted = True

        if search_type == 'search_full' and name_extracted:
            logging.info('Getting year stuff')
            search_item['year_to'] = int(data['year_to_{}'.format(counter)])
            search_item['year_from'] = int(data['year_from_{}'.format(counter)])

        if name_extracted:
            parameters['search_items'].append(search_item)

        counter += 1

    result = {}
    if search_type == 'search_full':
        if 'all_counties' in data and data['all_counties'] == 'yes':
            result['county'] = ['All']
        else:
            add_counties(result, data)
    else:
        result['county'] = None

    parameters['counties'] = result['county']
    session['application_dict']['search_criteria'] = parameters
    return