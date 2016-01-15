# valid_land_charge = ['A', 'B', 'C1', 'C2', 'C3', 'C4', 'D1', 'D2', 'D3', 'E', 'F', 'PA', 'WO', 'DA', 'ANN', 'LC']

valid_land_charge = ['A', 'B', 'C(I)', 'C(II)', 'C(III)', 'C(IV)', 'D(I)', 'D(II)', 'D(III)', 'E', 'F', 'PA', 'WO',
                     'DA', 'ANN', 'LC']


def convert_class(class_of_charge):
    charge = {
        "C1": "C(I)",
        "C2": "C(II)",
        "C3": "C(III)",
        "C4": "C(IV)",
        "D1": "D(I)",
        "D2": "D(II)",
        "D3": "D(III)",
        "PAB": "PA(B)",
        "WOB": "WO(B)"
    }
    if class_of_charge in charge:
        return charge.get(class_of_charge)
    else:
        return class_of_charge


def validate_land_charge(data):
    curr_class = ''
    errors = []
    if data['class'] != '':
        curr_class = convert_class(data['class'])
        if curr_class not in valid_land_charge:
            errors.append('class')
    else:
        errors.append('class')

    if data['county_0'] == '':
        errors.append('county')

    if data['district'] == '':
        errors.append('district')

    if data['short_desc'] == '':
        errors.append('short_desc')

    if data['forename'] == '' and data['surname'] == '' and data['company'] == '' \
            and data['loc_auth'] == '' """and data['complex_name'] == ''""" and data['other_name'] == '':
        errors.append('estate_owner')
    elif data['loc_auth'] != '' and data['loc_auth_area'] == '':
        errors.append('estate_owner')

    result = {'class': curr_class, 'error': errors}
    return result








