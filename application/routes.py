from application import app
from flask import request, Response, render_template, session
import requests
from datetime import datetime
import logging
import json
import ast


@app.route('/', methods=["GET"])
def index():

    try:
        data = get_totals()
        return render_template('totals.html', data=data)
    except Exception as error:
        logging.error(error)
        return render_template('error.html', error_msg=error)


@app.route('/get_list', methods=["GET"])
def get_list():

    try:
        requested_worklist = request.args.get('appn')

        url = app.config['CASEWORK_DB_URL'] + '/work_list/' + requested_worklist
        print(url)

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
        return render_template('error.html', error_msg=error)


@app.route('/get_application/<application_type>/<appn_id>', methods=["GET"])
def get_application(application_type, appn_id):

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

        if application_type == "amend" or application_type == "cancel":
            template = 'regn_retrieve.html'
        else:
            template = 'application.html'

        return render_template(template, application_type=application_type, data=application_json,
                               images=images,
                               current_page=0)

    except Exception as error:
        logging.error(error)
        return render_template('error.html', error_msg=error)


@app.route('/get_details', methods=["POST"])
def get_bankruptcy_details():

    try:
        application_type = request.form['application_type']
        regn_no = request.form['reg_no']

        url = app.config['BANKRUPTCY_DATABASE_URL'] + '/registration/' + regn_no

        response = requests.get(url)

        image_details = [
            "http://localhost:5014/document/9/image/1",
            "http://localhost:5014/document/9/image/2",
            "http://localhost:5014/document/9/image/3",
            ]

        if response.status_code == 404:
            error_msg = "Registration not found please re-enter"
            if application_type == "amend" or application_type == "cancel":
                template = 'regn_retrieve.html'
            else:
                template = 'application.html'

            return render_template(template, application_type=application_type,
                                   error_msg=error_msg, images=image_details, current_page=0)

        else:
            application_json = response.json()

            #  json missing court details at the moment, waiting for Ian to redesign the database to include them
            #  Will hard code for now
            application_json['court_name'] = "Liverpool"
            application_json['court_number'] = "523 / 15"

        return render_template('regn_details.html', application_type=application_type, data=application_json,
                               images=image_details, current_page=0)

    except Exception as error:
        logging.error(error)
        return render_template('error.html', error_msg=error)

@app.route('/process_request', methods=["POST"])
def process_request():

    application_type = request.form['application_type']

    # convert application the application retrieved from the request from a string to a dict
    application_dict = ast.literal_eval(request.form['application'])

    # convert application the application retrieved from the request from a string to a dict
    image_list = eval(request.form['images'])

    if 'Amend' in request.form:
        template = 'regn_amend.html'
    elif 'Continue' in request.form:
        template = 'regn_details.html'
    else:
        template = 'regn_details.html'

    return render_template(template, application_type=application_type, data=application_dict,
                           images=image_list, current_page=0)


@app.route('/process_banks_name', methods=["POST"])
def process_banks_name():

    try:
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
            except:
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

        return render_template('address.html', application=json.dumps(name), images=images,
                               requested_list=requested_worklist, current_page=1)

    except Exception as error:
        logging.error(error)
        return render_template('error.html', error_msg=error)


@app.route('/court_details', methods=["POST"])
def process_court_details():

    try:
        application = json.loads(request.form['application'])
        application["application_type"] = request.form['nature']
        application["court_name"] = request.form['court']
        application["court_ref"] = request.form['court_ref']

        # these are needed at the moment for registration but are not captured on the form
        application["key_number"] = "2244095"
        application["application_ref"] = "customer reference"
        today = datetime.now().strftime('%Y-%m-%d')
        application["date"] = today
        application["residence_withheld"] = False
        application['date_of_birth'] = "1980-01-01"

        url = app.config['BANKRUPTCY_DATABASE_URL'] + '/register'
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, data=json.dumps(application), headers=headers)

        if response.status_code == 200:
            data = response.json()
            reg_list = []
            for n in data['new_registrations']:
                reg_list.append(n)
            requested_worklist = 'bank_regn'
            display_date = datetime.now().strftime('%d.%m.%Y')
            return render_template('confirmation.html', application=application, data=reg_list, date=display_date,
                                   requested_list=requested_worklist)
        else:
            print("failed with", response.status_code)
            error = response.status_code
            logging.error(error)
            return render_template('error.html', error_msg=error)

    except Exception as error:
        logging.error(error)
        return render_template('error.html', error_msg=error)


@app.route('/address', methods=['POST'])
def application_step_2():
    application = json.loads(request.form['application'])
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

    address['address_lines'].append(request.form['county'])
    address['postcode'] = request.form['postcode']
    application['residence'].append(address)
    requested_worklist = 'bank_regn'

    if 'add_address' in request.form:
        return render_template('address.html', application=json.dumps(application), images=[
            "http://localhost:5014/document/9/image/1",
            "http://localhost:5014/document/9/image/2",
            "http://localhost:5014/document/9/image/3",
        ], residences=application['residence'], requested_list=requested_worklist, current_page=0)
    else:
        return render_template('banks_order.html', application=json.dumps(application),
                               images=[
                                   "http://localhost:5014/document/9/image/1",
                                   "http://localhost:5014/document/9/image/2",
                                   "http://localhost:5014/document/9/image/3", ],
                               requested_list=requested_worklist, current_page=0)


def get_totals():

    # initialise all counters to 0
    pabs, wobs, banks, lcreg, amend, canc, portal, search, oc = (0,)*9

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

