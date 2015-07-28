from application import app
from flask import render_template
import requests

@app.route('/', methods=["GET"])
def index():

    url = app.config['CASEWORK_DB_URL'] + '/work_list/all?'
    response = requests.get(url)
    full_list = response.json()

    # initialise all counters to 0
    pabs, wobs, lcreg, amend, canc, portal, search, oc = (0,)*8

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

    data = {
        'pabs': pabs,
        'wobs': wobs,
        'lcreg': lcreg,
        'amend': amend,
        'canc': canc,
        'portal': portal,
        'search': search,
        'oc': oc
    }
    return render_template('totals.html', data=data)

