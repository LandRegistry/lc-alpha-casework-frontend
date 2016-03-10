from application import app
from application.logformat import format_message
from flask import Response, request, render_template, session, redirect, url_for
import requests
from datetime import datetime
import logging
import json


def process_search_criteria(data, search_type):
    logging.debug('process search data')
    counties = []
    parameters = {
        'counties': counties,
        'search_type': "banks" if search_type == 'search_bank' else 'full',
        'search_items': []
    }
    counter = 1

    while True:

        name_type = 'nameType_{}'.format(counter)
        if name_type not in data:
            break

        name_extracted = False

        if data[name_type] == 'privateIndividual' \
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
                'name_type': 'Limited Company',
                'name': {
                    'company_name': data[company]
                }
            }
            name_extracted = True

        elif data[name_type] == 'countyCouncil' \
                and data['loc_auth_{}'.format(counter)] != '' \
                and data['loc_auth_area_{}'.format(counter)] != '':

            loc_auth = 'loc_auth_{}'.format(counter)
            loc_auth_area = 'loc_auth_area_{}'.format(counter)
            search_item = {
                'name_type': 'County Council',
                'name': {
                    'local_authority_name': data[loc_auth],
                    'local_authority_area': data[loc_auth_area]
                }
            }
            name_extracted = True

        elif data[name_type] == 'ruralCouncil' \
                and data['loc_auth_{}'.format(counter)] != '' \
                and data['loc_auth_area_{}'.format(counter)] != '':

            loc_auth = 'loc_auth_{}'.format(counter)
            loc_auth_area = 'loc_auth_area_{}'.format(counter)
            search_item = {
                'name_type': 'Rural Council',
                'name': {
                    'local_authority_name': data[loc_auth],
                    'local_authority_area': data[loc_auth_area]
                }
            }
            name_extracted = True

        elif data[name_type] == 'parishCouncil' \
                and data['loc_auth_{}'.format(counter)] != '' \
                and data['loc_auth_area_{}'.format(counter)] != '':

            loc_auth = 'loc_auth_{}'.format(counter)
            loc_auth_area = 'loc_auth_area_{}'.format(counter)
            search_item = {
                'name_type': 'Parish Council',
                'name': {
                    'local_authority_name': data[loc_auth],
                    'local_authority_area': data[loc_auth_area]
                }
            }
            name_extracted = True

        elif data[name_type] == 'otherCouncil' \
                and data['loc_auth_{}'.format(counter)] != '' \
                and data['loc_auth_area_{}'.format(counter)] != '':

            loc_auth = 'loc_auth_{}'.format(counter)
            loc_auth_area = 'loc_auth_area_{}'.format(counter)
            search_item = {
                'name_type': 'Other Council',
                'name': {
                    'local_authority_name': data[loc_auth],
                    'local_authority_area': data[loc_auth_area]
                }
            }
            name_extracted = True

        elif data[name_type] == 'codedName' and data['other_name_{}'.format(counter)] != '':
            other_name = 'other_name_{}'.format(counter)
            search_item = {
                'name_type': 'Coded Name',
                'name': {
                    'other_name': data[other_name]
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
            headers = {'Content-Type': 'application/json', 'X-Transaction-ID': session['transaction_id']}
            comp_name = {
                'name': data[complex_name],
                'number': int(data[complex_number])
            }
            response = requests.post(url, data=json.dumps(comp_name), headers=headers)
            logging.info(format_message('POST {} -- {}'.format(url, response)))
            result = response.json()

            for item in result:
                search_item['name']['complex_variations'].append({'name': item['name'],
                                                                  'number': int(item['number'])})
            name_extracted = True

        elif data[name_type] == 'developmentCorporation' and data['other_name_{}'.format(counter)] != '':
            # name_type is other
            other_name = 'other_name_{}'.format(counter)
            search_item = {
                'name_type': 'Development Corporation',
                'name': {
                    'other': data[other_name]
                }
            }
            name_extracted = True

        elif data[name_type] == 'other' and data['other_name_{}'.format(counter)] != '':
            # name_type is other
            other_name = 'other_name_{}'.format(counter)
            search_item = {
                'name_type': 'Other',
                'name': {
                    'other_name': data[other_name]
                }
            }
            name_extracted = True

        if search_type == 'search_full' and name_extracted:
            logging.debug('Getting year stuff')
            search_item['year_to'] = int(data['year_to_{}'.format(counter)])
            search_item['year_from'] = int(data['year_from_{}'.format(counter)])

        if name_extracted:
            parameters['search_items'].append(search_item)

        counter += 1

    result = {}
    if search_type == 'search_full':
        if 'all_counties' in data and data['all_counties'] == 'yes':
            result['county'] = ['ALL']
        else:
            add_counties(result, data)
    else:
        result['county'] = []

    parameters['counties'] = result['county']
    session['application_dict']['search_criteria'] = parameters
    return


def add_counties(result, data):
    logging.debug('add counties')
    logging.debug(data)
    counter = 0
    counties = []
    while True:
        county_counter = "county_" + str(counter)
        if county_counter in data and data[county_counter] != '':
            counties.append(data[county_counter])
            logging.debug('Add county ' + data[county_counter])
        else:
            break
        counter += 1

    result['county'] = counties
