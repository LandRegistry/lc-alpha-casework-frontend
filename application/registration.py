

def convert_response_data(api_data):

    result = {'class': class_of_charge(api_data['class_of_charge']),
              'county': api_data['particulars']['counties'],
              'district': api_data['particulars']['district'],
              'short_description': api_data['particulars']['description'],
              'estate_owner': estate_owner(api_data['parties'][0]['names'][0])
              }

    return result

# {
#     'registration':{
#         'date':'2014-08-01',
#         'number':1003
#     },
#     'parties':[
#         {
#             'names':[
#                 {
#                     'private':{
#                         'forenames':[
#                             'Jo',
#                             'John'
#                         ],
#                         'surname':'Johnson'
#                     },
#                     'type':'Private Individual'
#                 }
#             ],
#             'type':'Estate Owner'
#         }
#     ],
#     'particulars':{
#         'counties':[
#             'Devon'
#         ],
#         'district':'South Hams',
#         'description':'1 The Lane, Some Village'
#     },
#     'class_of_charge':'C1',
#     'revealed':True,
#     'status':'current'
# }

def class_of_charge(type):

        charge_class = {
            "C1": "C(I)",
            "C2": "C(II)",
            "C3": "C(III)",
            "C4": "C(IV)",
            "D1": "D(I)",
            "D2": "D(II)",
            "D3": "D(III)"
        }

        if charge_class.get(type) is not None:
            return charge_class.get(type)
        else:
            return type

def estate_owner(name):
    if name['type'] == 'Private Individual':
        return {'private': {'forenames': name['private']['forenames'], 'surname': name['private']['surname']},
                         'company': '',
                         'local': {'name': '', 'area': ''},
                         'complex': {"name": '', "number": ''},
                         'other': ''}
    elif name['type'] == 'Limited Company':
        return {'private': {'forenames': [''], 'surname': ''},
                'company': '',
                'local': {'name': '', 'area': ''},
                'complex': {"name": '', "number": ''},
                'other': ''}

