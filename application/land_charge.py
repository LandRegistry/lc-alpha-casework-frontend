def build_lc_inputs(data):
    print('this is the data entered', data)
    if len(data) > 0:
        print('can we get a handle on class of charge?', data['class'])
    print('this is the length', len(data))
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