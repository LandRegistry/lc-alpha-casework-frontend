data_no_residence = dict(county='', postcode='', application='{"forename": "John"}')

address = dict(address1='34 Haden Close', address2='Little Horn', address3='Bay of Islands', county='North Shore',
               postcode='AA1 1AA', application='{"debtor_name": {"forename": ["John"], "surname": "Smithers"}, '
                                               '"occupation": "Bodger", "residence": []}')

address_2_lines = dict(address1='34 Haden Close', address2='Little Horn', county='North Shore', postcode='AA1 1AA',
                       application='{"debtor_name": {"forename": ["John"], "surname": "Smithers"}, '
                                   '"occupation": "Bodger", "residence": []}')

additional_address = dict(address1='34 Haden Close', address2='Little Horn', county='North Shore', postcode='AA1 1AA',
                          application='{"debtor_name": {"forename": ["John"], "surname": "Smithers"}, '
                                      '"occupation": "Bodger", "residence": []}',
                          add_address='Add Address')

residence = dict(address1='34 Haden Close', address2='Little Horn', address3='', county='North Shore', postcode='AA1 1AA',
                 application='{"debtor_name": {"forename": ["John"], "surname": "Smithers"}, "occupation": "Bodger",'
                             '"residence": [{"address_lines": ["34 Main Street", "plymouth", "Devon"], '
                             '"postcode": "PL8 8EE"}]}')

process_pab = dict(application='{"forename": "John"}', nature='PA(B)', court='', court_ref='')

process_wob = dict(application='{"forename": "John"}', nature='WO(B)', court='', court_ref='')

process_court = dict(nature='PA(B)', court='Plymouth', court_ref='1 of 2015',
                     application='{"debtor_name": {"forename": ["John"], "surname": "Smithers"}, "occupation": "Bodge",'
                                 '"residence": [{"address_lines": ["34 Main Street", "plymouth", "Devon"], '
                                 '"postcode": "PL8 8EE"}]}')

multi_name = dict(nature='PA(B)', court='Plymouth', court_ref='1 of 2015',
                  application='{"debtor_name": {"forename": ["John"], "surname": "Smithers"}, "occupation": "Bodger",'
                              '"residence": [{"address_lines": ["34 Main Street", "plymouth", "Devon"], '
                              '"postcode": "PL8 8EE"}], "debtor_alternative_name": [{"forename": ["Jonathon"], '
                              '"surname": "Smithy"}')