from application import app
from flask import Response, request, render_template, session, redirect, url_for
import requests
from datetime import datetime
import logging
import json

#
# @app.errorhandler(Exception)
# def error_handler(err):
#     logging.error('========== Error Caught ===========')
#     logging.error(err)
#     return render_template('error.html', error_msg=str(err)), 500


@app.route('/', methods=["GET"])
def index():
    if 'worklist_id' in session:
        url = app.config['CASEWORK_DB_URL'] + '/applications/' + session['worklist_id'] + '/lock'
        requests.delete(url)
        del(session['worklist_id'])

    data = get_totals()
    if app.config['DEMONSTRATION_VIEW']:
        return render_template('totals_demo.html', data=data)
    else:
        return render_template('totals.html', data=data)


@app.route('/get_list', methods=["GET"])
def get_list():
    if 'worklist_id' in session:
        url = app.config['CASEWORK_DB_URL'] + '/applications/' + session['worklist_id'] + '/lock'
        requests.delete(url)
        del(session['worklist_id'])

    return get_list_of_applications(request.args.get('appn'), "")


def get_list_of_applications(requested_worklist, error_msg):
    url = app.config['CASEWORK_DB_URL'] + '/applications?type=' + requested_worklist
    response = requests.get(url)
    work_list_json = response.json()
    return_page = ''
    if requested_worklist.startswith('bank'):
        return_page = 'work_list_bank.html'
    elif requested_worklist.startswith('lc'):
        return_page = 'work_list_lc.html'
    elif requested_worklist.startswith('search'):
        return_page = 'work_list_search.html'
    elif requested_worklist.startswith('canc'):
        return_page = 'work_list_cancel.html'

    appn_list = []

    if len(work_list_json) > 0:
        for appn in work_list_json:
            # reformat result to include separate date and time received strings
            date = datetime.strptime(appn['date_received'], "%Y-%m-%d %H:%M:%S")

            application = {
                "appn_id": appn['appn_id'],
                "received_tmstmp": appn['date_received'],
                "date_received": "{:%d %B %Y}".format(date),
                "time_received": "{:%H:%M}".format(date),
                "application_type": appn['application_type'],
                "status": appn['status'],
                "work_type": appn['work_type'],
                "assigned_to": appn['assigned_to'],
                }
            appn_list.append(application)

    app_totals = get_totals()

    if app.config['DEMONSTRATION_VIEW']:
        return render_template('sub_list_demo.html', worklist=appn_list, requested_list=requested_worklist,
                               data=app_totals, error_msg=error_msg)
    else:
        return render_template(return_page, worklist=appn_list, requested_list=requested_worklist,
                               data=app_totals, error_msg=error_msg)


@app.route('/application_start/<application_type>/<appn_id>/<appn_type>', methods=["GET"])
def application_start(application_type, appn_id, appn_type):

    # Lock application if not in session otherwise assume user has refreshed the browser after select an application
    if 'worklist_id' not in session:
        url = app.config['CASEWORK_DB_URL'] + '/applications/' + appn_id + '/lock'
        response = requests.post(url)
        if response.status_code == 404:
            error_msg = "This application is being processed by another member of staff, " \
                        "please select a different application."
            return get_list_of_applications(application_type, error_msg)

    url = app.config['CASEWORK_DB_URL'] + '/applications/' + appn_id

    response = requests.get(url)

    application_json = response.json()
    document_id = application_json['application_data']['document_id']
    doc_response = requests.get(app.config["CASEWORK_DB_URL"] + "/forms/" + str(document_id))

    images = []
    image_data = doc_response.json()
    for page in image_data['images']:
        url = app.config["CASEWORK_DB_URL"] + "/forms/" + str(document_id) + '/' + str(page)
        images.append(url)

    if appn_type == "Full Search":
        template = page_required("search")
    else:
        template = page_required(application_type)

    application_json['application_type'] = appn_type

    session.clear()
    set_session_variables({'images': images, 'document_id': document_id,
                           'application_type': application_type, 'worklist_id': appn_id,
                           'application_dict': application_json})

    application = session['application_dict']

    years = {"year_from": "1925",
             "year_to": datetime.now().strftime('%Y')
             }

    return render_template(template, application_type=application_type, data=application_json,
                           images=images, application=application, years=years,
                           current_page=0)


@app.route('/get_details', methods=["POST"])
def get_bankruptcy_details():
    application_type = session['application_type']
    session['regn_no'] = request.form['reg_no']
    session['reg_date'] = '%s-%s-%s' % (request.form['reg_year'], request.form['reg_month'], request.form['reg_day'])

    url = app.config['BANKRUPTCY_DATABASE_URL'] + '/registrations/' + session['reg_date'] + '/' + session['regn_no']

    response = requests.get(url)

    error_msg = None

    if response.status_code == 404:
        error_msg = "Registration not found please re-enter"
    else:
        application_json = response.json()
        if application_json['status'] == 'cancelled' or application_json['status'] == 'superseded':
            error_msg = "Application has been cancelled or amended - please re-enter"

    if error_msg is not None:
        template = 'regn_retrieve.html'
        if application_type == 'rectify':
            template = 'rect_retrieve.html'

        return render_template(template, application_type=application_type,
                               error_msg=error_msg, images=session['images'], current_page=0)

    original_image_data = "none"

    if application_json['document_id'] is not None and application_json['document_id'] is not '0':
        document_id = application_json['document_id']

        doc_response = requests.get(app.config["DOCUMENT_URL"] + "/forms/" + str(document_id))
        original_image_data = doc_response.json()

        images = []
        for image in original_image_data['images']:
            images.append(app.config["DOCUMENT_URL"] + image)
        original_image_data = images

        set_session_variables({'document_id': document_id})
        if application_type == 'rectify':
            session['images'] = images

    set_session_variables({
        'original_image_data': original_image_data,
        'application_dict': application_json
    })

    return redirect('/process_application/' + application_type, code=302, Response=None)


@app.route('/process_application/<application_type>', methods=['GET'])
def process_application(application_type):
    if application_type == 'rectify':
        template = 'rect_amend.html'
    elif application_type == 'amend':
        template = 'regn_amend.html'
    else:
        template = 'regn_cancel.html'
    if 'data_amended' not in session:
        session['data_amended'] = 'false'

    return render_template(template, application_type=application_type, data=session['application_dict'],
                           images=session['images'], current_page=0, original_image_data=session['original_image_data'],
                           data_amended=session['data_amended'])


@app.route('/retrieve_new_reg', methods=["GET"])
def retrieve_new_reg():
    return redirect('/application_start/%s/%s/%s' % (session['application_type'], session['worklist_id'],
                    session['application_dict']['application_type']), code=302, Response=None)


# Registration routes
@app.route('/process_banks_name', methods=["POST"])
def process_banks_name():

    name = {"debtor_name": {"forenames": [], "surname": ""},
            "occupation": "",
            "debtor_alternative_name": [],
            "residence": [],
            }

    if 'comp_number' in request.form:
        comp_name = {"name": request.form['comp_name'], "number": int(request.form['comp_number'])}
        name['complex'] = comp_name
    elif 'complex_number' in request.form:
        comp_name = {"name": request.form['complex_name'], "number": int(request.form['complex_number'])}
        name['complex'] = comp_name
    else:
        alt_name = {"forenames": [],
                    "surname": ""
                    }

        for i in request.form['forename'].split():
            name['debtor_name']['forenames'].append(i)

        name['debtor_name']['surname'] = request.form['surname']
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

            for i in alt_forenames.split():
                alt_name['forenames'].append(i)

            alt_name['surname'] = alt_surname
            if alt_forenames != '' and alt_surname != '':
                name['debtor_alternative_name'].append(alt_name)

            alt_name = {"forenames": [], "surname": ""}
            counter += 1

    name['application_type'] = session['application_dict']['application_type']
    set_session_variables({'application_dict': name})

    return redirect('/address_details', code=302, Response=None)


@app.route('/complex_name', methods=['GET'])
def complex_name():
    logging.info('Entering complex name')
    application_type = session['application_type']
    application = session['application_dict']

    return render_template('complex_name_reg.html', images=session['images'], application=application,
                           application_type=application_type, current_page=0)


@app.route('/complex_retrieve', methods=['POST'])
def complex_name_retrieve():
    logging.info('Entering complex name retrieval')
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
        return render_template('error.html', error_msg=error), 500


@app.route('/address_details', methods=["GET"])
def address_details():
    return render_template('address.html', images=session['images'], current_page=0)


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

    return redirect('/court_details', code=302, Response=None)


@app.route('/court_details', methods=['GET'])
def court_details():
    return render_template('banks_order.html', images=session['images'], current_page=0,
                           charge=session['application_dict']['application_type'])


@app.route('/process_court_details', methods=["POST"])
def process_court_details():
    application = session['application_dict']
    application["legal_body"] = request.form['court']
    application["legal_body_ref"] = '%s of %s' % (request.form['court_no'], request.form['court_year'])
    application["key_number"] = request.form['keyno']

    return redirect('/verify_registration', code=302, Response=None)


@app.route('/verify_registration', methods=['GET'])
def verify_registration():
    return render_template('regn_verify.html', images=session['images'], current_page=0,
                           data=session['application_dict'])


@app.route('/process_registration', methods=['POST'])
def process_registration():
    application = session['application_dict']
    application["application_ref"] = " "  # TODO: do we need to capture the customer reference
    today = datetime.now().strftime('%Y-%m-%d')
    application["date"] = today
    application["residence_withheld"] = False
    application['date_of_birth'] = "1980-01-01"  # TODO: what are we doing about the DOB??
    application["document_id"] = session['document_id']

    url = app.config['CASEWORK_DB_URL'] + '/applications/' + session['worklist_id'] + '?action=complete'
    headers = {'Content-Type': 'application/json'}
    response = requests.put(url, data=json.dumps(application), headers=headers)
    if response.status_code == 200:
        data = response.json()
        reg_list = []
        for item in data['new_registrations']:
            reg_list.append(item)
        session['regn_no'] = reg_list
        return redirect('/confirmation', code=302, Response=None)
    else:
        error = response.status_code
        logging.error(error)
        return render_template('error.html', error_msg=error), 500
    # url = app.config['BANKRUPTCY_DATABASE_URL'] + '/registrations'
    # headers = {'Content-Type': 'application/json'}
    # response = requests.post(url, data=json.dumps(application), headers=headers)
    #
    # if response.status_code == 200:
    #     data = response.json()
    #     reg_list = []
    #     for item in data['new_registrations']:
    #         reg_list.append(item)
    #     session['regn_no'] = reg_list
    #     delete_from_worklist(session['worklist_id'])
    #
    #     return redirect('/confirmation', code=302, Response=None)
    # else:
    #     error = response.status_code
    #     logging.error(error)
    #     return render_template('error.html', error_msg=error), 500
# end of registration routes


# Amendment routes
@app.route('/amend_name', methods=["GET"])
def show_name():
    return render_template('regn_name.html', application_type=session['application_type'],
                           data=session['application_dict'], images=session['images'], current_page=0)


@app.route('/remove_alias_name/<int:name>', methods=["GET"])
def remove_alias_name(name):
    # del session['application_dict']['debtor_alternative_name'][name]
    del session['application_dict']['debtor_names'][name]
    session['data_amended'] = 'true'

    return redirect('/amend_name', code=302, Response=None)


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
        return redirect('/process_application/' + session['application_type'], code=302, Response=None)


@app.route('/amend_address', methods=["GET"])
def show_address():
    return render_template('regn_address.html', application_type=session['application_type'],
                           data=session['application_dict'], images=session['images'], current_page=0,
                           focus_on_address=len(session['application_dict']['residence']))


@app.route('/remove_address/<int:addr>', methods=["GET"])
def remove_address(addr):
    del session['application_dict']['residence'][addr]
    session['data_amended'] = 'true'

    return redirect('/amend_address', code=302, Response=None)


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
            return redirect('/process_application/' + session['application_type'], code=302, Response=None)


@app.route('/amend_court', methods=["GET"])
def show_court():
    return render_template('regn_court.html', application_type=session['application_type'],
                           data=session['application_dict'], images=session['images'], current_page=0)


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
        return redirect('/process_application/' + session['application_type'], code=302, Response=None)


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

    url = app.config['CASEWORK_DB_URL'] + '/applications/' + session['regn_no'] + '?action=amend'
    headers = {'Content-Type': 'application/json'}
    response = requests.put(url, json.dumps(application_dict), headers=headers)
    if response.status_code == 200:
        data = response.json()
        reg_list = []
        for item in data['new_registrations']:
            reg_list.append(item)

        session['regn_no'] = reg_list
        delete_from_worklist(session['worklist_id'])
    else:
        err = response.status_code
        logging.error(err)
        return render_template('error.html', error_msg=err), 500

    return redirect('/confirmation', code=302, Response=None)
# end of amendment routes


# Cancellation routes
@app.route('/submit_cancellation', methods=["POST"])
def submit_cancellation():
    url = app.config['BANKRUPTCY_DATABASE_URL'] + '/registrations/' + session['reg_date'] + '/' + session['regn_no']
    # TODO: pass empty dict for now, ian mentioned about doc id needed?
    data = {}
    headers = {'Content-Type': 'application/json'}
    response = requests.delete(url, data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        session['regn_no'] = []
        data = response.json()
        for item in data['cancelled']:
            session['regn_no'].append(item)
        delete_from_worklist(session['worklist_id'])
        return redirect('/confirmation', code=302, Response=None)
    else:
        err = response.status_code
        logging.error(err)
        return render_template('error.html', error_msg=err), 500
# end of cancellation routes


# Search routes
@app.route('/process_search_name/<search_type>', methods=['POST'])
def process_search_name(search_type):
    logging.info('Entering search name')

    counties = []
    parameters = {
        'counties': counties,
        'search_type': "bankruptcy" if search_type == 'banks' else 'full',
        'search_items': []
    }

    counter = 0
    while True:
        name_field = 'fullname{}'.format(counter)

        if name_field not in request.form:
            break

        if request.form[name_field] != '':
            if 'comp{}'.format(counter) in request.form:
                # Complex name so call legacy db api to get complex names and numbers
                url = app.config['LEGACY_URL'] + '/complex_names/search'
                headers = {'Content-Type': 'application/json'}
                comp_name = {
                    'name': request.form[name_field]
                }
                response = requests.post(url, data=json.dumps(comp_name), headers=headers)
                data = response.json()

                for item in data:
                    search_item = {
                        'name': item['name'],
                        'complex_no': item['number']
                    }
                    if search_type == 'full':
                        logging.info('Getting year stuff')
                        search_item['year_to'] = int(request.form['year_to{}'.format(counter)])
                        search_item['year_from'] = int(request.form['year_from{}'.format(counter)])
                    parameters['search_items'].append(search_item)
            else:
                # Normal name entered
                search_item = {
                    'name': request.form[name_field]
                }

                if search_type == 'full':
                    logging.info('Getting year stuff')
                    search_item['year_to'] = int(request.form['year_to{}'.format(counter)])
                    search_item['year_from'] = int(request.form['year_from{}'.format(counter)])
                parameters['search_items'].append(search_item)
        counter += 1

    session['application_dict']['search_criteria'] = parameters

    if search_type == 'full':
        return redirect('/search_counties', code=302, Response=None)
    else:
        return redirect('/search_customer', code=302, Response=None)


@app.route('/search_counties', methods=['GET'])
def search_counties():
    return render_template('search_counties.html', images=session['images'], application=session['application_dict'],
                           application_type=session['application_type'], current_page=0, backend_uri=app.config['CASEWORK_DB_URL'])


@app.route('/process_search_county', methods=['POST'])
def process_search_county():
    if 'all_counties' in request.form and request.form['all_counties'] == 'yes':
        counties = []
    elif 'area_list' in request.form and request.form['area_list'] != '':
        counties = request.form['area_list'].upper().strip('\r\n').split()
    else:
        counties = []

    session['application_dict']['search_criteria']['counties'] = counties

    return redirect('/search_customer', code=302, Response=None)


@app.route('/search_customer', methods=['GET'])
def search_customer():
    return render_template('search_customer.html', images=session['images'], application=session['application_dict'],
                           application_type=session['application_type'], current_page=0, backend_uri=app.config['CASEWORK_DB_URL'])


@app.route('/submit_search', methods=['POST'])
def submit_search():
    logging.info('Entering submit search')

    customer = {
        'key_number': request.form['key_number'],
        'name': request.form['customer_name'],
        'address': request.form['customer_address'],
        'reference': request.form['customer_ref']
    }

    search_data = {
        'customer': customer,
        'document_id': session['document_id'],
        'parameters': session['application_dict']['search_criteria']
    }

    session['search_data'] = search_data
    url = app.config['BANKRUPTCY_DATABASE_URL'] + '/searches'
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(search_data), headers=headers)

    if response.status_code == 200:
        search_response = response.json()
        set_session_variables({'search_result': search_response})
        delete_from_worklist(session['worklist_id'])
    elif response.status_code == 404:
        session['search_result'] = []
        delete_from_worklist(session['worklist_id'])
    else:
        logging.error('Unexpected return code: %d', response.status_code)
        return render_template('error.html')

    return redirect('/confirmation', code=302, Response=None)


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
    return render_template('search_result.html', display=display, results=session['search_result'], search_data=session['search_data'])
# end of search routes


# Rectification routes
@app.route('/start_rectification', methods=["GET"])
def start_rectification():
    session['application_type'] = "rectify"
    return render_template('rect_retrieve.html')
# end of rectification routes


# ============== Land Charges routes ===============

@app.route('/land_charge_capture', methods=['POST'])
def land_charge_capture():
    print('this is request.form...')
    print(request.form)
    print('this is session...')
    print(session)
    return get_list_of_applications("lc_regn", "")

# ============== Common routes =====================

@app.route('/confirmation', methods=['GET'])
def confirmation():
    if 'regn_no' not in session:
        session['regn_no'] = []

    return render_template('confirmation.html', data=session['regn_no'], application_type=session['application_type'])


@app.route('/notification', methods=['GET'])
def notification():
    application = session['application_dict']
    data = {
        "type": application['application_type'],
        "reg_no": session['regn_no'],
        "date": application['date'],
        "details": [
            {
                "name": ' '.join(application['debtor_name']['forenames']) + ' ' + application['debtor_name']['surname'],
                "particulars": 'TODO: what goes here?'
            }
        ]
    }
    return render_template('K22.html', data=data)


@app.route('/totals', methods=['GET'])
def totals():
    data = get_totals()
    return Response(json.dumps(data), status=200, mimetype='application/json')


@app.route('/rejection', methods=['GET'])
def rejection():
    application_type = session['application_type']

    return render_template('rejection.html', application_type=application_type)


@app.template_filter()
def date_time_filter(date_str, format='%d %B %Y'):
    """convert a datetime to a different format."""
    value = datetime.strptime(date_str, '%Y-%m-%d').date()
    return value.strftime(format)

app.jinja_env.filters['date_time_filter'] = date_time_filter
# end of common routes


# @app.route('/acknowledgement', methods=['GET'])
# def acknowledgement():
#     data = {
#         "type": request.args.get('type'),
#         "reg_no": request.args.get('reg_no'),
#         "date": request.args.get('date'),
#         "details": [
#             {
#                 "name": request.args.get('name'),
#                 "particulars": request.args.get('parts')
#             }
#         ]
#     }
#     return render_template('K22.html', data=data)


def get_totals():
    # initialise all counters to 0

    bank_regn, bank_amend, bank_rect, bank_with, bank_stored = (0,) * 5
    lc_regn, lc_pn, lc_rect, lc_renewal, lc_stored = (0,) * 5
    canc, canc_part, canc_stored = (0,) * 3
    search_full, search_bank, = (0,) * 2
    unknown = 0

    url = app.config['CASEWORK_DB_URL'] + '/applications'
    response = requests.get(url)
    if response.status_code == 200:
        full_list = response.json()

        for item in full_list:
            if item['work_type'] == "bank_regn":
                bank_regn += 1
            elif item['work_type'] == "bank_amend":
                bank_amend += 1
            elif item['work_type'] == "bank_rect":
                bank_rect += 1
            elif item['work_type'] == "bank_with":
                bank_with += 1
            elif item['work_type'] == "bank_stored":
                bank_stored += 1
            elif item['work_type'] == "lc_regn":
                lc_regn += 1
            elif item['work_type'] == "lc_pn":
                lc_pn += 1
            elif item['work_type'] == "lc_rect":
                lc_rect += 1
            elif item['work_type'] == "lc_renewal":
                lc_renewal += 1
            elif item['work_type'] == "lc_stored":
                lc_stored += 1
            elif item['work_type'] == "cancel":
                canc += 1
            elif item['work_type'] == "cancel_part":
                canc_part += 1
            elif item['work_type'] == "cancel_stored":
                canc_stored += 1
            # elif item['work_type'] == "prt_search":
            #     portal += 1
            elif item['work_type'] == "search_full":
                search_full += 1
            elif item['work_type'] == "search_bank":
                search_bank += 1
            elif item['work_type'] == "unknown":
                unknown += 1

    return {
        'bank_regn': bank_regn, 'bank_amend': bank_amend, 'bank_rect': bank_rect,
        'bank_with': bank_with, 'bank_stored': bank_stored,
        'lc_regn': lc_regn, 'lc_pn': lc_pn, 'lc_rect': lc_rect, 'lc_renewal': lc_renewal, 'lc_stored': lc_stored,
        'canc': canc, 'canc_part': canc_part, 'canc_stored': canc_stored,
        # 'portal': portal,
        'search_full': search_full, 'search_bank': search_bank,
        'unknown': unknown
    }


def page_required(appn_type):
    html_page = {
        "bank_amend": "regn_retrieve.html",
        "cancel": "regn_retrieve.html",
        "bank_regn": "application.html",
        "search": "search_name.html",
        "oc": "regn_retrieve.html",
        "lc_regn": "lc_regn_capture.html"
    }

    return html_page.get(appn_type)


# TODO: renamed as 'complete', move to back-end?
def delete_from_worklist(application_id):
    url = app.config['CASEWORK_DB_URL'] + '/applications/' + application_id
    response = requests.delete(url)
    if response.status_code != 204:
        err = 'Failed to delete application ' + application_id + ' from the worklist. Error code:' \
              + str(response.status_code)

        logging.error(err)
        raise RuntimeError(err)


def set_session_variables(variable_dict):
    for key in variable_dict:
        session[key] = variable_dict[key]
