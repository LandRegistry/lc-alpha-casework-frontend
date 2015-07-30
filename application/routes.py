from application import app
from flask import request, render_template
import requests
from datetime import datetime
import logging

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

        return render_template('application.html', requested_list=requested_worklist, data=application_json)

    except Exception as error:
        logging.error(error)
        return render_template('error.html', error_msg=error)


def get_totals():

    # initialise all counters to 0
    pabs, wobs, lcreg, amend, canc, portal, search, oc = (0,)*8

    url = app.config['CASEWORK_DB_URL'] + '/work_list/all?'
    response = requests.get(url)

    if response.status_code == 200:
        full_list = response.json()

        for item in full_list:
            if item['work_type'] == "bank_regn" and item['application_type'] == "PA(B)":
                pabs += 1
            elif item['work_type'] == "bank_regn" and item['application_type'] == "WO(B)":
                wobs += 1
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
        'lcreg': lcreg,
        'amend': amend,
        'canc': canc,
        'portal': portal,
        'search': search,
        'oc': oc
    }

