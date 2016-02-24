# TODO: This route should be deleted once we are happy that the code in it is redundant Alpha code

# Banks reg routes

# TODO: can process_banks_name be remove

"""
@app.route('/process_banks_name', methods=["POST"])
def process_banks_name():
    name = {"debtor_names": []}

    if 'comp_number' in request.form:
        comp_name = {"name": request.form['comp_name'], "number": int(request.form['comp_number'])}
        name['complex'] = comp_name
    elif 'complex_number' in request.form:
        comp_name = {"name": request.form['complex_name'], "number": int(request.form['complex_number'])}
        name['complex'] = comp_name
    else:
        name['debtor_names'].append({
            'forenames': request.form['forename'].split(),
            'surname': request.form['surname']
        })

        name['occupation'] = request.form['occupation']

        forename_var = "aliasforename"
        surname_var = "aliassurname"
        counter = 0
        while True:
            forename_counter = forename_var + str(counter)
            surname_counter = surname_var + str(counter)
            try:
                alt_forenames = request.form[forename_counter]
                alt_surname = request.form[surname_counter]
            except KeyError:
                break

            if alt_forenames != '' and alt_surname != '':
                name['debtor_names'].append({
                    'forenames': alt_forenames.split(),
                    'surname': alt_surname
                })
            counter += 1

    name['application_type'] = session['application_dict']['form']
    set_session_variables({'application_dict': name})

    return redirect('/address_details', code=302, Response=None) """


# TODO: can /complex_name be removed?
"""
@app.route('/complex_name', methods=['GET'])
def complex_name():
    logging.info('Entering complex name')
    application_type = session['application_type']
    application = session['application_dict']

    return render_template('complex_name_reg.html', images=session['images'], application=application,
                           application_type=application_type, current_page=0)"""

# TODO: should /complex_retrieve be removed?
"""
@app.route('/complex_retrieve', methods=['POST'])
def complex_name_retrieve():  # TODO: remove this (card added to backlog)
    logging.info('Entering complex name retrieval')
    logging.error('METHOD DEPRECTATED -- THIS SHOULD NOT BE USED')
    complex_search = {"name": request.form['complex_name']}

    url = app.config['LEGACY_URL'] + '/complex_names/search'
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(complex_search), headers=headers)

    if response.status_code == 200 or response.status_code == 404:
        data = response.json()

        return render_template('complex_name_select.html', images=session['images'],
                               application=session['application_type'], application_type=session['application_type'],
                               current_page=0, complex=data, orig_name=complex_search['name'])
    else:
        error = response.status_code
        logging.error(error)
        return render_template('error.html', error_msg=error), 500"""

# TODO: should address_details be removed?
"""
@app.route('/address_details', methods=["GET"])
def address_details():
    return render_template('address.html', images=session['images'], current_page=0) """

# TODO: should /address be removed?
"""
@app.route('/address', methods=['POST'])
def application_step_2():
    application = session['application_dict']
    if 'residence' not in application:
        application['residence'] = []

    counter = 0
    while True:
        addr1_counter = "add_" + str(counter) + "_line1"
        addr2_counter = "add_" + str(counter) + "_line2"
        addr3_counter = "add_" + str(counter) + "_line3"
        county_counter = "add_" + str(counter) + "_county"
        postcode_counter = "add_" + str(counter) + "_postcode"
        address = {'address_lines': []}
        if addr1_counter in request.form and request.form[addr1_counter] != '':
            address['address_lines'].append(request.form[addr1_counter])
        else:
            break
        if addr2_counter in request.form and request.form[addr2_counter] != '':
            address['address_lines'].append(request.form[addr2_counter])
        if addr3_counter in request.form and request.form[addr3_counter] != '':
            address['address_lines'].append(request.form[addr3_counter])

        address['county'] = request.form[county_counter]
        address['postcode'] = request.form[postcode_counter]
        application['residence'].append(address)
        counter += 1

    return redirect('/court_details', code=302, Response=None) """

# TODO: shoulld /court_details be removed?
"""
@app.route('/court_details', methods=['GET'])
def court_details():
    return render_template('banks_order.html', images=session['images'], current_page=0,
                           charge=session['application_dict']['form'])"""


# TODO: should /verify_registration be removed?
"""
@app.route('/verify_registration', methods=['GET'])
def verify_registration():
    return render_template('regn_verify.html', images=session['images'], current_page=0,
                           data=session['application_dict']) """


# TODO: should /process_registration be removed?
"""
@app.route('/process_registration', methods=['POST'])
def process_registration():
    application = session['application_dict']
    application["application_ref"] = " "  # TODO: do we need to capture the customer reference
    today = datetime.now().strftime('%Y-%m-%d')
    application["date"] = today
    application["residence_withheld"] = False
    application['date_of_birth'] = "1980-01-01"  # TODO: what are we doing about the DOB??
    application["document_id"] = session['document_id']

    url = app.config['CASEWORK_API_URL'] + '/applications/' + session['worklist_id'] + '?action=complete'
    headers = {'Content-Type': 'application/json'}
    response = requests.put(url, data=json.dumps(application), headers=headers)
    if response.status_code == 200:
        data = response.json()
        reg_list = []
        for item in data['new_registrations']:
            reg_list.append(item['number'])
        session['confirmation'] = {'reg_no': reg_list}
        return redirect('/get_list?appn=bank_regn', code=302, Response=None)
    else:
        error = response.status_code
        logging.error(error)
        return render_template('error.html', error_msg=error), 500 """


# ==== search routes =======
# TODO: should /search_result be removed?
"""
@app.route('/search_result', methods=['GET'])
def search_result():

    display = []
    for result in session['search_result']:
        for key, value in result.items():
            if len(value) == 0:
                display.append({
                    'name': key,
                    'result': 'No Match'
                })
            else:
                display.append({
                    'name': key,
                    'result': 'Match Found'
                })

    print('---------')
    print(session['search_data'])
    print('search_result is ', session['search_result'])
    return render_template('search_result.html', display=display, results=session['search_result'],
                           search_data=session['search_data']) """

# ===== amend routes ==========
# TODO: should /search_result be removed?
"""
@app.route('/amend_name', methods=["GET"])
def show_name():
    return render_template('regn_name.html', application_type=session['application_type'],
                           data=session[''], images=session['images'], current_page=0)"""


# TODO: should /search_result be removed?
"""
@app.route('/remove_alias_name/<int:name>', methods=["GET"])
def remove_alias_name(name):
    # del session['application_dict']['debtor_alternative_name'][name]
    del session['application_dict']['debtor_names'][name]
    session['data_amended'] = 'true'

    return redirect('/amend_name', code=302, Response=None) """


# TODO: should /search_result be removed?
"""
@app.route('/update_name', methods=["POST"])
def update_name_details():
    application_dict = session['application_dict']

    forenames = request.form['forenames'].strip()
    surname = request.form['surname'].strip()
    occupation = request.form['occupation'].strip()

    new_debtor_name = {
        'forenames': forenames.split(),
        'surname': surname
    }

    alt_name = {"forenames": [],
                "surname": ""
                }

    application_dict['debtor_alternative_name'] = []
    forename_var = "aliasforename"
    surname_var = "aliassurname"
    counter = 0
    while True:
        forename_counter = forename_var + str(counter)
        surname_counter = surname_var + str(counter)
        try:
            alt_forenames = request.form[forename_counter]
            alt_surname = request.form[surname_counter]
        except KeyError:
            break

        for i in alt_forenames.split():
            alt_name['forenames'].append(i)

        alt_name['surname'] = alt_surname
        if alt_forenames != '' and alt_surname != '':
            application_dict['debtor_alternative_name'].append(alt_name)

        alt_name = {"forenames": [], "surname": ""}
        counter += 1

    application_dict['debtor_name'] = new_debtor_name
    application_dict['debtor_names'] = []
    application_dict['debtor_names'].append(new_debtor_name)
    for name in application_dict['debtor_alternative_name']:
        application_dict['debtor_names'].append(name)
    application_dict['occupation'] = occupation
    session['data_amended'] = 'true'

    if session['application_type'] == 'bank_regn':
        return redirect('/verify_registration', code=302, Response=None)
    else:
        return redirect('/process_application/' + session['application_type'], code=302, Response=None) """

# TODO: should /search_result be removed?
"""
@app.route('/amend_address', methods=["GET"])
def show_address():
    return render_template('regn_address.html', application_type=session['application_type'],
                           data=session['application_dict'], images=session['images'], current_page=0,
                           focus_on_address=len(session['application_dict']['residence'])) """


# TODO: should /search_result be removed?
"""
@app.route('/update_address', methods=["POST"])
def update_address_details():
    application_dict = session['application_dict']
    amended_addresses = []
    address_no = 1

    # update dictionary with any address amendments
    while 'address_{:s}'.format(str(address_no)) in request.form:

        address = {'address_lines': []}
        address['address_lines'].append(request.form['add_{:s}_line1'.format(str(address_no))])
        address['address_lines'].append(request.form['add_{:s}_line2'.format(str(address_no))])
        address['address_lines'].append(request.form['add_{:s}_line3'.format(str(address_no))])
        address['county'] = request.form['add_{:s}_county'.format(str(address_no))]
        address['postcode'] = request.form['add_{:s}_postcode'.format(str(address_no))]

        if address['address_lines'][0] != '' and address['county'] != '' and address['postcode'] != '':
            amended_addresses.append(address)

        address_no += 1

    application_dict['residence'] = amended_addresses
    session['data_amended'] = 'true'

    # check if user wants to enter and additional address
    if request.form['add_address'] == 'yes':
        new_address = {'county': '', 'postcode': '', 'address_lines': []}
        application_dict['residence'].append(new_address)
        return redirect('/amend_address', code=302, Response=None)
    else:
        if session['application_type'] == 'bank_regn':
            return redirect('/verify_registration', code=302, Response=None)
        else:
            return redirect('/process_application/' + session['application_type'], code=302, Response=None) """


# TODO: should /search_result be removed?
"""
@app.route('/amend_court', methods=["GET"])
def show_court():
    return render_template('regn_court.html', application_type=session['application_type'],
                           data=session['application_dict'], images=session['images'], current_page=0) """

# TODO: should /search_result be removed?
"""
@app.route('/update_court', methods=["POST"])
def update_court():
    application_dict = session['application_dict']

    application_dict['key_number'] = request.form['key_no'].strip()
    application_dict['legal_body'] = request.form['court'].strip()
    application_dict['legal_body_ref'] = request.form['ref'].strip()

    session['data_amended'] = 'true'

    if session['application_type'] == 'bank_regn':
        return redirect('/verify_registration', code=302, Response=None)
    else:
        return redirect('/process_application/' + session['application_type'], code=302, Response=None) """

# TODO: should /search_result be removed?
"""
@app.route('/submit_amendment', methods=["POST"])
def submit_amendment():
    application_dict = session['application_dict']

    if 'Reject' in request.form:
        return render_template('rejection.html', application_type=session['application_type'])

    # TODO: these are needed at the moment for registration but are not captured on the form
    application_dict["key_number"] = "2244095"  # TODO: is design changing to add key_number??
    application_dict["application_ref"] = " "  # TODO: customer ref needed??
    today = datetime.now().strftime('%Y-%m-%d')
    application_dict["date"] = today
    application_dict["residence_withheld"] = False
    application_dict['date_of_birth'] = "1980-01-01"  # TODO: DOB still needed??
    application_dict['regn_no'] = session['regn_no']
    application_dict["document_id"] = session['document_id']

    url = app.config['CASEWORK_API_URL'] + '/applications/' + session['regn_no'] + '?action=amend'
    headers = {'Content-Type': 'application/json'}
    response = requests.put(url, json.dumps(application_dict), headers=headers)
    if response.status_code == 200:
        data = response.json()
        reg_list = []
        # for item in data['new_registrations']:
        #     reg_list.append(item)

        # session['regn_no'] = reg_list
        # reg_list = []
        for item in data['new_registrations']:
            reg_list.append(item['number'])
        session['confirmation'] = {'reg_no': reg_list}
        delete_from_worklist(session['worklist_id'])
    else:
        err = response.status_code
        logging.error(err)
        return render_template('error.html', error_msg=err), 500

    return redirect('/get_list?appn=amend', code=302, Response=None) """
