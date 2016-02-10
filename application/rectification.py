

def convert_response_data(api_data):

    result = {'class': get_class_of_charge(api_data),
              'county': api_data['particulars']['counties'],
              'district': api_data['particulars']['district'],
              'short_description': api_data['particulars']['description'],
              'estate_owner': get_estate_owner(api_data['parties'][0]['names'][0]),
              'estate_owner_ind': api_data['parties'][0]['names'][0]['type'],
              'occupation': get_occupation(api_data['parties'][0]),
              'additional_info': get_additional_info(api_data)
              }

    return result


def get_class_of_charge(response):
    charge_class = {
        "C1": "C(I)",
        "C2": "C(II)",
        "C3": "C(III)",
        "C4": "C(IV)",
        "D1": "D(I)",
        "D2": "D(II)",
        "D3": "D(III)"
    }

    if response['class_of_charge'] in charge_class:
        return charge_class.get(response['class_of_charge'])
    else:
        return response['class_of_charge']


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


