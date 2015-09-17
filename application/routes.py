from application import app
from flask import request, render_template, session
import requests
from datetime import datetime
import logging
import json


@app.route('/', methods=["GET"])
def index():
    try:
        data = get_totals()
        return render_template('totals.html', data=data)
    except Exception as error:
        logging.error(error)
        return render_template('error.html', error_msg=error), 500


@app.route('/start_rectification', methods=["GET"])
def start_rectification():
    session['application_type'] = "rectify"
    return render_template('rect_retrieve.html')


@app.route('/get_list', methods=["GET"])
def get_list():
    try:
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

        return render_template('sub_list.html', worklist=appn_list, requested_list=requested_worklist, data=totals)

    except Exception as error:
        logging.error(error)
        return render_template('error.html', error_msg=error), 500


@app.route('/get_application/<application_type>/<appn_id>/<appn_type>', methods=["GET"])
def get_application(application_type, appn_id, appn_type):
    try:
        url = app.config['CASEWORK_DB_URL'] + '/search/' + appn_id

        response = requests.get(url)
        application_json = response.json()
        document_id = application_json['document_id']
        doc_response = requests.get(app.config["DOCUMENT_URL"] + "/document/" + str(document_id))
        image_data = doc_response.json()

        images = []
        for image in image_data['images']:
            images.append(app.config["DOCUMENT_URL"] + image)
        session['images'] = images
        session['document_id'] = document_id

        template = page_required(application_type)

        session['application_type'] = application_type
        session['worklist_id'] = appn_id
        session['document_id'] = document_id
        session['application_dict'] = application_json
        session['application_dict']['application_type'] = appn_type
        application = session['application_dict']

        return render_template(template, application_type=application_type, data=application_json,
                               images=images, application=application,
                               current_page=0)

    except Exception as error:
        logging.error(error)
        return render_template('error.html', error_msg=error), 500


@app.route('/get_details', methods=["POST"])
def get_bankruptcy_details():
    try:
        application_type = session['application_type']
        regn_no = request.form['reg_no']
        session['regn_no'] = regn_no
        if application_type == 'rectify':
            image_details = ['']
        else:
            image_details = session['images']

        url = app.config['BANKRUPTCY_DATABASE_URL'] + '/registration/' + regn_no

        response = requests.get(url)

        if application_type == 'amend':
            template = 'regn_amend.html'
        elif application_type == 'rectify':
            template = 'rect_amend.html'
        else:
            template = 'regn_cancel.html'

        if response.status_code == 404:
            error_msg = "Registration not found please re-enter"
            if application_type == "amend" or application_type == "cancel":
                template = 'regn_retrieve.html'
            elif application_type == 'rectify':
                template = 'rect_retrieve.html'
            else:
                template = 'application.html'

            return render_template(template, application_type=application_type,
                                   error_msg=error_msg, images=image_details, current_page=0)
        else:
            application_json = response.json()
            if application_json['status'] == 'cancelled' or application_json['status'] == 'superseded':
                error_msg = "Application has been cancelled or amended - please re-enter"
                if application_type == "amend" or application_type == "cancel":
                    template = 'regn_retrieve.html'
                elif application_type == 'rectify':
                    template = 'rect_retrieve.html'
                else:
                    template = 'application.html'

                return render_template(template, application_type=application_type,
                                       error_msg=error_msg, images=image_details, current_page=0)

            original_image_data = ""

            if application_json['document_id'] is not None:
                document_id = application_json['document_id']
                doc_response = requests.get(app.config["DOCUMENT_URL"] + "/document/" + str(document_id))
                original_image_data = doc_response.json()
                images = []
                for image in original_image_data['images']:
                    images.append(app.config["DOCUMENT_URL"] + image)
                original_image_data = images
                session['document_id'] = document_id
                session['original_image_data'] = original_image_data
                if application_type == 'rectify':
                    session['images'] = images

            else:
                logging.info("No original document images found for registration " + regn_no)

        session['application_dict'] = application_json

        return render_template(template, application_type=application_type, data=application_json,
                               images=image_details, current_page=0, original_image_data=original_image_data, addr=0)

    except Exception as error:
        logging.error(error)
        return render_template('error.html', error_msg=error), 500


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
            for n in data['cancelled']:
                application_dict.append(n)
            try:
                delete_from_worklist(session['worklist_id'])
            except Exception as error:
                logging.error(error)
                return render_template('error.html', error_msg=error), 500
        else:
            error = response.status_code
            logging.error(error)
            return render_template('error.html', error_msg=error), 500
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
    url = app.config['BANKRUPTCY_DATABASE_URL'] + '/registration/' + regn_no + '/' + 'amend'
    headers = {'Content-Type': 'application/json'}
    response = requests.put(url, json.dumps(application_dict), headers=headers)
    if response.status_code == 200:
        data = response.json()
        reg_list = []
        for n in data['new_registrations']:
            reg_list.append(n)
        try:
            delete_from_worklist(session['worklist_id'])
        except Exception as error:
            logging.error(error)
            return render_template('error.html', error_msg=error), 500
    else:
        error = response.status_code
        logging.error(error)
        return render_template('error.html', error_msg=error), 500

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
    url = app.config['BANKRUPTCY_DATABASE_URL'] + '/registration/' + regn_no + '/' + 'amend'
    headers = {'Content-Type': 'application/json'}
    response = requests.put(url, json.dumps(application_dict), headers=headers)
    if response.status_code == 200:
        data = response.json()
        reg_list = []
        for n in data['new_registrations']:
            reg_list.append(n)
    else:
        error = response.status_code
        logging.error(error)
        return render_template('error.html', error_msg=error), 500

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
                           images=image_list, current_page=0, original_image_data=session['original_image_data'])


# TODO: renamed as 'complete', move to back-end?
def delete_from_worklist(application_id):
    url = app.config['CASEWORK_DB_URL'] + '/workitem/' + application_id
    response = requests.delete(url)
    if response.status_code != 204:
        error = 'Failed to delete application ' + application_id + ' from the worklist. Error code:' \
                + str(response.status_code)

        logging.error(error)
        raise RuntimeError(error)


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


@app.route('/amend_address/<addr>', methods=["GET"])
def show_address(addr):
    application_type = session['application_type']
    application_dict = session['application_dict']
    image_list = session['images']

    if addr == 'new':
        address = addr
    else:
        address = int(addr)

    return render_template('regn_address.html', application_type=application_type, data=application_dict,
                           images=image_list, current_page=0, addr=address)


@app.route('/update_address/<addr>', methods=["POST"])
def update_address_details(addr):
    application_type = session['application_type']
    application_dict = session['application_dict']
    image_list = session['images']

    address = {'address_lines': []}
    if 'address1' in request.form and request.form['address1'] != '':
        address['address_lines'].append(request.form['address1'])
    if 'address2' in request.form and request.form['address2'] != '':
        address['address_lines'].append(request.form['address2'])
    if 'address3' in request.form and request.form['address3'] != '':
        address['address_lines'].append(request.form['address3'])
    if 'address4' in request.form and request.form['address4'] != '':
        address['address_lines'].append(request.form['address4'])
    if 'address5' in request.form and request.form['address5'] != '':
        address['address_lines'].append(request.form['address5'])
    if 'address6' in request.form and request.form['address6'] != '':
        address['address_lines'].append(request.form['address6'])

    address['county'] = request.form['county']
    address['postcode'] = request.form['postcode']
    if addr == 'new':
        application_dict['residence'].append(address)
    else:
        application_dict['residence'][int(addr)] = address

    return render_template('regn_amend.html', application_type=application_type, data=application_dict,
                           images=image_list, current_page=0, original_image_data=session['original_image_data'])


@app.route('/remove_address/<int:addr>', methods=["GET"])
def remove_address(addr):
    application_type = session['application_type']
    application_dict = session['application_dict']
    image_list = session['images']

    del (application_dict['residence'][addr])

    return render_template('regn_amend.html', application_type=application_type, data=application_dict,
                           images=image_list, current_page=0, original_image_data=session['original_image_data'])


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
    del (application_dict['debtor_alternative_name'][name])

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
                           images=image_list, current_page=0, original_image_data=session['original_image_data'])


@app.route('/process_banks_name', methods=["POST"])
def process_banks_name():
    try:
        appn_type = session['application_dict']['application_type']
        doc_id = session['document_id']
        name = {"debtor_name": {"forenames": [], "surname": ""},
                "occupation": "",
                "debtor_alternative_name": [],
                "residence": []
                }
        alt_name = {"forenames": [],
                    "surname": ""
                    }

        forenames = request.form['forename']
        for i in forenames.split():
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
        session['application_dict'] = name
        session['application_dict']['application_type'] = appn_type
        session['application_dict']['document_id'] = doc_id
        application = session['application_dict']

        return render_template('address.html', application=application, images=images,
                               requested_list=requested_worklist, current_page=0)

    except Exception as error:
        logging.error(error)
        return render_template('error.html', error_msg=error), 500


@app.route('/court_details', methods=["POST"])
def process_court_details():
    try:
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
            for n in data['new_registrations']:
                reg_list.append(n)
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

    except Exception as error:
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
    # application_type will be type of application being performed e.g. 'amend'
    application_type = session['application_type']
    # appn_type will be type of bankruptcy being processed i.e. PAB or WOB
    appn_type = session['application_dict']['application_type']
    doc_id = session['document_id']

    name = {"debtor_name": {"forenames": [], "surname": ""},
            "occupation": "",
            "debtor_alternative_name": [],
            "residence": []
            }
    alt_name = {"forenames": [],
                "surname": ""
                }

    forenames = request.form['forenames']
    for i in forenames.split():
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

    application_dict = name

    addr1_var = "address1"
    addr2_var = "address2"
    addr3_var = "address3"
    county_var = "county"
    postcode_var = "postcode"
    counter = 0
    while True:
        addr1_counter = addr1_var + str(counter)
        addr2_counter = addr2_var + str(counter)
        addr3_counter = addr3_var + str(counter)
        county_counter = county_var + str(counter)
        postcode_counter = postcode_var + str(counter)
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
    application_dict['document_id'] = doc_id
    session['application_dict'] = application_dict

    return render_template('rect_summary.html', application_type=application_type, data=application_dict,
                           date='')


@app.route('/process_search/<search_type>', methods=['POST'])
def process_search(search_type):

    # TODO: add validation here for name and search period
    search_names = []

    name = {"full_name": " ", "forename": " ", "surname": " "}
    name_var = "fullname"
    counter = 0
    while True:
        name_counter = name_var + str(counter)
        if name_counter in request.form and request.form[name_counter] != '':
            name['full_name'] = request.form[name_counter].strip().upper()
        else:
            break

        search_names.append(name)
        name = {"full_name": " ", "forename": " ", "surname": " "}
        counter += 1

    search_data = {}
    search = search_type
    search_data['search_type'] = search
    search_period = []
    if search_type == 'full':
        # TODO: next 4 lines to be removed when front-end hooked up
        # my_counties = {"counties": ['all']}
        my_counties = {"counties": ['Devon ', ' Cornwall', 'Dorset', 'Lancashire']}
        my_counties['counties'] = list(map(str.strip, my_counties['counties']))
        my_counties['counties'] = [element.upper() for element in my_counties['counties']]

        # TODO: kept this code in but commented out as might need similar later
        # counties_var = "('" + "', '".join((str(n) for n in my_counties['counties'])) + "')"

        # TODO: remove the line below when front-end there and uncomment the 3 lines below
        search_data['counties'] = my_counties['counties']
        # county_search['counties'] = map(str.strip, request.form['counties'])
        # county_search['counties'] = list(map(str.strip, county_search['counties']))
        # county_search['counties'] = [element.upper() for element in county_search['counties']]
        search = {"year_from": " ", "year_to": " "}
        yr_from_var = "year_from"
        yr_to_var = "year_to"
        counter = 0
        yr_from_counter = yr_from_var + str(counter)
        yr_to_counter = yr_to_var + str(counter)
        while yr_from_counter in request.form:
            search['year_from'] = request.form[yr_from_counter]
            search['year_to'] = request.form[yr_to_counter]
            search_period.append(search)
            search = {"year_from": " ", "year_to": " "}
            counter += 1
            yr_from_counter = yr_from_var + str(counter)
            yr_to_counter = yr_to_var + str(counter)

    search_results = {}
    counter = 0
    for names in search_names:
        if names['full_name'] == " ":
            fullname = names['forenames'] + ' ' + names['surname']
            search_data["forename"] = names['forenames']
            search_data["surname"] = names['surname']
        else:
            fullname = names['full_name']
            search_data["full_name"] = names['full_name']

        if search_type == 'full':
            search_data['year_from'] = search_period[counter]['year_from']
            search_data['year_to'] = search_period[counter]['year_to']
        counter += 1

        print("search data is", search_data)

        url = app.config['BANKRUPTCY_DATABASE_URL'] + '/search'
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, data=json.dumps(search_data), headers=headers)
        if response.status_code == 200:
            data = response.json()
            search_results[fullname] = data
            print("the search results are", search_results)
        else:
            print('failed for :', name, response.status_code)

    return render_template('confirmation.html')


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
    pabs, wobs, banks, lcreg, amend, canc, portal, search, oc = (0,) * 9

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
                oc += 1

    return {
        'pabs': pabs,
        'wobs': wobs,
        'banks': banks,
        'lcreg': lcreg,
        'amend': amend,
        'canc': canc,
        'portal': portal,
        'search': search,
        'oc': oc
    }


def page_required(appn_type):
    html_page = {
        "amend": "regn_retrieve.html",
        "cancel": "regn_retrieve.html",
        "bank_regn": "application.html",
        "search": "search_capture.html",
        "oc": "regn_retrieve.html",
        "lc": "application.html"
    }

    return html_page.get(appn_type)
