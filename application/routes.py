from application import app
from application.logformat import format_message
from flask import Response, request, render_template, session, redirect, url_for, send_file, make_response
from datetime import datetime
import logging
import json
import re
import requests
import os
from application.form_validation import validate_land_charge
from application.land_charge import build_lc_inputs, build_customer_fee_inputs, submit_lc_registration
from application.search import process_search_criteria
from application.rectification import convert_response_data, submit_lc_rectification, convert_class_of_charge
from application.cancellation import submit_lc_cancellation
from application.banks import get_debtor_details, register_bankruptcy, get_original_data, build_original_data, \
    build_corrections, register_correction
from application.headers import get_headers
from application.auth import authenticate
from application.http import http_get, http_delete, http_post, http_put
from application.error import CaseworkFrontEndError
from io import BytesIO
import uuid
from functools import wraps
import traceback


@app.errorhandler(Exception)
def error_handler(err):
    logging.error('========== Error Caught ===========')
    logging.error(err)

    call_stack = traceback.format_exc()
    lines = call_stack.split("\n")[0:-2]
    edata = None


    try:
        edata = json.loads(str(err))
    except ValueError as e:
        pass

    if edata:
        error = {
            "dict": {
                "stack": lines,
                "dict": edata
            }
        }

        if 'text' in edata:
            error['message'] = edata['text']

    else:
        error = {
            "message": str(err),
            "dict": {
                "stack": lines
            }
        }

    # logging.info(lines)
    # logging.info('=======================================')
    # logging.info(json.dumps(error, indent=2))
    # logging.info('=======================================')
    return render_template('error.html', error_msg=error, status=500)


@app.before_request
def before_request():
    # tid = "T:" + session['transaction_id'] if 'transaction_id' in session else ''
    # logging.info("%s %s %s [%s]",
    #              tid, request.method, request.url, request.remote_addr)
    pass


@app.after_request
def after_request(response):
    # tid = "T:" + session['transaction_id'] if 'transaction_id' in session else ''
    # logging.info('%s %s %s [%s] -- %s',
    #              tid, request.method, request.url, request.remote_addr,
    #              response.status)
    return response


def go_to_login():
    return redirect("/login")


def go_to_home():
    return redirect("/")


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session or session['username'] == '':
            logging.debug("Login required")
            return go_to_login()
        return f(*args, **kwargs)

    return decorated


def requires_auth_role(roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'username' not in session or session['username'] == '':
                logging.debug("Login required")
                return go_to_login()

            if 'role' not in session:
                logging.debug("No role allocated")
                return go_to_home()

            if session['role'] not in roles:
                logging.debug("Invalid role %s for method", session['role'])
                logging.debug(roles)
                return go_to_home()

            return func(*args, **kwargs)
        return wrapper
    return decorator


def clear_session():
    username = session['username']
    display = session['display_name']
    role = session['role']
    session.clear()
    session['username'] = username
    session['display_name'] = display
    session['role'] = role


@app.route("/logout", methods=["GET"])
def logout():
    logging.info(format_message("User %s logged out"), session['username'])
    session.clear()
    return redirect("/login")


@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html", errors=False)


@app.route("/login_failed", methods=["GET"])
def login_failed():
    return render_template("login.html", errors=True)


@app.route("/login", methods=["POST"])
def login_as_user():
    username = request.form['username']
    password = request.form['password']
    auth = authenticate(username, password)

    if not auth:
        logging.info(format_message("Login failed for user %s"), username)
        return redirect("/login_failed")
    else:
        session['username'] = auth['username']
        session['display_name'] = auth['display_name']

        # roles = {
        #     os.getenv('CASEWORKER_GROUP', 'casework_group'): 'normal',
        #     os.getenv('ADMIN_GROUP', 'not specified'): 'normal',
        #     os.getenv('REPRINT_GROUP', 'reprint_group'): 'reprint'
        # }

        if auth['primary_group'] == os.getenv('CASEWORKER_GROUP', 'casework_group'):
            session['role'] = 'normal'
        elif auth['primary_group'] == os.getenv('ADMIN_GROUP', 'not specified'):
            session['role'] = 'normal'
        elif auth['primary_group'] == os.getenv('REPRINT_GROUP', 'reprint_group'):
            session['role'] = 'reprint'
        else:
            session['role'] = 'none'

        # if auth['primary_group'] in roles:
        #     session['role'] = roles[auth['primary_group']]
        # else:
        #     session['role'] = 'none'

        logging.info(format_message("Login successful for user %s"), username)
        return redirect("/")


@app.route('/', methods=["GET"])
@requires_auth
def index():
    if 'transaction_id' in session:
        logging.info(format_message('End transaction %s'), session['transaction_id'])
        del(session['transaction_id'])

    if 'worklist_id' in session:
        url = app.config['CASEWORK_API_URL'] + '/applications/' + session['worklist_id'] + '/lock'
        http_delete(url, headers=get_headers({'X-Transaction-ID': session['worklist_id']}))
        del(session['worklist_id'])

    data = get_totals()
    return render_template('work_list/totals.html', data=data)


@app.route('/get_list', methods=["GET"])
@requires_auth_role(['normal'])
def get_list():
    if 'transaction_id' in session:
        logging.info(format_message('End transaction %s'), session['transaction_id'])
        del(session['transaction_id'])

    # check if confirmation or rejection message is required
    if 'confirmation' in session:
        result = session['confirmation']
        del(session['confirmation'])
    elif 'rejection' in session:
        result = {'rejection': True}
        del(session['rejection'])
    else:
        result = {}

    if 'worklist_id' in session:
        url = app.config['CASEWORK_API_URL'] + '/applications/' + session['worklist_id'] + '/lock'
        http_delete(url, headers=get_headers({'X-Transaction-ID': session['worklist_id']}))
        del(session['worklist_id'])

    return get_list_of_applications(request.args.get('appn'), result, "")


def get_list_of_applications(requested_worklist, result, error_msg):
    logging.info('--- GET LIST OF APPLICATIONS ---')
    logging.info(requested_worklist)

    return_page = ''
    if requested_worklist.startswith('bank'):
        return_page = 'work_list/bank.html'
    elif requested_worklist.startswith('lc'):
        return_page = 'work_list/lc.html'
    elif requested_worklist.startswith('search'):
        return_page = 'work_list/search.html'
    elif requested_worklist.startswith('canc'):
        return_page = 'work_list/cancel.html'
    elif requested_worklist.startswith('unknown'):
        return_page = 'work_list/unknown.html'
    appn_list = []

    # This is going to be fragile - depends on the internal strings identifying worklists
    # being slightly consistent...
    m = re.search("(.*)_stored", requested_worklist)
    if m is not None:
        prefix = m.group(1)
        url = app.config['CASEWORK_API_URL'] + '/applications?state=stored'
        response = http_get(url, headers=get_headers())
        work_list_json = response.json()

        for item in work_list_json:
            if prefix in item['work_type']:
                date = datetime.strptime(item['date_received'], "%Y-%m-%d %H:%M:%S")
                application = {
                    "appn_id": item['appn_id'],
                    "received_tmstmp": item['date_received'],
                    "date_received": "{:%d %B %Y}".format(date),
                    "time_received": "{:%H:%M}".format(date),
                    "application_type": item['application_type'],
                    "status": item['status'],
                    "work_type": item['work_type'],
                    "stored_by": item['stored_by'],
                    "store_reason": item['store_reason'],
                    "delivery_method": item['delivery_method']
                }
                appn_list.append(application)
    else:
        url = app.config['CASEWORK_API_URL'] + '/applications?type=' + requested_worklist + '&state=NEW'
        response = http_get(url, headers=get_headers())
        work_list_json = response.json()

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
                    "work_type": appn['work_type']
                }
                if requested_worklist.startswith('search'):
                    application['delivery_method'] = appn['delivery_method']

                appn_list.append(application)

    app_totals = get_totals()

    # Courtesy of the Intenet; seems to fix the issue where /get_list isn't called on navigating
    # "back" from an input form. This was leaving applications locked.
    resp = make_response(render_template(return_page, worklist=appn_list, requested_list=requested_worklist,
                                         data=app_totals, error_msg=error_msg, result=result))
    resp.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@app.route('/application_start/<application_type>/<appn_id>/<form>', methods=["GET"])
@requires_auth_role(['normal'])
def application_start(application_type, appn_id, form):

    url = app.config['CASEWORK_API_URL'] + '/applications/' + appn_id
    response = http_get(url, headers=get_headers())
    application_json = response.json()
    stored = application_json['stored']
    if stored:
        application_type = application_json['application_data']['application_type']
        form = application_json['application_data']['application_dict']['form']
        stored_template = application_json['application_data']['page_template']

    # Lock application if not in session otherwise assume user has refreshed the browser after select an application
    if 'worklist_id' not in session:
        url = app.config['CASEWORK_API_URL'] + '/applications/' + appn_id + '/lock'
        session['transaction_id'] = appn_id
        response = http_post(url, headers=get_headers({'X-Transaction-ID': appn_id}))
        if response.status_code == 404:
            error_msg = "This application is being processed by another member of staff, " \
                        "please select a different application."
            result = {}
            return get_list_of_applications(application_type, result, error_msg)

    logging.debug(application_json)
    document_id = application_json['application_data']['document_id']
    doc_response = get_form_images(document_id)
    images = []
    image_data = json.loads(doc_response[0])
    for page in image_data['images']:
        url = "/images/" + str(document_id) + '/' + str(page['page'])
        images.append(url)

    template = page_required(application_type, form)

    application_json['form'] = form

    clear_session()
    if stored:
        # Load stored stuff into session...
        for key in application_json['application_data']:
            session[key] = application_json['application_data'][key]
        session['transaction_id'] = appn_id
        logging.info(format_message("Resume %s Application"), form)
        # get_registration_details()

    else:
        set_session_variables({'images': images, 'document_id': document_id,
                               'application_type': application_type, 'worklist_id': appn_id,
                               'application_dict': application_json, 'transaction_id': appn_id})
        logging.info(format_message("Start %s Application"), form)

    application = session['application_dict']

    years = {"year_from": "1925",
             "year_to": datetime.now().strftime('%Y')
             }

    # land charge input data required for validation on lc_regn/capture.html
    if 'register_details' in session:
        curr_data = session['register_details']
    elif 'rectification_details' in session:
        curr_data = session['rectification_details']
    else:
        curr_data = build_lc_inputs({})

    session['page_template'] = template  # Might need this later

    logging.debug('---- START RENDER TEMPLATE DATA ----')
    logging.debug(json.dumps(application_json))

    if stored:
        screen = ''
        date = ''
        if application_type == 'cancel':
            logging.debug('---- RESTORING A CANCELLATION ----')
            date = re.sub("(\d{4})\-(\d+)\-(\d\d)", r"\3/\2/\1", application_json['application_data']['reg_date'])
            return render_template('cancellation/canc_retrieve.html', application_type=application_type,
                                   images=session['images'], current_page=0,
                                   reg_no=application_json['application_data']['regn_no'], reg_date=date,
                                   transaction=session['transaction_id'])

        elif application_type == 'bank_amend':  # Tiresome special case, skip the PAB WOB screen...
            if 'retrieve' in stored_template:
                return render_template('bank_amend/retrieve.html', images=session['images'], current_page=0,
                                       data=application_json['application_data'], application=session)
            else:
                return render_template('bank_amend/amend_details.html', images=session['images'], current_page=0,
                                       data=session, application=session, screen='capture',
                                       transaction=session['transaction_id'])

        elif application_type == 'lc_rect' or application_type == 'lc_renewal':
            if application_json['application_data']['reg_date'] == '':
                date = ''
            else:
                date = re.sub("(\d{4})\-(\d+)\-(\d\d)", r"\3/\2/\1", application_json['application_data']['reg_date'])
            reg_no = application_json['application_data']['regn_no']
            template = stored_template
            return render_template(template, application_type=application_type,
                                   data=application_json, images=images, reg_date=date, reg_no=reg_no,
                                   application=application, details=curr_data,
                                   screen=screen, curr_data=curr_data, errors=[],
                                   current_page=0, transaction=session['transaction_id'])

        elif application_type.startswith('search'):
            return render_template(template, application_type=application_type, data=application_json,
                                   images=images, application=application, years=years,
                                   current_page=0, errors=[], curr_data=curr_data, transaction=session['transaction_id'])

        return render_template(template, application_type=application_type,
                               data=application_json, images=images, date=date,
                               application=application, details=curr_data,
                               screen=screen, curr_data=curr_data, errors=[],
                               current_page=0, transaction=session['transaction_id'])

    return render_template(template, application_type=application_type, data=application_json,
                           images=images, application=application, years=years,
                           current_page=0, errors=[], curr_data=curr_data, transaction=session['transaction_id'])


@app.route('/retrieve_new_reg', methods=["GET"])
@requires_auth_role(['normal'])
def retrieve_new_reg():
    return redirect('/application_start/%s/%s/%s' % (session['application_type'], session['worklist_id'],
                    session['application_dict']['form']), code=302, Response=None)


# ======Banks Registration routes===========

@app.route('/check_court_details', methods=["POST"])
@requires_auth_role(['normal'])
def check_court_details():

    if 'store' in request.form:
        application = {"legal_body":  request.form['court'],
                       "legal_body_ref_no": request.form['ref_no']}
        session['court_info'] = application
        return store_application()

    if request.form['submit_btn'] == 'No':
        return render_template('bank_regn/assoc_image.html', images=session['images'], current_page=0,
                               curr_data=session['current_registrations'], error=' ')

    elif request.form['submit_btn'] == 'Yes' and \
        session['court_info']['legal_body'] == request.form['court'] and \
            session['court_info']['legal_body_ref_no'] == request.form['ref_no']:

        session['current_registrations'] = []
        if 'return_to_verify' in request.form:
            return render_template('bank_regn/verify.html', images=session['images'], current_page=0,
                                   court_data=session['court_info'], party_data=session['parties'])
        else:
            return render_template('bank_regn/debtor.html', images=session['images'], current_page=0, data=session)
    else:

        application = {"legal_body":  request.form['court'],
                       "legal_body_ref_no": request.form['ref_no']}
        session['court_info'] = application

        legal_body_ref = application['legal_body'] + ' ' + application['legal_body_ref_no']
        legal_body_ref = legal_body_ref.strip()
        #  call api to see if registration already exists
        url = app.config['CASEWORK_API_URL'] + '/court_check/' + legal_body_ref

        response = http_get(url, headers=get_headers())
        if response.status_code == 200:
            session['current_registrations'] = json.loads(response.text)
            return render_template('bank_regn/official.html', images=session['images'], current_page=0,
                                   data=session['court_info'], application=session,
                                   current_registrations=session['current_registrations'],
                                   transaction=session['transaction_id'])
        elif response.status_code == 404:
            session['current_registrations'] = []
            if 'return_to_verify' in request.form:
                return render_template('bank_regn/verify.html', images=session['images'], current_page=0,
                                       court_data=session['court_info'], party_data=session['parties'])
            else:
                return redirect("/debtor")
                # return render_template('bank_regn/debtor.html',
                # images=session['images'], current_page=0, data=session)
        else:
            err = 'Failed to process bankruptcy registration application id:%s - Error code: %s' \
                  % (session['worklist_id'], str(response.status_code))
            logging.error(format_message(err))
            return render_template('error.html', error_msg=err), response.status_code


@app.route("/debtor", methods=['GET'])
@requires_auth_role(['normal'])
def enter_debtor_details():
    return render_template('bank_regn/debtor.html', images=session['images'], current_page=0, data=session)


@app.route('/associate_image', methods=['POST'])
@requires_auth_role(['normal'])
def associate_image():
    reg = {'reg_no': request.form['reg_no_assoc'],
           'date': request.form['date_assoc'],
           'document_id': session['document_id'],
           'appn_id': session['worklist_id']}
    logging.debug(reg)

    url = app.config['CASEWORK_API_URL'] + '/assoc_image'
    response = http_put(url, json.dumps(reg), headers=get_headers())

    if response.status_code == 200:
        return redirect('/get_list?appn=bank_regn', code=302, Response=None)
    elif response.status_code == 404:
        err = 'Error 404 - Unable to associate the image for reg: %s and date %s. Please contact service desk.' \
              % (reg['reg_no'], reg['date'])
        logging.error(format_message(err))
        return render_template('error.html', error_msg=err), response.status_code
    else:
        err = 'Failed to process bankruptcy registration application id:%s - Error code: %s' \
              % (session['worklist_id'], str(response.status_code))
        logging.error(format_message(err))
        return render_template('error.html', error_msg=err), response.status_code


@app.route('/process_debtor_details', methods=['POST'])
@requires_auth_role(['normal'])
def process_debtor_details():
    logging.debug('PROCESS DEBTOR DETAILS')
    logging.debug(request.form)

    logging.info(format_message('processing debtor details'))

    session['parties'] = get_debtor_details(request.form)

    if 'store' in request.form:
        return store_application()

    return render_template('bank_regn/verify.html', images=session['images'], current_page=0,
                           court_data=session['court_info'], party_data=session['parties'],
                           transaction=session['transaction_id'])


@app.route('/bankruptcy_capture/<page>', methods=['GET'])
@requires_auth_role(['normal'])
def bankruptcy_capture(page):
    # For returning from verification screen

    if page == 'court':
        page_template = 'bank_regn/official.html'
        data = session['court_info']
    else:
        page_template = 'bank_regn/debtor.html'
        data = session['parties'][0]

    return render_template(page_template,
                           application_type=session['application_type'],
                           data=data,
                           images=session['images'],
                           current_page=0,
                           errors=[], from_verify=True, transaction=session['transaction_id'])


@app.route('/bankruptcy_capture/key_no', methods=['POST'])
@requires_auth_role(['normal'])
def bankruptcy_capture_key():

    if 'store' in request.form:
        return store_application()

    page_template = 'bank_regn/key_no.html'
    data = session

    return render_template(page_template,
                           application_type=session['application_type'],
                           data=data,
                           images=session['images'],
                           current_page=0,
                           errors=[], from_verify=True, transaction=session['transaction_id'])


@app.route('/submit_banks_registration', methods=['POST'])
@requires_auth_role(['normal'])
def submit_banks_registration():
    if 'store' in request.form:
        session['key_number'] = request.form['key_number']
        return store_application()

    logging.info(format_message('submitting banks registration'))
    key_number = request.form['key_number']

    # Check key_number is valid
    url = app.config['CASEWORK_API_URL'] + '/keyholders/' + key_number
    response = http_get(url, headers=get_headers())

    if response.status_code != 200:
        err = 'This Key number is invalid please re-enter'
        return render_template('bank_regn/key_no.html',
                               application_type=session['application_type'],
                               data=request.form,
                               images=session['images'],
                               current_page=0,
                               error_msg=err, transaction=session['transaction_id'])
    else:

        response = register_bankruptcy(key_number)

        if response.status_code == 400:
            error = response.text
            logging.error(format_message(error))
            return render_template('error.html', error_msg=json.loads(error)), response.status_code
        elif response.status_code != 200:
            err = 'Failed to submit bankruptcy registration application id:%s - Error code: %s' \
                  % (session['worklist_id'], str(response.status_code))
            logging.error(format_message(err))
            return render_template('error.html', error_msg=err), response.status_code
        else:
            return redirect('/get_list?appn=bank_regn', code=302, Response=None)


# =============== Amendment routes ======================

@app.route('/get_original_bankruptcy', methods=['POST'])
@requires_auth_role(['normal'])
def get_original_banks_details():

    if 'store' in request.form:
        session['wob'] = {'number': request.form['wob_ref'],
                          'date': request.form['wob_date']}
        session['pab'] = {'number': request.form['pab_ref'],
                          'date': request.form['pab_date']}
        return store_application()

    curr_data = []
    if request.form['wob_ref'] == '' and request.form['pab_ref'] == '':
        error_msg = 'A registration number must be entered'
    else:
        curr_data, error_msg, status_code, fatal = build_original_data(request.form)
        session['curr_data'] = curr_data
        if fatal:
            err = 'Failed to process bankruptcy amendment application id:%s - Error code: %s' \
                  % (session['worklist_id'], str(status_code))
            logging.error(format_message(err))
            return render_template('error.html', error_msg=err), status_code

    if error_msg != '':
        return render_template('bank_amend/retrieve.html', images=session['images'], current_page=0,
                               data=curr_data, application=session, error_msg=error_msg)
    else:
        if request.form['wob_ref'] == '' or request.form['pab_ref'] == '':
            # User has only entered one registration number so ok to proceed
            return redirect('/view_original_details')
        else:
            # User has entered both wob and pab numbers so display screen so user can check they have entered the
            # correct pab registration before amending it.
            return render_template('bank_amend/retrieve_with_data.html', images=session['images'], current_page=0,
                                   data=session['original_regns'], curr_data=curr_data, application=session,
                                   screen='capture', error=error_msg, transaction=session['transaction_id'])


@app.route('/re_enter_registration', methods=['GET'])
@requires_auth_role(['normal'])
def re_enter_registration():
    return render_template('bank_amend/retrieve.html', images=session['images'], current_page=0,
                           data=session['curr_data'], application=session, transaction=session['transaction_id'])


@app.route('/continue_amendment', methods=['POST'])
@requires_auth_role(['normal'])
def continue_amendment():
    return redirect('/view_original_details')


@app.route('/view_original_details', methods=['GET'])
@requires_auth_role(['normal'])
def view_original_details():
    if session['application_type'] == 'correction':
        template = 'corrections/correct_details.html'
    else:
        template = 'bank_amend/amend_details.html'

    return render_template(template, images=session['images'], current_page=0,
                           data=session['original_regns'], application=session, screen='capture',
                           transaction=session['transaction_id'])


@app.route('/remove_address/<int:addr>', methods=["POST"])
@requires_auth_role(['normal'])
def remove_address(addr):

    session['parties'] = get_debtor_details(request.form)
    # session['original_regns']['additional_information'] = request.form['add_info']
    session['original_regns']['parties'] = session['parties']

    if addr < len(session['original_regns']['parties'][0]['addresses']):
        del session['original_regns']['parties'][0]['addresses'][addr]
        session['data_amended'] = 'true'

    return redirect('/view_original_details', code=302, Response=None)


@app.route('/process_amended_details', methods=['POST'])
@requires_auth_role(['normal'])
def process_amended_details():

    session['parties'] = get_debtor_details(request.form)

    if 'store' in request.form:
        session['page_template'] = 'bank_amend/amend_details.html'
        return store_application()

    return render_template('bank_amend/check.html', images=session['images'], current_page=0,
                           data=session['parties'], transaction=session['transaction_id'])


@app.route('/amendment_capture', methods=['GET'])
@requires_auth_role(['normal'])
def amendment_capture():
    # For returning from check screen
    party_data = {'parties': session['parties']}

    return render_template('bank_amend/amend_details.html',
                           application_type=session['application_type'],
                           data=party_data,
                           images=session['images'],
                           current_page=0,
                           errors=[],
                           transaction=session['transaction_id'])


@app.route('/amendment_key_no', methods=['POST'])
@requires_auth_role(['normal'])
def amendment_key_no():

    if 'store' in request.form:
        session['page_template'] = 'bank_amend/amend_details.html'
        return store_application()

    return render_template('bank_amend/key_no.html',
                           application_type=session['application_type'],
                           data=session,
                           images=session['images'],
                           current_page=0,
                           errors=[],
                           transaction=session['transaction_id'])


@app.route('/submit_banks_amendment', methods=['POST'])
@requires_auth_role(['normal'])
def submit_banks_amendment():

    if 'store' in request.form:
        session['key_number'] = request.form['key_number']
        session['page_template'] = 'bank_amend/amend_details.html'
        return store_application()

    logging.info(format_message('submitting banks amendment'))
    key_number = request.form['key_number']

    # Check key_number is valid
    url = app.config['CASEWORK_API_URL'] + '/keyholders/' + key_number
    response = http_get(url, headers=get_headers())

    if response.status_code != 200:
        err = 'This Key number is invalid please re-enter'
        return render_template('bank_amend/key_no.html',
                               application_type=session['application_type'],
                               data=request.form,
                               images=session['images'],
                               current_page=0,
                               error_msg=err, transaction=session['transaction_id'])
    else:
        response = register_bankruptcy(key_number)

        if response.status_code != 200:
            err = 'Failed to submit bankruptcy amendment application id:%s - Error code: %s' \
                  % (session['worklist_id'], str(response.status_code))
            logging.error(err)
            return render_template('error.html', error_msg=err), response.status_code
        else:
            return redirect('/get_list?appn=bank_amend', code=302, Response=None)

# ===== end of amendment routes  ===========

# =============== Correction routes ======================


#  Do we need to set the transaction id here for logging later?????
@app.route('/correction', methods=['GET'])
@requires_auth_role(['normal'])
def start_correction():
    clear_session()
    return render_template("corrections/retrieve.html", reg_no="", reg_date="", result="")


@app.route('/get_original', methods=['POST'])
@requires_auth_role(['normal'])
def get_original_details():
    session['application_type'] = 'correction'
    curr_data = []
    if request.form['reg_no'] == '' or request.form['reg_date'] == '':

        error_msg = 'A registration number and date must be entered'
    else:
        request_data = {'reg_no': request.form['reg_no'],
                        'reg_date': request.form['reg_date']}

        session['transaction_id'] = uuid.uuid4().int  # consider fields[0] if the int is too long; it *should* be OK

        error_msg, status_code, fatal = build_corrections(request_data)
        session['curr_data'] = session['details_entered']

        if fatal:
            err = 'Failed to process correction for %s dated %s - Error code: %s' \
                  % (request.form['reg_no'], request.form['reg_date'], str(status_code))
            logging.error(format_message(err))
            return render_template('error.html', error_msg=err), status_code

    if error_msg != '':
        return render_template('corrections/retrieve.html', data=curr_data, application=session, error_msg=error_msg)
    else:
        return render_template('corrections/correct_details.html',
                               data=session['original_regns'], application=session, screen='capture',
                               transaction=session['transaction_id'])


@app.route('/process_corrected_details', methods=['POST'])
@requires_auth_role(['normal'])
def process_corrected_details():
    session['parties'] = get_debtor_details(request.form)
    return render_template('corrections/check.html', data=session['parties'], transaction=session['transaction_id'])


@app.route('/correction_capture', methods=['GET'])
@requires_auth_role(['normal'])
def correction_capture():
    # For returning from check screen
    party_data = {'parties': session['parties']}

    return render_template('corrections/correct_details.html',
                           application_type=session['application_type'],
                           data=party_data,
                           errors=[],
                           transaction=session['transaction_id'])


@app.route('/submit_banks_correction', methods=['POST'])
@requires_auth_role(['normal'])
def submit_banks_correction():
    logging.info(format_message('submitting banks correction'))

    response = register_correction()

    if response.status_code != 200:
        err = 'Failed to submit bankruptcy correction for registration :%s dated  - Error code: %s' \
              % (session['original_regns']['registration']['number'], str(response.status_code))
        logging.error(err)
        return render_template('error.html', error_msg=err), response.status_code
    else:
        return render_template("corrections/retrieve.html", reg_no="", reg_date="", result="success")

# ===== end of correction routes  ===========


@app.route('/process_search_name/<application_type>', methods=['POST'])
@requires_auth_role(['normal'])
def process_search_name(application_type):

    process_search_criteria(request.form, application_type)

    if 'store' in request.form:
        return store_application()

    request_data = {}
    for k in request.form:
        request_data[k] = request.form[k]

    return render_template('searches/customer.html', images=session['images'], application=session['application_dict'],
                           application_type=session['application_type'], current_page=0,
                           backend_uri=app.config['CASEWORK_FRONTEND_URL'], data=request_data,
                           transaction=session['transaction_id'])


@app.route('/back_to_search_name', methods=['GET'])
@requires_auth_role(['normal'])
def back_to_search_name():
    return render_template('searches/info.html', images=session['images'], application=session['application_dict'],
                           application_type=session['application_type'], current_page=0,
                           backend_uri=app.config['CASEWORK_FRONTEND_URL'], transaction=session['transaction_id'])


@app.route('/submit_search', methods=['POST'])
@requires_auth_role(['normal'])
def submit_search():
    if 'store' in request.form:
        return store_application()

    logging.info(format_message('Submitting submit search'))
    cust_address = request.form['customer_address'].replace("\r\n", ", ").strip()
    customer = {
        'key_number': request.form['key_number'],
        'name': request.form['customer_name'],
        'address': cust_address,
        'address_type': request.form['address_type'],
        'reference': request.form['customer_ref']
    }

    search_data = {
        'customer': customer,
        'document_id': session['document_id'],
        'parameters': session['application_dict']['search_criteria'],
        'fee_details': {'type': request.form['payment'],
                        'fee_factor': len(session['application_dict']['search_criteria']['search_items']),
                        'delivery': session['application_dict']['delivery_method']}
    }

    session['search_data'] = search_data
    url = app.config['CASEWORK_API_URL'] + '/searches'
    headers = get_headers({'Content-Type': 'application/json'})
    response = http_post(url, data=json.dumps(search_data), headers=headers)

    if response.status_code == 200:
        search_response = response.json()
        set_session_variables({'search_result': search_response})
        delete_from_worklist(session['worklist_id'])
    elif response.status_code == 404:
        session['search_result'] = []
        delete_from_worklist(session['worklist_id'])
    else:
        logging.error(format_message('Unexpected return code: %d'), response.status_code)
        logging.error(format_message(response.text))
        return render_template('error.html', error_msg=response.text)

    session['confirmation'] = {'reg_no': []}

    if session['application_dict']['search_criteria']['search_type'] == 'full':
        return redirect('/get_list?appn=search_full', code=302, Response=None)
    else:
        return redirect('/get_list?appn=search_bank', code=302, Response=None)

# ===== end of search routes =========


# ======== Rectification routes =============
@app.route('/start_rectification', methods=["GET"])
@requires_auth_role(['normal'])
def start_rectification():
    session['application_type'] = "rectify"
    return render_template('rectification/retrieve.html')


@app.route('/get_details', methods=["POST"])
@requires_auth_role(['normal'])
def get_registration_details():

    application_type = session['application_type']

    if 'store' in request.form:
        session['regn_no'] = request.form['reg_no']
        if request.form['reg_date'] == '' or request.form['reg_date'] == ' ':
            session['reg_date'] = ''
        else:
            date_as_list = request.form['reg_date'].split("/")  # dd/mm/yyyy
            session['reg_date'] = '%s-%s-%s' % (date_as_list[2], date_as_list[1], date_as_list[0])
        return store_application()

    multi_reg_class = ""
    if "multi_reg_sel" in request.form:
        multi_reg_class = request.form['multi_reg_sel']

    logging.debug('---- GET DETAILS ----')
    logging.debug(request.form)

    session['regn_no'] = request.form['reg_no']

    date_as_list = request.form['reg_date'].split("/")  # dd/mm/yyyy
    session['reg_date'] = '%s-%s-%s' % (date_as_list[2], date_as_list[1], date_as_list[0])
    url = app.config['CASEWORK_API_URL'] + '/registrations/' + session['reg_date'] + '/' + session['regn_no']
    if multi_reg_class != "":
        url += "?class_of_charge=" + multi_reg_class
        session['class_of_charge'] = multi_reg_class

    response = http_get(url, headers=get_headers())
    error_msg = None
    if response.status_code == 404:
        error_msg = "Registration not found please re-enter"

    else:
        application_json = response.json()
        if application_json['status'] == 'cancelled' or application_json['status'] == 'superseded':
            error_msg = "Application has been cancelled or amended - please re-enter"
        elif 'amends_registration' in application_json:
            if application_json['amends_registration']['type'] == 'Cancellation':
                error_msg = "Registration has been cancelled - please re-enter"

    #  check if part cans has been selected for a bankruptcy
    application_json = response.json()
    if (error_msg is None) and (application_type == 'cancel'):
        session['cancellation_type'] = 'Cancellation'
        if request.form['full_cans'] == 'false':
            session['cancellation_type'] = 'Part Cancellation'
            class_of_charge = application_json['class']
            if class_of_charge in ['WO', 'PA', 'WOB', 'PAB', 'PA(B)', 'WO(B)']:
                error_msg = "You cannot part cancel a bankruptcy registration"
    elif (error_msg is None) and (application_type == 'lc_rect'):
        if application_json['class'] in ['WOB', 'PAB', 'PA(B)', 'WO(B)']:
            error_msg = "You cannot rectify a bankruptcy registration"

    if error_msg is not None:
        if application_type == 'lc_rect':
            template = 'rectification/retrieve.html'
        elif application_type == 'lc_renewal':
            template = 'renewal/retrieve.html'
        elif application_type == 'cancel':
            template = 'cancellation/canc_retrieve.html'
        else:
            template = 'regn_retrieve.html'
        return render_template(template, application_type=application_type,
                               error_msg=error_msg, images=session['images'], current_page=0,
                               reg_no=request.form['reg_no'], reg_date=request.form['reg_date'],
                               transaction=session['transaction_id'])
    else:
        data = response.json()
        # session['orig_addl_info'] = data['additional_info']  # A terrible hack, but we need to keep it somewhere
        # and hidden fields aren't being POSTed. Lovely.

        template = ''
        if application_type == 'lc_rect':
            template = 'rectification/amend.html'
        elif application_type == 'amend':
            template = 'regn_amend.html'
        elif application_type == 'lc_renewal':
            session['class_of_charge'] = application_json['class']
            template = 'renewal/check.html'
        elif application_type == 'cancel':
            data['full_cans'] = request.form['full_cans']
            template = 'cancellation/canc_check.html'
        return render_template(template, data=session['application_dict'],
                               images=session['images'], current_page=0, curr_data=data,
                               transaction=session['transaction_id'])


@app.route('/rectification_capture', methods=['POST'])
@requires_auth_role(['normal'])
def rectification_capture():

    result = validate_land_charge(request.form)
    entered_fields = build_lc_inputs(request.form)

    entered_fields['class'] = result['class']
    # entered_fields["additional_info"] = session['orig_addl_info']

    if "addl_info_type" in request.form:
        entered_fields["update_registration"] = {"type": "Rectification"}
        if request.form["addl_info_type"] == 'date_of_instrument':
            entered_fields["update_registration"]["instrument"] = {"original": "", "current": ""}

            if "orig_data" in request.form:
                entered_fields["update_registration"]["instrument"]["original"] = request.form["doi_orig_data"]
            if "current_data" in request.form:
                entered_fields["update_registration"]["instrument"]["current"] = request.form["doi_current_data"]

        elif request.form["addl_info_type"] == "chargee_details":
            entered_fields["update_registration"]["chargee"] = {"original": "", "current": ""}
            if "orig_data" in request.form:
                entered_fields["update_registration"]["chargee"]["original"] = request.form["orig_data"]
            if "current_data" in request.form:
                entered_fields["update_registration"]["chargee"]["current"] = request.form["current_data"]

    if 'store' in request.form:
        session['page_template'] = 'rectification/amend.html'
        session['rectification_details'] = entered_fields
        return store_application()

    if len(result['error']) == 0:
        session['rectification_details'] = entered_fields
        return render_template('rectification/check.html', application_type=session['application_type'], data={},
                               images=session['images'], application=session['application_dict'],
                               details=session['rectification_details'], screen='verify',
                               current_page=0, transaction=session['transaction_id'])
    else:
        return render_template('rectification/amend.html', application_type=session['application_type'],
                               images=session['images'], application=session['application_dict'],
                               current_page=0, errors=result['error'], curr_data=entered_fields,
                               screen='capture', data=session['application_dict'],
                               transaction=session['transaction_id'])


@app.route('/rectification_capture', methods=['GET'])
@requires_auth_role(['normal'])
def return_to_rectification_amend():
    # For returning from check rectification screen
    return render_template('rectification/amend.html',
                           application_type=session['application_type'],
                           data=session['application_dict'],
                           images=session['images'],
                           application=session['application_dict'],
                           current_page=0,
                           errors=[],
                           curr_data=session['rectification_details'], transaction=session['transaction_id'])


@app.route('/rectification_customer', methods=['POST'])
@requires_auth_role(['normal'])
def rectification_capture_customer():
    if 'store' in request.form:
        session['page_template'] = 'rectification/amend.html'
        session['register_details'] = session['rectification_details']
        return store_application()

    return render_template('rectification/customer.html', images=session['images'],
                           application=session['application_dict'],
                           application_type=session['application_type'], current_page=0,
                           backend_uri=app.config['CASEWORK_FRONTEND_URL'], transaction=session['transaction_id'])


@app.route('/submit_rectification', methods=['POST'])
@requires_auth_role(['normal'])
def submit_rectification():

    if 'store' in request.form:
        session['page_template'] = 'rectification/amend.html'
        return store_application()

    logging.info(format_message('Submitting rectification'))
    response = submit_lc_rectification(request.form)

    if response.status_code != 200:
        err = 'Failed to submit land charges rectification application id:%s - Error code: %s'.format(
            session['worklist_id'],
            str(response.status_code))
        logging.error(format_message(err))
        return render_template('error.html', error_msg=err), response.status_code
    else:
        return redirect('/get_list?appn=lc_rect', code=302, Response=None)

# end of rectification routes

# ============== Cancellation Routes ===============


@app.route('/cancellation_customer', methods=['POST'])
@requires_auth_role(['normal'])
def cancellation_capture_customer():
    if 'store' in request.form:
        return store_application()

    if "plan_attached" in request.form:
        if request.form["plan_attached"] == 'on':
            session["plan_attached"] = 'true'
        else:
            session["plan_attached"] = 'false'
    if 'part_cans_text' in request.form:
        session["part_cans_text"] = request.form["part_cans_text"]
    return render_template('cancellation/canc_customer.html', images=session['images'],
                           application=session['application_dict'],
                           application_type=session['application_type'], current_page=0,
                           backend_uri=app.config['CASEWORK_FRONTEND_URL'], transaction=session['transaction_id'])


@app.route('/submit_cancellation', methods=['POST'])
@requires_auth_role(['normal'])
def submit_cancellation():
    if 'store' in request.form:
        return store_application()

    logging.info(format_message('Submitting cancellation'))
    response = submit_lc_cancellation(request.form)
    if response.status_code != 200:
        err = 'Failed to submit cancellation application id:%s - Error code: %s'.format(
            session['worklist_id'],
            str(response.status_code))
        logging.error(err)
        return render_template('error.html', error_msg=err), response.status_code
    else:
        return redirect('/get_list?appn=cancel', code=302, Response=None)

# end of cancellation routes


# ============== Renewal Routes ===============


@app.route('/renewal_customer', methods=['POST'])
@requires_auth_role(['normal'])
def renewal_capture_customer():
    if 'store' in request.form:
        return store_application()
    return render_template('renewal/customer.html', images=session['images'],
                           application=session['application_dict'],
                           application_type=session['application_type'], current_page=0,
                           backend_uri=app.config['CASEWORK_FRONTEND_URL'], transaction=session['transaction_id'])


@app.route('/submit_renewal', methods=['POST'])
@requires_auth_role(['normal'])
def submit_renewal():
    if 'store' in request.form:
        return store_application()

    form = request.form
    logging.info(format_message('Submitting renewal'))
    cust_address = form['customer_address'].replace("\r\n", ", ").strip()
    application = {'update_registration': {'type': 'Renewal'},
                   'applicant': {
                       'key_number': form['key_number'],
                       'name': form['customer_name'],
                       'address': cust_address,
                       'address_type': form['address_type'],
                       'reference': form['customer_ref']},
                   'class_of_charge': convert_class_of_charge(session['class_of_charge']),
                   'registration_no': session['regn_no'],
                   'registration': {'date': session['reg_date']},
                   'document_id': session['document_id'],
                   'fee_details': {'type': form['payment'],
                                   'fee_factor': 1,
                                   'delivery': session['application_dict']['delivery_method']}
                   }
    url = app.config['CASEWORK_API_URL'] + '/applications/' + session['worklist_id'] + '?action=renewal'
    headers = get_headers({'Content-Type': 'application/json'})
    response = http_put(url, data=json.dumps(application), headers=headers)
    if response.status_code != 200:
        err = 'Failed to submit renewal application id:%s - Error code: %s'.format(
            session['worklist_id'],
            str(response.status_code))
        logging.error(err)
        return render_template('error.html', error_msg=err), response.status_code

    logging.info(format_message("Rectification submitted to CASEWORK_API"))
    data = response.json()

    if 'new_registrations' in data:
        reg_list = []
        for item in data['new_registrations']:
            reg_list.append(item['number'])
        session['confirmation'] = {'reg_no': reg_list}
    else:
        session['confirmation'] = {'reg_no': []}

    return redirect('/get_list?appn=lc_renewal', code=302, Response=None)
# end of renewal routes


# ============== Land Charges routes ===============


@app.route('/land_charge_capture', methods=['POST'])
@requires_auth_role(['normal'])
def land_charge_capture():
    logging.debug(request.form)

    if 'store' in request.form:
        session['register_details'] = build_lc_inputs(request.form)
        return store_application()

    result = validate_land_charge(request.form)
    entered_fields = build_lc_inputs(request.form)
    entered_fields['class'] = result['class']

    if len(result['error']) == 0:
        # return get_list_of_applications("lc_regn", "")
        session['register_details'] = entered_fields
        return redirect('/land_charge_verification', code=302, Response=None)
    else:
        # page = "%s.html" % (session['application_dict']['form'])
        page = session['page_template']
        return render_template(page, application_type=session['application_type'],
                               images=session['images'],
                               application=session['application_dict'],
                               current_page=0,
                               errors=result['error'],
                               curr_data=entered_fields,
                               screen='capture',
                               data=session['application_dict'],
                               transaction=session['transaction_id'])


@app.route('/land_charge_capture', methods=['GET'])
@requires_auth_role(['normal'])
def get_land_charge_capture():
    # For returning from verification screen
    # session['page_template']
    return render_template(session['page_template'],
                           application_type=session['application_type'],
                           data=session['application_dict'],
                           images=session['images'],
                           application=session['application_dict'],
                           current_page=0,
                           errors=[],
                           curr_data=session['register_details'],
                           transaction=session['transaction_id'])


@app.route('/land_charge_verification', methods=['GET'])
@requires_auth_role(['normal'])
def land_charge_verification():
    return render_template('lc_regn/verify.html', application_type=session['application_type'], data={},
                           images=session['images'], application=session['application_dict'],
                           details=session['register_details'], screen='verify',
                           current_page=0, transaction=session['transaction_id'])


@app.route('/lc_verify_details', methods=['POST'])
@requires_auth_role(['normal'])
def lc_verify_details():
    if 'store' in request.form:
        return store_application()

    return redirect('/conveyancer_and_fees', code=302, Response=None)


@app.route('/conveyancer_and_fees', methods=['GET'])
@requires_auth_role(['normal'])
def conveyancer_and_fees():
    return render_template('lc_regn/customer.html', application_type=session['application_type'], data={},
                           images=session['images'], application=session['application_dict'],
                           screen='customer', backend_uri=app.config['CASEWORK_FRONTEND_URL'], current_page=0,
                           transaction=session['transaction_id'])


# def extract_error(stack, message):
#     items = stack.split("\n")
#     result = {
#         "message": message,
#         "stack": []
#     }


@app.route('/lc_process_application', methods=['POST'])
@requires_auth_role(['normal'])
def lc_process_application():
    if 'store' in request.form:
        return store_application()

    logging.info(format_message('Submitting LC registration'))
    customer_fee_details = build_customer_fee_inputs(request.form)
    response = submit_lc_registration(customer_fee_details)
    if response.status_code != 200:
        exception = json.loads(response.text)

        error = {
            "message": 'Failed to submit land charges registration application id: {}'.format(session['worklist_id']),
            "dict": exception
        }

        # error = {
        #     "message": 'Failed to submit land charges registration application id: {}'.format(session['worklist_id']),
        #     "stack": exception["stack"]
        # }

        # err = 'Failed to submit land charges registration application id: {} - Error code: {}; {}'.format(
        #      session['worklist_id'],
        #      str(response.status_code),
        #      response.text
        # )
        logging.error(format_message(error))
        return render_template('error.html', error_msg=error), response.status_code
    else:
        return redirect('/get_list?appn=' + session['application_type'], code=302, Response=None)


# ============== Common routes =====================

@app.route('/confirmation', methods=['GET'])
@requires_auth_role(['normal'])
def confirmation():
    if 'regn_no' not in session:
        session['regn_no'] = []

    return render_template('confirmation.html', data=session['regn_no'], application_type=session['application_type'])


@app.route('/totals', methods=['GET'])
def totals():
    data = get_totals()
    return Response(json.dumps(data), status=200, mimetype='application/json')


@app.route('/rejection', methods=['POST'])
@requires_auth_role(['normal'])
def rejection():
    logging.info(format_message("Reject application"))
    appn_id = session['worklist_id']
    url = app.config['CASEWORK_API_URL'] + '/applications/' + appn_id
    response = http_delete(url, params={'reject': True}, headers=get_headers())

    if response.status_code != 204 and response.status_code != 404:
        return redirect('/rejection_error', code=302, Response=None)

    doc_id = session['document_id']
    url = app.config['CASEWORK_API_URL'] + '/forms/' + str(doc_id)
    response = http_delete(url, headers=get_headers())
    if response.status_code != 204 and response.status_code != 404:
        return redirect('/rejection_error', code=302, Response=None)
    session['rejection'] = True
    return redirect('/get_list?appn=' + session['application_type'], code=302, Response=None)


@app.route('/rejection_error', methods=['GET'])
def rejection_error():
    err = 'Failure in the deletion of application id: %s and/or document id: %s' \
          % (session['worklist_id'], session['document_id'])
    logging.error(format_message(err))
    return render_template('error.html', error_msg=err), '500'


@app.template_filter()
def date_time_filter(date_str, date_format='%d %B %Y'):
    """convert a datetime to a different format."""
    value = datetime.strptime(date_str, '%Y-%m-%d').date()
    return value.strftime(date_format)

app.jinja_env.filters['date_time_filter'] = date_time_filter
# end of common routes


def get_totals():
    # initialise all counters to 0

    bank_regn, bank_amend, bank_rect, bank_with, bank_stored = (0,) * 5
    lc_regn, lc_pn, lc_rect, lc_renewal, lc_stored = (0,) * 5
    canc, canc_stored = (0,) * 2
    search_full, search_bank, search_stored = (0,) * 3
    unknown = 0

    url = app.config['CASEWORK_API_URL'] + '/applications'
    response = http_get(url, headers=get_headers())
    if response.status_code == 200:
        full_list = response.json()

        for item in full_list:
            if item['stored']:
                if item['work_type'] in ['bank_regn', 'bank_amend', 'bank_rect', 'bank_with']:
                    bank_stored += 1
                elif item['work_type'] in ['lc_regn', 'lc_pn', 'lc_rect', 'lc_renewal']:
                    lc_stored += 1
                elif item['work_type'] in ['cancel']:
                    canc_stored += 1
                elif item['work_type'] in ['search_full', 'search_bank']:
                    search_stored += 1

            else:
                if item['work_type'] == "bank_regn":
                    bank_regn += 1
                elif item['work_type'] == "bank_amend":
                    bank_amend += 1
                elif item['work_type'] == "bank_rect":
                    bank_rect += 1
                elif item['work_type'] == "bank_with":
                    bank_with += 1
                elif item['work_type'] == "lc_regn":
                    lc_regn += 1
                elif item['work_type'] == "lc_pn":
                    lc_pn += 1
                elif item['work_type'] == "lc_rect":
                    lc_rect += 1
                elif item['work_type'] == "lc_renewal":
                    lc_renewal += 1
                elif item['work_type'] == "cancel":
                    canc += 1
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
        'canc': canc, 'canc_stored': canc_stored,
        'search_full': search_full, 'search_bank': search_bank, 'search_stored': search_stored,
        'unknown': unknown
    }


def page_required(appn_type, sub_type=''):
    if appn_type == 'lc_regn':
        page = {
            'K1': 'lc_regn/k1234.html',
            'K2': 'lc_regn/k1234.html',
            'K3': 'lc_regn/k1234.html',
            'K4': 'lc_regn/k1234.html',
        }
        return page[sub_type]

    else:
        html_page = {
            "bank_amend": "bank_amend/retrieve.html",
            "cancel": "cancellation/canc_retrieve.html",
            "bank_regn": "bank_regn/official.html",
            "search_full": "searches/info.html",
            "search_bank": "searches/info.html",
            "oc": "regn_retrieve.html",
            "lc_rect": "rectification/retrieve.html",
            "lc_pn": "priority_notice_capture.html",
            "lc_renewal": "renewal/retrieve.html"
        }
        return html_page.get(appn_type)


# Still used for searches
def delete_from_worklist(application_id):
    url = app.config['CASEWORK_API_URL'] + '/applications/' + application_id
    response = http_delete(url, headers=get_headers({'X-Transaction-ID': application_id}))
    if response.status_code != 204:
        err = 'Failed to delete application ' + application_id + ' from the worklist. Error code:' \
              + str(response.status_code)

        logging.error(format_message(err))
        raise RuntimeError(err)


def set_session_variables(variable_dict):
    for key in variable_dict:
        session[key] = variable_dict[key]


# pull back an individual page as an image
@app.route('/images/<int:doc_id>/<int:page_no>', methods=['GET'])
def get_page_image(doc_id, page_no):
    url = app.config['CASEWORK_API_URL'] + '/forms/' + str(doc_id) + '/' + str(page_no)
    data = http_get(url, headers=get_headers())
    return data.content, data.status_code, data.headers.items()


# pull back page data as JSON
@app.route('/images/<int:doc_id>', methods=['GET'])
def get_form_images(doc_id):
    url = app.config['CASEWORK_API_URL'] + '/forms/' + str(doc_id)
    data = http_get(url, headers=get_headers())
    json_data = json.loads(data.content.decode('utf-8'))
    return json.dumps(json_data), data.status_code, data.headers.items()


@app.route('/counties', methods=['GET'])
def get_counties():
    params = ""
    if 'welsh' in request.args:
        if request.args['welsh'] == "yes":
            params = "?welsh=yes"
    else:
        params = "?welsh=no"

    url = app.config['CASEWORK_API_URL'] + '/counties' + params
    data = requests.get(url, headers=get_headers())
    return Response(data, status=data.status_code, mimetype='application/json')


def get_translated_county(county_name):
    url = app.config['CASEWORK_API_URL'] + '/county/' + county_name
    response = http_get(url, headers=get_headers())
    return response.json()


@app.route('/internal', methods=['GET'])
@requires_auth_role(['normal'])
def internal():
    return render_template('work_list/internal.html')


@app.route('/enquiries', methods=['GET'])
@requires_auth_role(['normal'])
def enquiries():
    # curr_data = {'reprint_selected': True, 'estate_owner': {'private': {"forenames": [], "surname": ""},
    #                                                       'local': {'name': "", "area": ""}, "complex": {"name": ""}}}

    data = get_totals()
    return render_template('work_list/enquiries.html', data=data)

    # return render_template('work_list/enquiries.html', curr_data=curr_data)


@app.route('/reprints', methods=['GET'])
@requires_auth_role(['normal', 'reprint'])
def reprints():
    curr_data = {'reprint_selected': True, 'estate_owner_ind': 'Private Individual',
                 'estate_owner': {'private': {"forenames": [], "surname": ""},
                                  'local': {'name': "", "area": ""}, "complex": {"name": ""}}}
    if 'request_id' in request.args:  # search request id passed, generate pdf
        request_id = request.args["request_id"]

        url = app.config['CASEWORK_API_URL'] + '/reprints/search?request_id=' + request_id
        response = http_get(url)
        if response.status_code == 200:
            return send_file(BytesIO(response.content), as_attachment=False, attachment_filename='reprint.pdf',
                             mimetype='application/pdf')
        else:
            return render_template('error.html', error_msg=response.text, status=response.status_code)

    return render_template('reprint.html', curr_data=curr_data)


@app.route('/reprints', methods=['POST'])
@requires_auth_role(['normal', 'reprint'])
def generate_reprints():
    curr_data = {"reprint_selected": True,
                 "estate_owner": {"private": {"forenames": [], "surname": ""}, "company": "",
                                  "local": {'name': "", "area": ""}, "complex": {"name": ""}}}
    if "k22_reg_no" in request.form:
        curr_data["k22_reg_no"] = request.form["k22_reg_no"]
    if "k22_reg_date" in request.form:
        curr_data["k22_reg_date"] = request.form["k22_reg_date"]
    if 'reprint_type' not in request.form:
        return Response('no reprint type supplied', status=400)
    reprint_type = request.form["reprint_type"]

    if reprint_type == 'k22':
        registration_no = request.form["k22_reg_no"]
        reg_date = request.form["k22_reg_date"].split("/")  # dd/mm/yyyy
        registration_date = '%s-%s-%s' % (reg_date[2], reg_date[1], reg_date[0])
        url = app.config['CASEWORK_API_URL'] + '/reprints/'
        url += 'registration?registration_no=' + registration_no + '&registration_date=' + registration_date
        response = http_get(url)
        if response.status_code == 200:
            return send_file(BytesIO(response.content), as_attachment=False, attachment_filename='reprint.pdf',
                             mimetype='application/pdf')
        elif response.status_code == 405:
            return render_template('error.html', error_msg=response.text, status=405)
        else:
            curr_data["k22_error_message"] = response.text
            return render_template('reprint.html', curr_data=curr_data)

    elif reprint_type == 'k18':
        if 'estateOwnerTypes' not in request.form:
            return Response('no estate owner type supplied', status=400)
        curr_data['estate_owner_ind'] = request.form["estateOwnerTypes"]
        curr_data["estate_owner"]["private"]["forenames"] = request.form['forename'].split()
        curr_data["estate_owner"]["private"]["surname"] = request.form['surname']
        curr_data["estate_owner"]["local"]["name"] = request.form['loc_auth']
        curr_data["estate_owner"]["local"]["area"] = request.form['loc_auth_area']
        curr_data['key_number'] = request.form['key_number']
        date_from = request.form['date_from'].split("/")  # dd/mm/yyyy
        curr_data['date_from'] = '%s-%s-%s' % (date_from[2], date_from[1], date_from[0])
        date_to = request.form['date_to'].split("/")  # dd/mm/yyyy
        curr_data['date_to'] = '%s-%s-%s' % (date_to[2], date_to[1], date_to[0])
        curr_data['estate_owner']['company'] = request.form['company']
        curr_data['estate_owner']['complex']['name'] = request.form['complex_name']
        curr_data['estate_owner']['complex']['number'] = request.form['complex_number']
        curr_data['estate_owner']['other'] = request.form['other_name']
    url = app.config['CASEWORK_API_URL'] + '/reprints/search'
    response = http_post(url, data=json.dumps(curr_data))
    data = json.loads(response.content.decode('utf-8'))
    results = {'results': []}
    for result in data['results']:
        search_time = result['search_timestamp']
        search_time = search_time[0:16]
        res = {'request_id': result['request_id'], 'search_timestamp': search_time}
        if result['name_type'] == 'Private Individual':
            res['name'] = result['estate_owner']['private']['forenames'] + ' ' + \
                result['estate_owner']['private']['surname']
        elif result['name_type'] in ['Local Authority', 'County Council', 'Rural Council', 'Other Council',
                                     'Parish Council']:
            res['name'] = result['estate_owner']['local']['name'] + ' - ' + \
                result['estate_owner']['local']['area']
        elif result['name_type'] == 'Limited Company':
            res['name'] = result['estate_owner']['company']
        elif result['name_type'] == 'Complex Name':
            res['name'] = result['estate_owner']['complex']['name']
        elif result['name_type'] in ['Other', 'Development Corporation']:
            res['name'] = result['estate_owner']['other']
        results['results'].append(res)
    return render_template('reprint_k18_results.html', curr_data=results)


# Some CORS avoidance routes

@app.route('/keyholders/<key_number>', methods=['GET'])
def get_keyholder(key_number):
    uri = app.config['CASEWORK_API_URL'] + '/keyholders/' + key_number
    response = http_get(uri, headers=get_headers())
    return Response(response.text, status=response.status_code, mimetype='application/json')


@app.route('/complex_names/<name>', methods=['GET'])
def get_complex_names(name):
    uri = app.config['CASEWORK_API_URL'] + '/complex_names/' + name
    response = http_get(uri, headers=get_headers())
    return Response(response.text, status=200, mimetype='application/json')


@app.route('/complex_names/<name>/<number>', methods=['POST'])
def insert_complex_name(name, number):
    uri = app.config['CASEWORK_API_URL'] + '/complex_names/{}/{}'.format(name, number)
    response = http_post(uri, headers=get_headers({'Content-Type': 'application/json'}))
    return Response(response.text, status=response.status_code, mimetype='application/json')


@app.route('/reclassify/<appn_id>', methods=['GET'])
@requires_auth_role(['normal'])
def get_reclassify_form(appn_id):
    clear_session()
    logging.info("Reclassify %s Application", appn_id)
    session['transaction_id'] = appn_id
    session['worklist_id'] = appn_id
    url = app.config['CASEWORK_API_URL'] + '/applications/' + appn_id
    response = http_get(url, headers=get_headers())
    application_json = response.json()
    logging.debug(application_json)
    session['application_type'] = application_json['work_type']
    document_id = application_json['application_data']['document_id']
    session['document_id'] = document_id
    doc_response = get_form_images(document_id)
    images = []
    image_data = json.loads(doc_response[0])
    for page in image_data['images']:
        url = "/images/" + str(document_id) + '/' + str(page['page'])
        images.append(url)
    template = "reclassify/reclassify.html"
    session['page_template'] = template
    return render_template(template, data=application_json, images=images, curr_data=application_json,
                           current_page=0, errors=[], transaction=session['transaction_id'])


@app.route('/reclassify', methods=['POST'])
@requires_auth_role(['normal'])
def post_reclassify_form():
    appn_id = session['transaction_id']
    form_type = request.form['form_type']
    logging.info("T:%s Reclassify %s Application ", appn_id, form_type)
    uri = app.config['CASEWORK_API_URL'] + '/reclassify'
    data = {"appn_id": appn_id, "form_type": form_type}
    response = http_post(uri, data=json.dumps(data), headers=get_headers({'Content-Type': 'application/json'}))
    work_type = json.loads(response.content.decode('utf-8'))
    result = work_type
    return get_list_of_applications("unknown", result, "")


@app.route('/multi_reg_check/<reg_date>/<reg_no>', methods=['GET'])
def get_multiple_registrations(reg_date, reg_no):
    url = app.config['CASEWORK_API_URL'] + '/multi_reg_check/' + reg_date + "/" + reg_no
    data = http_get(url, headers=get_headers())
    return Response(data, status=200, mimetype='application/json')


# @app.route('/store', methods=['GET'])
# def get_store_form(): # TODO: probably not needed...
#     return render_template('store.html', application_type=session['application_type'],
#                                images=session['images'],
#                                application=session['application_dict'],
#                                current_page=0,
#
#                                # curr_data=entered_fields,
#                                screen='capture',
#                                data=session['application_dict'],
#                                # transaction=session['transaction_id'])
#                            )


def store_application():
    logging.debug(session)

    # if session['application_type'] in ['bank_regn', 'bank_amend']:
    #     if session['page_template'] in ['bank_regn/debtor.html', 'bank_amend/debtor.html']:
    #         session['parties'] = get_debtor_details(request.form)
    if session['application_type'] in ['cancel']:
        # TODO: this duplicates code in /cancellation_customer
        if "plan_attached" in request.form:
            if request.form["plan_attached"] == 'on':
                session["plan_attached"] = 'true'
            else:
                session["plan_attached"] = 'false'

        if 'part_cans_text' in request.form:
            session["part_cans_text"] = request.form["part_cans_text"]
    # else:  # land charge application
    #       if session['page_template'] == 'lc_regn/k1234.html' or session['page_template'] == 'rectification/amend.html':
     #       session['register_details'] = build_lc_inputs(request.form)
     #   elif session['page_template'] == 'rectification/check.html':
     #       session['register_details'] = session['rectification_details']

    return render_template('store.html', application_type=session['application_type'],
                           images=session['images'],
                           application=session['application_dict'],
                           current_page=0,
                           # curr_data=entered_fields,
                           # screen='capture',
                           data=session['application_dict'],
                           # transaction=session['transaction_id'])
                           )
    # entered_fields = build_lc_inputs(request.form)
    # entered_fields['class'] = result['class']
    #
    # if len(result['error']) == 0:
    #     # return get_list_of_applications("lc_regn", "")
    #     session['register_details'] = entered_fields
    # SESSION:
    # {'page_template': 'lc_regn/k1234.html', 'application_type': 'lc_regn', 'document_id': 67,
    # 'application_dict': {'date_received': '2015-11-05 14:03:57', 'work_type': 'lc_regn',
    # 'delivery_method': 'Postal', 'appn_id': '958', 'status': 'new', 'application_data': {'document_id': 67},
    # 'form': 'K2', 'application_type': 'K2'}, 'transaction_id': '958',
    # 'images': ['http://localhost:5010/images/67/1'], 'worklist_id': '958'}


@app.route('/store', methods=['POST'])
def post_store():
    logging.debug('---------- STORE -----------')

    # stored_data = {
    #     "document_id": session['document_id'],
    #     "page_template": session['page_template'],
    #     "application_type": session['application_type'],
    #     "application_dict": session['application_dict']
    # }

    stored_data = {}
    for key in session:
        if key not in ['username', 'display_name', 'appn_id', 'transaction_id']:
            # Don't want to save this as part of the data
            stored_data[key] = session[key]

    store_app = {
        'data': stored_data,
        'who': session['username'],
        'reason': request.form['store_reason']
    }

    logging.debug(session)

    url = app.config['CASEWORK_API_URL'] + '/applications/' + session['worklist_id'] + '?action=store'
    headers = get_headers({'Content-Type': 'application/json'})
    response = http_put(url, data=json.dumps(store_app), headers=headers)

    if response.status_code != 200:
        logging.debug(response.text)
        raise RuntimeError("Failed to save application")

    return redirect("/")
    #

    # logging.debug(session)
    # logging.debug(session['application_dict'])
    # logging.debug(request.form)
    #
    # for key in request.form:
    #     logging.debug(key)
    #     #logging.debug(value)

    # Initially assume we're saving from the capture screen

    # We need to store the current 'register_details'
    # And the contents of the current form (damn)
    # And which page we were on
    # Therefore this needs to be a POST, and the link needs to be JavaScript

    #     result = validate_land_charge(request.form)
    # entered_fields = build_lc_inputs(request.form)
    # entered_fields['class'] = result['class']
    #
    # if len(result['error']) == 0:
    #     # return get_list_of_applications("lc_regn", "")
    #     session['register_details'] = entered_fields

    # @app.route('/applications/<appn_id>', methods=['PUT'])
    # which will store all of the data we hope


# We need a place to navigate to if any of the important AJAX queries fail during form creation
# Can't post, which is a shame, so we're not able to display much information. It's enough at least
# to stop the user when the application is invisibly broken.
@app.route("/error/<message_id>/<status>", methods=["GET"])
def get_ajax_error(message_id, status):
    messages = {
        "county": "Failed to load county list."
    }

    msg = message_id
    if message_id in messages:
        msg = messages[message_id]

    msg += " Status: {}.".format(status)
    error = msg

    return render_template('error.html', error_msg=error, status=500)


# These routes added because I have a nasty feeling they'll be needed
@app.route('/forms/<size>', methods=["POST"])
def create_documents(size):
    uri = app.config['CASEWORK_API_URL'] + '/forms/' + size
    response = http_post(uri, data=request.data, params=request.args, headers=request.headers)
    return Response(response.text, status=response.status_code, mimetype='application/json')


@app.route('/forms/<int:doc_id>', methods=["GET"])
def get_document_info(doc_id):
    uri = app.config['CASEWORK_API_URL'] + '/forms/' + str(doc_id)
    response = http_get(uri, headers=get_headers())
    return Response(response.text, status=response.status_code, mimetype='application/json')


@app.route('/applications', methods=['POST'])
def create_application():
    uri = app.config['CASEWORK_API_URL'] + '/applications'
    response = http_post(uri, data=request.data, params=request.args, headers=request.headers)
    return Response(response.text, status=response.status_code, mimetype='application/json')


@app.route('/health', methods=['GET'])
def health():
    result = {
        'status': 'OK',
        'dependencies': {}
    }
    url = app.config['CASEWORK_API_URL'] + '/health'
    status = 200
    try:
        response = http_get(url)
        data = response.json()
        status = response.status_code
        result["dependencies"] = data["dependencies"]
        result["dependencies"]["casework-api"] = str(response.status_code) + " " + data["status"]
        result["status"] = "OK"
    except Exception as e:
        result["dependencies"]["casework-api"] = "Error"
        result["status"] = "Error"
        result["error"] = str(e)
    return Response(json.dumps(result), status=status, mimetype='application/json')
