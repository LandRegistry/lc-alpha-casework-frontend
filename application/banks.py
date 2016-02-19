from application import app
from flask import Response, request, render_template, session, redirect, url_for
import requests
from datetime import datetime
import logging
import json


def get_debtor_details(data):
    counter = 1
    names = []
    while True:
        forenames = "forenames_" + str(counter)
        surname = "surname_" + str(counter)
        if surname in data and data[surname] != ' ':
            private = {'forenames': data[forenames].split(),
                       'surname': data[surname]}
            names.append({'type': 'Private Individual',
                          'private': private})
        else:
            break
        counter += 1

    counter = 1
    addresses = []
    # TODO: what if the residence is witheld????
    while True:
        addr1_counter = "add_" + str(counter) + "_line1"
        addr2_counter = "add_" + str(counter) + "_line2"
        addr3_counter = "add_" + str(counter) + "_line3"
        addr4_counter = "add_" + str(counter) + "_line4"
        addr5_counter = "add_" + str(counter) + "_line5"
        county_counter = "county_" + str(counter)
        postcode_counter = "postcode_" + str(counter)
        address = {'address_lines': []}
        if addr1_counter in data and data[addr1_counter] != '':
            address['address_lines'].append(data[addr1_counter])
        else:
            break
        if addr2_counter in data and data[addr2_counter] != '':
            address['address_lines'].append(data[addr2_counter])
        if addr3_counter in data and data[addr3_counter] != '':
            address['address_lines'].append(data[addr3_counter])
        if addr4_counter in data and data[addr4_counter] != '':
            address['address_lines'].append(data[addr4_counter])
        if addr5_counter in data and data[addr5_counter] != '':
            address['address_lines'].append(data[addr5_counter])

        address['county'] = data[county_counter]
        address['postcode'] = data[postcode_counter]
        address['type'] = 'Residence'
        address['address_string'] = ' '.join(address['address_lines']) + ' ' + data[county_counter] + ' ' + \
                                    data[postcode_counter]
        addresses.append(address)
        counter += 1

    parties = [
        {
            'type': 'Debtor',
            'names': names,
            'addresses': addresses,
            'occupation': data['occupation'],
            'residence_witheld': False
        }
    ]

    return parties