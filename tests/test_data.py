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

rectification = dict(forenames='Don', surname='Draper', occupation='Advertising', aliasforename0='Donald',
                     aliassurname0='Draper', aliasforename1='Richard', aliassurname1='Whitman', aliasforename2='Dick',
                     aliassurname2='Draper', address10='34 Main Street', address20='Fake area', address30='Fake Town',
                     county0='Fakeshire', postcode0='FF1 1FF', address11='22 Main Street', address21='Fake Place',
                     address31='Fake City', county1='West Fakeshire', postcode1='FF1 2FF', court='Fake County Court',
                     ref='1 of 1990')

rect_no_addr = dict(forenames='Don', surname='Draper', occupation='Advertising', aliasforename0='Donald',
                    aliassurname0='Draper', aliasforename1='Richard', aliassurname1='Whitman', aliasforename2='Dick',
                    aliassurname2='Draper', court='Fake County Court', ref='1 of 1990')

full_search = dict(fullname0='Cooper Bogan', year_from0='1925', year_to0='2015', area_list='["Lancashire"]',
                   key_no='1234567', customer_name='full search test plc',
                   customer_address='34 new street, new town, devon, pl1 1aa', customer_ref='full search test ref')

full_search_all_counties = dict(fullname0='Cooper Bogan', year_from0='1925', year_to0='2015',
                                key_no='1234567', customer_name='full search test plc',
                                customer_address='34 new street, new town, devon, pl1 1aa',
                                customer_ref='full search test ref', all_counties='True')

banks_search = dict(fullname0='Cooper Bogan', fullname1='Terrence Jones',
                    key_no='1234567', customer_name='full search test plc',
                    customer_address='34 new street, new town, devon, pl1 1aa', customer_ref='full search test ref')