from application import app
from flask import request, Response, render_template
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
        return render_template('error.html', error_msg=error)


@app.route('/idea', methods=['GET'])
def idea():
    return render_template('idea.html')

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


@app.route('/get_application/<requested_worklist>/<appn_id>', methods=["GET"])
def get_application(requested_worklist, appn_id):

    try:
        url = app.config['CASEWORK_DB_URL'] + '/search/' + appn_id

        response = requests.get(url)

        application_json = response.json()

        # reformat dates to dd Month yyyy
        date = datetime.strptime(application_json['date'], "%Y-%m-%d")
        application_json['date'] = "{:%d %B %Y}".format(date)
        date = datetime.strptime(application_json['date_of_birth'], "%Y-%m-%d")
        application_json['date_of_birth'] = "{:%d %B %Y}".format(date)

        return render_template('application.html', requested_list=requested_worklist, appn_id=appn_id,
                               data=application_json,
                               images=[
                                   "http://localhost:5014/document/9/image/1",
                                   "http://localhost:5014/document/9/image/2",
                                   "http://localhost:5014/document/9/image/3",
                               ],
                               current_page=0)

    except Exception as error:
        logging.error(error)
        return render_template('error.html', error_msg=error)


@app.route('/process_banks_name', methods=["POST"])
def process_banks_name():

    try:
        name = {"debtor_name": {"forenames": [], "surname": ""},
                "occupation": "",
                "debtor_alternative_name": []
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
            name['debtor_alternative_name'].append(alt_name)
            alt_name = {"forenames": [], "surname": ""}
            counter += 1

        requested_worklist = 'bank_regn'

        return render_template('address.html', images=[
                               "http://localhost:5014/document/9/image/1",
                               "http://localhost:5014/document/9/image/2",
                               "http://localhost:5014/document/9/image/3",
                               ], requested_list=requested_worklist, current_page=1)

    except Exception as error:
        logging.error(error)
        return render_template('error.html', error_msg=error)


@app.route('/court_details', methods=["POST"])
def process_court_details():

    try:
        charge_details = {
            "application_type": request.form['nature'],
            "court_name": request.form['court'],
            "court_ref": request.form['court_ref']
        }
        requested_worklist = 'bank_regn'

        return render_template('confirmation.html', requested_list=requested_worklist, current_page="thumbnail_3")

    except Exception as error:
        logging.error(error)
        return render_template('error.html', error_msg=error)


@app.route('/address', methods=['POST'])
def application_step_2():
    application_json = {}  # TODO: will contain body
    return render_template('banks_order.html', data=application_json,
                           images=[
                               "http://localhost:5014/document/9/image/1",
                               "http://localhost:5014/document/9/image/2",
                               "http://localhost:5014/document/9/image/3",
                           ],
                           current_page=0)


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
                amend += 1
            elif item['work_type'] == "prt_search":
                amend += 1
            elif item['work_type'] == "search":
                amend += 1
            elif item['work_type'] == "oc":
                amend += 1

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

