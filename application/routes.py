from application import app
from flask import Response, request, render_template, session
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
    data = get_totals()
    if app.config['DEMONSTRATION_VIEW']:
        return render_template('totals_demo.html', data=data)
    else:
        return render_template('totals.html', data=data)


@app.route('/start_rectification', methods=["GET"])
def start_rectification():
    session['application_type'] = "rectify"
    return render_template('rect_retrieve.html')


@app.route('/get_list', methods=["GET"])
def get_list():
    requested_worklist = request.args.get('appn')
    url = app.config['CASEWORK_DB_URL'] + '/work_list/' + requested_worklist
    response = requests.get(url)
    work_list_json = response.json()
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

    totals = get_totals()
    if app.config['DEMONSTRATION_VIEW']:
        return render_template('sub_list_demo.html', worklist=appn_list, requested_list=requested_worklist, data=totals)
    else:
        return render_template('sub_list.html', worklist=appn_list, requested_list=requested_worklist, data=totals)


@app.route('/get_application/<application_type>/<appn_id>/<appn_type>', methods=["GET"])
def get_application(application_type, appn_id, appn_type):
    url = app.config['CASEWORK_DB_URL'] + '/search/' + appn_id

    response = requests.get(url)
    application_json = response.json()
    document_id = application_json['document_id']
    doc_response = requests.get(app.config["DOCUMENT_URL"] + "/document/" + str(document_id))
    image_data = doc_response.json()

    images = []
    for image in image_data['images']:
        images.append(app.config["DOCUMENT_URL"] + image)

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
    regn_no = request.form['reg_no']
    session['regn_no'] = regn_no

    image_details = ['']

    if application_type == 'rectify':
        template = 'rect_amend.html'
    elif application_type == 'amend':
        template = 'regn_amend.html'
        image_details = session['images']
    else:
        template = 'regn_cancel.html'
        image_details = session['images']

    url = app.config['BANKRUPTCY_DATABASE_URL'] + '/registration/' + regn_no

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
                               error_msg=error_msg, images=image_details, current_page=0)

    original_image_data = "none"

    if application_json['document_id'] is not None and application_json['document_id'] is not '0':
        document_id = application_json['document_id']

        doc_response = requests.get(app.config["DOCUMENT_URL"] + "/document/" + str(document_id))
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

    print(application_json)
    return render_template(template, application_type=application_type, data=application_json,
                           images=image_details, current_page=0, original_image_data=original_image_data, addr=0)


@app.route('/process_request', methods=["POST"])
def process_request():
    application_type = session['application_type']
    application_dict = session['application_dict']
    image_list = session['images']
    regn_no = session['regn_no']
    display_date = datetime.now().strftime('%d.%m.%Y')

    if 'Amend' in request.form:
        template = 'regn_amend.html'
    elif 'Continue' in request.form:
        template = 'confirmation.html'
        url = app.config['BANKRUPTCY_DATABASE_URL'] + '/registration/' + regn_no
        # TODO: pass empty dict for now, ian mentioned about doc id needed?
        data = {}
        headers = {'Content-Type': 'application/json'}
        response = requests.delete(url, data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            data = response.json()
            # although this is list it is called application_dict to reuse render template statement below
            application_dict = []
            for item in data['cancelled']:
                application_dict.append(item)
            delete_from_worklist(session['worklist_id'])

        else:
            err = response.status_code
            logging.error(err)
            return render_template('error.html', error_msg=err), 500
    else:
        template = 'rejection.html'

    return render_template(template, application_type=application_type, data=application_dict,
                           images=image_list, current_page=0, date=display_date,
                           original_image_data=session['original_image_data'])


@app.route('/submit_amendment', methods=["POST"])
def submit_amendment():
    application_type = session['application_type']
    application_dict = session['application_dict']
    regn_no = session['regn_no']
    display_date = datetime.now().strftime('%d.%m.%Y')

    if 'Reject' in request.form:
        return render_template('rejection.html', application_type=application_type)

    # TODO: these are needed at the moment for registration but are not captured on the form
    application_dict["key_number"] = "2244095"
    application_dict["application_ref"] = "customer reference"
    today = datetime.now().strftime('%Y-%m-%d')
    application_dict["date"] = today
    application_dict["residence_withheld"] = False
    application_dict['date_of_birth'] = "1980-01-01"
    url = app.config['BANKRUPTCY_DATABASE_URL'] + '/registration/' + regn_no
    headers = {'Content-Type': 'application/json'}
    response = requests.put(url, json.dumps(application_dict), headers=headers)
    if response.status_code == 200:
        data = response.json()
        reg_list = []
        for item in data['new_registrations']:
            reg_list.append(item)

        delete_from_worklist(session['worklist_id'])
    else:
        err = response.status_code
        logging.error(err)
        return render_template('error.html', error_msg=err), 500

    return render_template('confirmation.html', application_type=application_type, data=reg_list,
                           date=display_date)


@app.route('/submit_rectification', methods=["POST"])
def submit_rectification():
    application_type = session['application_type']
    application_dict = session['application_dict']
    regn_no = session['regn_no']
    display_date = datetime.now().strftime('%d.%m.%Y')

    # these are needed at the moment for registration but are not captured on the form
    application_dict["key_number"] = "2244095"
    application_dict["application_ref"] = "customer reference"
    today = datetime.now().strftime('%Y-%m-%d')
    application_dict["date"] = today
    application_dict["residence_withheld"] = False
    application_dict['date_of_birth'] = "1980-01-01"

    # TODO: once backend rectification code is in place
    url = app.config['BANKRUPTCY_DATABASE_URL'] + '/registration/' + regn_no
    headers = {'Content-Type': 'application/json'}
    response = requests.put(url, json.dumps(application_dict), headers=headers)
    if response.status_code == 200:
        data = response.json()
        reg_list = []
        for item in data['new_registrations']:
            reg_list.append(item)
    else:
        err = response.status_code
        logging.error(err)
        return render_template('error.html', error_msg=err), 500

    return render_template('confirmation.html', application_type=application_type, data=reg_list,
                           date=display_date, acknowledgement=request.form['ack'])


@app.route('/amend_name', methods=["GET"])
def show_name():
    application_type = session['application_type']
    application_dict = session['application_dict']

    image_list = session['images']

    return render_template('regn_name.html', application_type=application_type, data=application_dict,
                           images=image_list, current_page=0)


@app.route('/update_name', methods=["POST"])
def update_name_details():
    application_type = session['application_type']
    application_dict = session['application_dict']
    image_list = session['images']

    forenames = request.form['forenames'].strip()
    surname = request.form['surname'].strip()
    occupation = request.form['occupation'].strip()

    new_debtor_name = {
        'forenames': forenames.split(),
        'surname': surname
    }

    application_dict['debtor_name'] = new_debtor_name
    application_dict['occupation'] = occupation

    return render_template('regn_amend.html', application_type=application_type, data=application_dict,
                           images=image_list, current_page=0, original_image_data=session['original_image_data'],
                           data_amended='true')


# TODO: renamed as 'complete', move to back-end?
def delete_from_worklist(application_id):
    url = app.config['CASEWORK_DB_URL'] + '/workitem/' + application_id
    response = requests.delete(url)
    if response.status_code != 204:
        err = 'Failed to delete application ' + application_id + ' from the worklist. Error code:' \
              + str(response.status_code)

        logging.error(err)
        raise RuntimeError(err)


# Commented out - it's quite slow...
# def send_notification(application):
#     logging.info('Sending notification')
#     import subprocess
#     from requests.utils import quote
#     print(session)
#     application = session['application_dict']
#     name = quote(' '.join(application['debtor_name']['forenames']) + ' ' + application['debtor_name']['surname'])
#     app_type = quote(application['application_type'])
#     date = quote(application['date'])
#     reg_no = quote(str(application['reg_nos'][0]))
#     parts = quote('[Insert particulars here]')
#     params = "type={}&date={}&reg_no={}&name={}&parts={}".format(
#         app_type, date, reg_no, name, parts
#     )
#     url = "localhost:5010/acknowledgement?" + params
#     subprocess.check_output(['wkhtmltopdf', 'http://' + url, '/tmp/' + reg_no + '.pdf'])
#
#     localhost:5010/acknowledgement?type=PA(B)&reg_no=50001&date=26.12.2014&name=Bob%20Howard&parts=Stuff%20Goes%20Here
#     print(application)


@app.route('/amend_address', methods=["GET"])
def show_address():
    application_type = session['application_type']
    application_dict = session['application_dict']
    image_list = session['images']

    return render_template('regn_address.html', application_type=application_type, data=application_dict,
                           images=image_list, current_page=0)


@app.route('/update_address', methods=["POST"])
def update_address_details():
    application_type = session['application_type']
    application_dict = session['application_dict']
    image_list = session['images']
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

    # check if user wants to enter and additional address
    if request.form['add_address'] == 'yes':
        new_address = {'county': '', 'postcode': '', 'address_lines': []}
        application_dict['residence'].append(new_address)
        return render_template('regn_address.html', application_type=application_type, data=application_dict,
                               images=image_list, current_page=0)
    else:
        return render_template('regn_amend.html', application_type=application_type, data=application_dict,
                               images=image_list, current_page=0, original_image_data=session['original_image_data'],
                               data_amended='true')


@app.route('/remove_address/<int:addr>', methods=["GET"])
def remove_address(addr):
    application_type = session['application_type']
    application_dict = session['application_dict']
    image_list = session['images']

    del application_dict['residence'][addr]

    return render_template('regn_address.html', application_type=application_type, data=application_dict,
                           images=image_list, current_page=0,data_amended='true')


@app.route('/amend_alias/<name_index>', methods=["GET"])
def show_alias(name_index):
    application_type = session['application_type']
    application_dict = session['application_dict']
    image_list = session['images']

    if name_index != 'new':
        name_index = int(name_index)

    return render_template('regn_alias.html', application_type=application_type, data=application_dict,
                           images=image_list, current_page=0, name_index=name_index)


@app.route('/remove_alias/<int:name>', methods=["GET"])
def remove_alias(name):
    application_type = session['application_type']
    application_dict = session['application_dict']
    image_list = session['images']
    del application_dict['debtor_alternative_name'][name]

    return render_template('regn_amend.html', application_type=application_type, data=application_dict,
                           images=image_list, current_page=0, original_image_data=session['original_image_data'])


@app.route('/update_alias/<name_index>', methods=["POST"])
def update_alias(name_index):
    application_type = session['application_type']
    application_dict = session['application_dict']
    image_list = session['images']

    forenames = request.form['forenames'].strip()
    surname = request.form['surname'].strip()

    alias_name = {
        'forenames': forenames.split(),
        'surname': surname
    }

    if name_index == 'new':
        application_dict['debtor_alternative_name'].append(alias_name)
    else:
        application_dict['debtor_alternative_name'][int(name_index)] = alias_name

    return render_template('regn_amend.html', application_type=application_type, data=application_dict,
                           images=image_list, current_page=0, original_image_data=session['original_image_data'])


@app.route('/amend_court', methods=["GET"])
def show_court():
    application_type = session['application_type']
    application_dict = session['application_dict']

    image_list = session['images']

    return render_template('regn_court.html', application_type=application_type, data=application_dict,
                           images=image_list, current_page=0)


@app.route('/update_court', methods=["POST"])
def update_court():
    application_type = session['application_type']
    application_dict = session['application_dict']
    image_list = session['images']

    application_dict['legal_body'] = request.form['court'].strip()
    application_dict['legal_body_ref'] = request.form['ref'].strip()

    return render_template('regn_amend.html', application_type=application_type, data=application_dict,
                           images=image_list, current_page=0, original_image_data=session['original_image_data'],
                           data_amended='true')


@app.route('/process_banks_name', methods=["POST"])
def process_banks_name():
    appn_type = session['application_dict']['application_type']
    doc_id = session['document_id']

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

    requested_worklist = 'bank_regn'
    images = session['images']
    name['application_type'] = appn_type
    name['document_id'] = doc_id
    set_session_variables({'application_dict': name})
    application = session['application_dict']

    return render_template('address.html', application=application, images=images,
                           requested_list=requested_worklist, current_page=0)


@app.route('/court_details', methods=["POST"])
def process_court_details():
    # application = json.loads(request.form['application'])
    application = session['application_dict']
    application["application_type"] = request.form['nature']
    application["legal_body"] = request.form['court']
    application["legal_body_ref"] = request.form['court_ref']

    # these are needed at the moment for registration but are not captured on the form
    application["key_number"] = "2244095"
    application["application_ref"] = "customer reference"
    today = datetime.now().strftime('%Y-%m-%d')
    application["date"] = today
    application["residence_withheld"] = False
    application['date_of_birth'] = "1980-01-01"
    application["document_id"] = session['document_id']

    url = app.config['BANKRUPTCY_DATABASE_URL'] + '/registration'
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(application), headers=headers)

    if response.status_code == 200:
        data = response.json()
        reg_list = []
        for item in data['new_registrations']:
            reg_list.append(item)
        application['reg_nos'] = reg_list
        requested_worklist = 'bank_regn'
        display_date = datetime.now().strftime('%d.%m.%Y')
        delete_from_worklist(session['worklist_id'])

        # thread = Thread(target=send_notification, args=(session['application_dict'],))
        # thread.start()
        # send_notification(session['application_dict'])

        return render_template('confirmation.html', application=application, data=reg_list, date=display_date,
                               application_type=requested_worklist)
    else:
        error = response.status_code
        logging.error(error)
        return render_template('error.html', error_msg=error), 500


@app.route('/address', methods=['POST'])
def application_step_2():
    # application = json.loads(request.form['application'])
    application = session['application_dict']
    if 'residence' not in application:
        application['residence'] = []

    # handle empty 'last address'.
    # if request.form['address1'] != '' and 'address2' in request.form and 'submit' in request.form:
    address = {'address_lines': []}
    if 'address1' in request.form and request.form['address1'] != '':
        address['address_lines'].append(request.form['address1'])
    if 'address2' in request.form and request.form['address2'] != '':
        address['address_lines'].append(request.form['address2'])
    if 'address3' in request.form and request.form['address3'] != '':
        address['address_lines'].append(request.form['address3'])

    address['county'] = request.form['county']
    address['postcode'] = request.form['postcode']
    application['residence'].append(address)
    requested_worklist = 'bank_regn'

    if 'add_address' in request.form:
        return render_template('address.html', application=json.dumps(application), images=session['images'],
                               residences=application['residence'], requested_list=requested_worklist, current_page=0)
    else:
        return render_template('banks_order.html', application=json.dumps(application),
                               images=session['images'],
                               requested_list=requested_worklist, current_page=0,
                               appn_type=session['application_dict']['application_type'])


@app.route('/process_rectification', methods=['POST'])
def process_rectification():
    # appn_type will be type of bankruptcy being processed i.e. PAB or WOB
    appn_type = session['application_dict']['application_type']

    name = {"debtor_name": {"forenames": [], "surname": ""},
            "occupation": "",
            "debtor_alternative_name": [],
            "residence": []
            }
    alt_name = {"forenames": [],
                "surname": ""
                }

    for i in request.form['forenames'].split():
        name['debtor_name']['forenames'].append(i)

    name['debtor_name']['surname'] = request.form['surname']
    name['occupation'] = request.form['occupation']

    counter = 0
    while True:
        try:
            alt_forenames = request.form["aliasforename" + str(counter)]
            alt_surname = request.form["aliassurname" + str(counter)]
        except KeyError:
            break

        for i in alt_forenames.split():
            alt_name['forenames'].append(i)

        alt_name['surname'] = alt_surname
        if alt_forenames != '' and alt_surname != '':
            name['debtor_alternative_name'].append(alt_name)

        alt_name = {"forenames": [], "surname": ""}
        counter += 1

    application_dict = name

    counter = 0
    while True:
        addr1_counter = "address1" + str(counter)
        addr2_counter = "address2" + str(counter)
        addr3_counter = "address3" + str(counter)
        county_counter = "county" + str(counter)
        postcode_counter = "postcode" + str(counter)
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
        application_dict['residence'].append(address)
        counter += 1

    application_dict['legal_body'] = request.form['court'].strip()
    application_dict['legal_body_ref'] = request.form['ref'].strip()
    application_dict['application_type'] = appn_type
    if 'document_id' in session:
        application_dict['document_id'] = session['document_id']
    else:
        application_dict['document_id'] = None

    session['application_dict'] = application_dict

    return render_template('rect_summary.html', application_type=session['application_type'], data=application_dict,
                           date='')


@app.route('/process_search/<search_type>', methods=['POST'])
def process_search(search_type):
    logging.info('From the top')
    application_type = session['application_type']
    application = session['application_dict']

    if 'all_counties' in request.form:
        counties = []
    elif 'area_list' in request.form and request.form['area_list'] != '':
        counties = request.form['area_list'].upper().strip('\r\n').split()
    else:
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

    customer = {
        'key_number': request.form['key_no'],
        'name': request.form['customer_name'],
        'address': request.form['customer_address'],
        'reference': request.form['customer_ref']
    }

    search_data = {
        'customer': customer,
        'document_id': application['document_id'],
        'parameters': parameters
    }

    session['search_data'] = search_data
    url = app.config['BANKRUPTCY_DATABASE_URL'] + '/search'
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

    return render_template('confirmation.html', application_type=application_type)


@app.route('/process_search_name/<search_type>', methods=['POST'])
def process_search_name(search_type):
    logging.info('Entering search name')
    application_type = session['application_type']
    application_dict = session['application_dict']

    """
    if 'all_counties' in request.form:
        counties = []
    elif 'area_list' in request.form and request.form['area_list'] != '':
        counties = request.form['area_list'].upper().strip('\r\n').split()
    else:
        counties = []"""
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

    application_dict['search_criteria'] = parameters

    if search_type == 'full':
        return render_template('search_counties.html', images=session['images'], application=application_dict,
                               application_type=application_type, current_page=0)
    else:
        return render_template('search_customer.html', images=session['images'], application=application_dict,
                               application_type=application_type, current_page=0)


@app.route('/process_search_county', methods=['POST'])
def process_search_county():
    if 'all_counties' in request.form and request.form['all_counties'] == 'yes':
        counties = []
    elif 'area_list' in request.form and request.form['area_list'] != '':
        counties = request.form['area_list'].upper().strip('\r\n').split()
    else:
        counties = []

    session['application_dict']['search_criteria']['counties'] = counties

    return render_template('search_customer.html', images=session['images'], application=session['application_dict'],
                           application_type=session['application_type'], current_page=0)


@app.route('/submit_search', methods=['POST'])
def submit_search():
    logging.info('Entering submit search')
    application_type = session['application_type']
    application = session['application_dict']

    customer = {
        'key_number': request.form['key_no'],
        'name': request.form['customer_name'],
        'address': request.form['customer_address'],
        'reference': request.form['customer_ref']
    }

    search_data = {
        'customer': customer,
        'document_id': application['document_id'],
        'parameters': application['search_criteria']
    }

    session['search_data'] = search_data
    url = app.config['BANKRUPTCY_DATABASE_URL'] + '/search'
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

    return render_template('confirmation.html', application_type=application_type, application=application)


@app.route('/search_result', methods=['GET'])
def search_result():

    display = []
    for result in session['search_result']:
        for key, value in result.items():
            print()
            if len(value) == 0:
                display.append({
                    'name': key,
                    'result': 'No Match'
                })
            else:
                display.append({
                    'name': key,
                    'result': 'Match Found - Registration number is: ' + str(value)
                })

    print('---------')
    print(session['search_data'])
    print('search_result is ', session['search_result'])
    return render_template('search_result.html', display=display, results=session['search_result'], search_data=session['search_data'])


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
    pabs, wobs, banks, lcreg, amend, canc, portal, search, ocp = (0,) * 9
    url = app.config['CASEWORK_DB_URL'] + '/work_list/all?'
    response = requests.get(url)
    if response.status_code == 200:
        full_list = response.json()

        for item in full_list:
            if item['work_type'] == "bank_regn" and item['application_type'] == "PA(B)":
                pabs += 1
                banks += 1
            elif item['work_type'] == "bank_regn" and item['application_type'] == "WO(B)":
                wobs += 1
                banks += 1
            elif item['work_type'] == "lc_regn":
                lcreg += 1
            elif item['work_type'] == "amend":
                amend += 1
            elif item['work_type'] == "cancel":
                canc += 1
            elif item['work_type'] == "prt_search":
                portal += 1
            elif item['work_type'] == "search":
                search += 1
            elif item['work_type'] == "oc":
                ocp += 1

    return {
        'pabs': pabs,
        'wobs': wobs,
        'banks': banks,
        'lcreg': lcreg,
        'amend': amend,
        'canc': canc,
        'portal': portal,
        'search': search,
        'oc': ocp
    }


@app.route('/totals', methods=['GET'])
def totals():
    data = get_totals()
    return Response(json.dumps(data), status=200, mimetype='application/json')


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
        print(data)

        return render_template('complex_name_select.html', images=session['images'],
                               application=session['application_type'], application_type=session['application_type'],
                               current_page=0, complex=data, orig_name=complex_search['name'])
    else:
        error = response.status_code
        logging.error(error)
        return render_template('error.html', error_msg=error), 500


@app.template_filter()
def date_time_filter(date_str, format='%d %B %Y'):
    """convert a datetime to a different format."""
    value = datetime.strptime(date_str, '%Y-%m-%d').date()
    return value.strftime(format)

app.jinja_env.filters['date_time_filter'] = date_time_filter


def page_required(appn_type):
    html_page = {
        "amend": "regn_retrieve.html",
        "cancel": "regn_retrieve.html",
        "bank_regn": "application.html",
        # "search": "search_capture.html",
        "search": "search_name.html",
        "full_search": "search_full_capture.html",
        "oc": "regn_retrieve.html",
        "lc": "application.html"
    }

    return html_page.get(appn_type)


def set_session_variables(variable_dict):
    for key in variable_dict:
        session[key] = variable_dict[key]
