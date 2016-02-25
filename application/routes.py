from application import app
from flask import Response, request, render_template, session, redirect, url_for, send_file
import requests
from datetime import datetime
import logging
import json
from application.form_validation import validate_land_charge
from application.land_charge import build_lc_inputs, build_customer_fee_inputs, submit_lc_registration
from application.search import process_search_criteria
from application.rectification import convert_response_data, submit_lc_rectification
from application.cancellation import submit_lc_cancellation
from application.banks import get_debtor_details, register_bankruptcy, get_original_data, build_original_data
from io import BytesIO


# @app.errorhandler(Exception)
# def error_handler(err):
#     logging.error('========== Error Caught ===========')
#     logging.error(err)
#     return render_template('error.html', error_msg=str(err)), 500


@app.before_request
def before_request():
    logging.info("BEGIN %s %s [%s] (%s)",
                 request.method, request.url, request.remote_addr, request.__hash__())


@app.after_request
def after_request(response):
    logging.info('END %s %s [%s] (%s) -- %s',
                 request.method, request.url, request.remote_addr, request.__hash__(),
                 response.status)
    return response


@app.route('/', methods=["GET"])
def index():
    if 'worklist_id' in session:
        url = app.config['CASEWORK_API_URL'] + '/applications/' + session['worklist_id'] + '/lock'
        requests.delete(url)
        del(session['worklist_id'])

    data = get_totals()
    return render_template('totals.html', data=data)


@app.route('/get_list', methods=["GET"])
def get_list():
    # check if confirmation message is required
    if 'confirmation' in session:
        result = session['confirmation']
        del(session['confirmation'])
    else:
        result = {}

    if 'worklist_id' in session:
        url = app.config['CASEWORK_API_URL'] + '/applications/' + session['worklist_id'] + '/lock'
        requests.delete(url)
        del(session['worklist_id'])

    return get_list_of_applications(request.args.get('appn'), result, "")


def get_list_of_applications(requested_worklist, result, error_msg):
    url = app.config['CASEWORK_API_URL'] + '/applications?type=' + requested_worklist
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
            if requested_worklist.startswith('search'):
                application['delivery_method'] = appn['delivery_method']

            appn_list.append(application)

    app_totals = get_totals()
    return render_template(return_page, worklist=appn_list, requested_list=requested_worklist,
                           data=app_totals, error_msg=error_msg, result=result)


@app.route('/application_start/<application_type>/<appn_id>/<form>', methods=["GET"])
def application_start(application_type, appn_id, form):

    # Lock application if not in session otherwise assume user has refreshed the browser after select an application
    if 'worklist_id' not in session:
        print('LOCK APPLICATION')
        url = app.config['CASEWORK_API_URL'] + '/applications/' + appn_id + '/lock'
        response = requests.post(url)
        if response.status_code == 404:
            error_msg = "This application is being processed by another member of staff, " \
                        "please select a different application."
            result = {}
            return get_list_of_applications(application_type, result, error_msg)

    url = app.config['CASEWORK_API_URL'] + '/applications/' + appn_id

    response = requests.get(url)

    application_json = response.json()
    document_id = application_json['application_data']['document_id']
    doc_response = get_form_images(document_id)
    images = []
    image_data = json.loads(doc_response[0])
    for page in image_data['images']:
        url = app.config["CASEWORK_FRONTEND_URL"] + "/images/" + str(document_id) + '/' + str(page['page'])
        images.append(url)
    template = page_required(application_type, form)
    application_json['form'] = form

    session.clear()
    set_session_variables({'images': images, 'document_id': document_id,
                           'application_type': application_type, 'worklist_id': appn_id,
                           'application_dict': application_json})

    application = session['application_dict']

    years = {"year_from": "1925",
             "year_to": datetime.now().strftime('%Y')
             }

    # land charge input data required for validation on lc_regn_capture.html
    if 'register_details' in session:
        curr_data = session['register_details']
    else:
        curr_data = build_lc_inputs({})

    session['page_template'] = template  # Might need this later

    return render_template(template, application_type=application_type, data=application_json,
                           images=images, application=application, years=years,
                           current_page=0, errors=[], curr_data=curr_data)


@app.route('/retrieve_new_reg', methods=["GET"])
def retrieve_new_reg():
    return redirect('/application_start/%s/%s/%s' % (session['application_type'], session['worklist_id'],
                    session['application_dict']['form']), code=302, Response=None)


# ======Banks Registration routes===========

@app.route('/check_court_details', methods=["POST"])
def check_court_details():

    if request.form['submit_btn'] == 'No':
        # TODO: Need to save images somewhere, separate story promised
        delete_from_worklist(session['worklist_id'])
        return redirect('/get_list?appn=bank_regn', code=302, Response=None)

    elif request.form['submit_btn'] == 'Yes' and \
        session['court_info']['legal_body'] == request.form['court'] and \
        session['court_info']['legal_body_ref_no'] == request.form['ref_no'] and \
            session['court_info']['legal_body_ref_year'] == request.form['ref_year']:

        session['current_registrations'] = []
        if 'return_to_verify' in request.form:
            return render_template('bank_regn_verify.html', images=session['images'], current_page=0,
                                   court_data=session['court_info'], party_data=session['parties'])
        else:
            return render_template('bank_regn_debtor.html', images=session['images'], current_page=0, data=session)
    else:

        application = {"legal_body":  request.form['court'],
                       "legal_body_ref_no": request.form['ref_no'],
                       "legal_body_ref_year": request.form['ref_year']}
        session['court_info'] = application

        #  call api to see if registration already exists
        url = app.config['CASEWORK_API_URL'] + '/court_check/' + application['legal_body'] + '/' + \
            application['legal_body_ref_no'] + '/' + application['legal_body_ref_year']
        response = requests.get(url)
        if response.status_code == 200:
            logging.info("200 response here")
            session['current_registrations'] = json.loads(response.text)
            return render_template('bank_regn_court.html', images=session['images'], current_page=0,
                                   data=session['court_info'], application=session,
                                   current_registrations=session['current_registrations'])
        elif response.status_code == 404:
            session['current_registrations'] = []
            if 'return_to_verify' in request.form:
                return render_template('bank_regn_verify.html', images=session['images'], current_page=0,
                                       court_data=session['court_info'], party_data=session['parties'])
            else:
                return render_template('bank_regn_debtor.html', images=session['images'], current_page=0, data=session)
        else:
            err = 'Failed to process bankruptcy registration application id:%s - Error code: %s' \
                  % (session['worklist_id'], str(response.status_code))
            logging.error(err)
            return render_template('error.html', error_msg=err), response.status_code



@app.route('/process_debtor_details', methods=['POST'])
def process_debtor_details():
    print('request****', request.form)
    logging.info('processing debtor details')

    session['parties'] = get_debtor_details(request.form)

    return render_template('bank_regn_verify.html', images=session['images'], current_page=0,
                           court_data=session['court_info'], party_data=session['parties'])


@app.route('/bankruptcy_capture/<page>', methods=['GET'])
def bankruptcy_capture(page):
    # For returning from verification screen

    if page == 'key_no':
        page_template = 'bank_regn_key_no.html'
        data = session
    elif page == 'court':
        page_template = 'bank_regn_court.html'
        data = session['court_info']
    else:
        page_template = 'bank_regn_debtor.html'
        data = session['parties'][0]

    return render_template(page_template,
                           application_type=session['application_type'],
                           data=data,
                           images=session['images'],
                           current_page=0,
                           errors=[], from_verify=True)



@app.route('/submit_banks_registration', methods=['POST'])
def submit_banks_registration():

    logging.info('submitting banks registration')
    key_number = request.form['key_number']

    # Check key_number is valid
    url = app.config['CASEWORK_API_URL'] + '/keyholders/' + key_number
    response = requests.get(url)

    if response.status_code != 200:
        err = 'This Key number is invalid please re-enter'
        return render_template('bank_regn_key_no.html',
                               application_type=session['application_type'],
                               data=request.form,
                               images=session['images'],
                               current_page=0,
                               error_msg=err)
    else:

        response = register_bankruptcy(key_number)

        if response.status_code != 200:
            err = 'Failed to submit bankruptcy registration application id:%s - Error code: %s' \
                  % (session['worklist_id'], str(response.status_code))
            logging.error(err)
            return render_template('error.html', error_msg=err), response.status_code
        else:
            return redirect('/get_list?appn=bank_regn', code=302, Response=None)


# =============== Amendment routes ======================

@app.route('/get_original_bankruptcy', methods=['POST'])
def get_original_banks_details():
    curr_data, error_msg, status_code, fatal = build_original_data(request.form)
    if fatal:
        err = 'Failed to process bankruptcy amendment application id:%s - Error code: %s' \
              % (session['worklist_id'], str(status_code))
        logging.error(err)
        return render_template('error.html', error_msg=err), status_code
    else:
        return render_template('bank_amend_retrieve.html', images=session['images'], current_page=0,
                               data=session['original_regns'], curr_data=curr_data, application=session,
                               screen='capture', error=error_msg)


@app.route('/view_original_details', methods=['GET'])
def view_original_details():
    return render_template('bank_amend_details.html', images=session['images'], current_page=0,
                           data=session['original_regns'], application=session, screen='capture')


@app.route('/remove_address/<int:addr>', methods=["GET"])
def remove_address(addr):
    del session['original_regns']['parties']['addresses'][addr]
    session['data_amended'] = 'true'

    return redirect('/view_original_details', code=302, Response=None)


@app.route('/process_amended_details', methods=['POST'])
def process_amended_details():
    logging.info('processing amended details')
    # TODO: this is temp until screen there - can be called by postman
    # data = request.get_json(force=True)
    session['parties'] = get_debtor_details(request.form)
    # result = get_debtor_details(data)
    # print('result', result)
    # return Response(json.dumps(result), status=200, mimetype='application/json')

    return render_template('bank_amend_verify.html', images=session['images'], current_page=0,
                           data=session['parties'])


# TODO: need some routing route here for amendments for navigation from verify screen - will wait till screens available
# TODO: I think it will be something like...
@app.route('/amendment_capture/<page>', methods=['GET'])
def amendment_capture(page):
    # For returning from verification screen

    if page == 'key_no':
        page_template = 'bank_amend_key_no.html'
        data = session
    elif page == 'court':
        page_template = 'bank_amend_court.html'
        data = session['court_info']
    else:
        page_template = 'bank_amend_debtor.html'
        data = session['parties']

    return render_template(page_template,
                           application_type=session['application_type'],
                           data=data,
                           images=session['images'],
                           current_page=0,
                           errors=[], from_verify=True)


@app.route('/submit_banks_amendment', methods=['POST'])
def submit_banks_amendment():
    logging.info('submitting banks amendment')
    key_number = request.form['key_number']
    response = register_bankruptcy(key_number)

    if response.status_code != 200:
        err = 'Failed to submit bankruptcy amendment application id:%s - Error code: %s' \
              % (session['worklist_id'], str(response.status_code))
        logging.error(err)
        return render_template('error.html', error_msg=err), response.status_code
    else:
        return redirect('/get_list?appn=amend', code=302, Response=None)

# ===== end of amendment routes  ===========


@app.route('/process_search_name/<application_type>', methods=['POST'])
def process_search_name(application_type):
    logging.info('Entering search name')

    process_search_criteria(request.form, application_type)

    request_data = {}
    for k in request.form:
        request_data[k] = request.form[k]

    return render_template('search_customer.html', images=session['images'], application=session['application_dict'],
                           application_type=session['application_type'], current_page=0,
                           backend_uri=app.config['CASEWORK_API_URL'], data=request_data)


@app.route('/back_to_search_name', methods=['GET'])
def back_to_search_name():
    logging.info('Entering search name')

    return render_template('search_info.html', images=session['images'], application=session['application_dict'],
                           application_type=session['application_type'], current_page=0,
                           backend_uri=app.config['CASEWORK_API_URL'])


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
    url = app.config['CASEWORK_API_URL'] + '/searches'
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
        logging.error(response.text)
        return render_template('error.html', error_msg=response.text)

    session['confirmation'] = {'reg_no': []}

    if session['application_dict']['search_criteria']['search_type'] == 'full':
        return redirect('/get_list?appn=search_full', code=302, Response=None)
    else:
        return redirect('/get_list?appn=search_bank', code=302, Response=None)

# ===== end of search routes =========


# ======== Rectification routes =============
@app.route('/start_rectification', methods=["GET"])
def start_rectification():
    session['application_type'] = "rectify"
    return render_template('rect_retrieve.html')


@app.route('/get_details', methods=["POST"])
def get_registration_details():
    application_type = session['application_type']
    session['regn_no'] = request.form['reg_no']

    date_as_list = request.form['reg_date'].split("/")  # dd/mm/yyyy

    session['reg_date'] = '%s-%s-%s' % (date_as_list[2], date_as_list[1], date_as_list[0])

    url = app.config['CASEWORK_API_URL'] + '/registrations/' + session['reg_date'] + '/' + session['regn_no']

    response = requests.get(url)

    error_msg = None

    if response.status_code == 404:
        error_msg = "Registration not found please re-enter"
    else:
        application_json = response.json()
        if application_json['status'] == 'cancelled' or application_json['status'] == 'superseded':
            error_msg = "Application has been cancelled or amended - please re-enter"

    # check if part cans has been selected for a bankruptcy

    if error_msg is not None:
        if application_type == 'lc_rect':
            template = 'rectification_retrieve.html'
        elif application_type == 'cancel':
            template = 'canc_retrieve.html'
        else:
            template = 'regn_retrieve.html'
        return render_template(template, application_type=application_type,
                               error_msg=error_msg, images=session['images'], current_page=0,
                               reg_no=request.form['reg_no'], reg_date=request.form['reg_date'])
    else:
        data = response.json()
        template = ''
        if application_type == 'lc_rect':
            template = 'rectification_amend.html'
        elif application_type == 'amend':
            template = 'regn_amend.html'
        elif application_type == 'cancel':
            data['full_cans'] = request.form['full_cans']
            template = 'canc_check.html'
        return render_template(template, data=session['application_dict'],
                               images=session['images'], current_page=0, curr_data=data)


@app.route('/rectification_capture', methods=['POST'])
def rectification_capture():

    logging.info(request.form)

    result = validate_land_charge(request.form)
    entered_fields = build_lc_inputs(request.form)

    entered_fields['class'] = result['class']

    logging.info(entered_fields)

    if len(result['error']) == 0:
        session['rectification_details'] = entered_fields
        return render_template('rectification_check.html', application_type=session['application_type'], data={},
                               images=session['images'], application=session['application_dict'],
                               details=session['rectification_details'], screen='verify',
                               current_page=0)
    else:
        return render_template('rectification_amend.html', application_type=session['application_type'],
                               images=session['images'], application=session['application_dict'],
                               current_page=0, errors=result['error'], curr_data=entered_fields,
                               screen='capture', data=session['application_dict'])


@app.route('/rectification_capture', methods=['GET'])
def return_to_rectification_amend():
    # For returning from check rectification screen
    return render_template('rectification_amend.html',
                           application_type=session['application_type'],
                           data=session['application_dict'],
                           images=session['images'],
                           application=session['application_dict'],
                           current_page=0,
                           errors=[],
                           curr_data=session['rectification_details'])


@app.route('/rectification_customer', methods=['GET'])
def rectification_capture_customer():
    logging.info('rectification_capture_customer')
    return render_template('rectification_customer.html', images=session['images'],
                           application=session['application_dict'],
                           application_type=session['application_type'], current_page=0,
                           backend_uri=app.config['CASEWORK_API_URL'])


@app.route('/submit_rectification', methods=['POST'])
def submit_rectification():
    logging.info('Entering submit_rectification')
    response = submit_lc_rectification(request.form)

    if response.status_code != 200:
        err = 'Failed to submit land charges rectification application id:%s - Error code: %s'.format(
            session['worklist_id'],
            str(response.status_code))
        logging.error(err)
        return render_template('error.html', error_msg=err), response.status_code
    else:
        return redirect('/get_list?appn=lc_rect', code=302, Response=None)

# end of rectification routes

# ============== Cancellation Routes ===============


@app.route('/cancellation_customer', methods=['POST'])
def cancellation_capture_customer():
    if 'addl_info' in request.form:
        logging.debug('found addl info')
        session["addl_info"] = request.form["addl_info"]
    else:
        logging.debug('no addl info')
    return render_template('canc_customer.html', images=session['images'],
                           application=session['application_dict'],
                           application_type=session['application_type'], current_page=0,
                           backend_uri=app.config['CASEWORK_API_URL'])


@app.route('/submit_cancellation', methods=['POST'])
def submit_cancellation():
    logging.info('Entering submit_cancellation', str(request.form))
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

# ============== Land Charges routes ===============


@app.route('/land_charge_capture', methods=['POST'])
def land_charge_capture():

    logging.info(request.form)

    result = validate_land_charge(request.form)
    entered_fields = build_lc_inputs(request.form)
    entered_fields['class'] = result['class']

    logging.info(entered_fields)

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
                               data=session['application_dict'])


@app.route('/land_charge_capture', methods=['GET'])
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
                           curr_data=session['register_details'])


@app.route('/land_charge_verification', methods=['GET'])
def land_charge_verification():
    return render_template('lc_regn_verify.html', application_type=session['application_type'], data={},
                           images=session['images'], application=session['application_dict'],
                           details=session['register_details'], screen='verify',
                           current_page=0)


@app.route('/lc_verify_details', methods=['POST'])
def lc_verify_details():
    return redirect('/conveyancer_and_fees', code=302, Response=None)


@app.route('/conveyancer_and_fees', methods=['GET'])
def conveyancer_and_fees():
    return render_template('lc_regn_customer.html', application_type=session['application_type'], data={},
                           images=session['images'], application=session['application_dict'],
                           screen='customer', backend_uri=app.config['CASEWORK_API_URL'], current_page=0)


@app.route('/lc_process_application', methods=['POST'])
def lc_process_application():
    customer_fee_details = build_customer_fee_inputs(request.form)
    response = submit_lc_registration(customer_fee_details)
    if response.status_code != 200:
        err = 'Failed to submit land charges registration application id:%s - Error code: %s' \
              % (session['worklist_id'], str(response.status_code))
        logging.error(err)
        return render_template('error.html', error_msg=err), response.status_code
    else:
        return redirect('/get_list?appn=' + session['application_type'], code=302, Response=None)


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
        "type": application['form'],
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
def date_time_filter(date_str, date_format='%d %B %Y'):
    """convert a datetime to a different format."""
    value = datetime.strptime(date_str, '%Y-%m-%d').date()
    return value.strftime(date_format)

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

    url = app.config['CASEWORK_API_URL'] + '/applications'
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


def page_required(appn_type, sub_type=''):
    if appn_type == 'lc_regn':
        page = {
            'K1': 'k1234.html',
            'K2': 'k1234.html',
            'K3': 'k1234.html',
            'K4': 'k1234.html',
        }
        return page[sub_type]

    else:
        html_page = {
            "bank_amend": "regn_retrieve.html",
            "cancel": "canc_retrieve.html",
            "bank_regn": "bank_regn_court.html",
            "search_full": "search_info.html",
            "search_bank": "search_info.html",
            "oc": "regn_retrieve.html",
            "lc_rect": "rectification_retrieve.html",
            "lc_pn": "priority_notice_capture.html"
        }
        return html_page.get(appn_type)


# TODO: renamed as 'complete', move to back-end?
def delete_from_worklist(application_id):
    url = app.config['CASEWORK_API_URL'] + '/applications/' + application_id
    response = requests.delete(url)
    if response.status_code != 204:
        err = 'Failed to delete application ' + application_id + ' from the worklist. Error code:' \
              + str(response.status_code)

        logging.error(err)
        raise RuntimeError(err)


def set_session_variables(variable_dict):
    for key in variable_dict:
        session[key] = variable_dict[key]


# pull back an individual page as an image
@app.route('/images/<int:doc_id>/<int:page_no>', methods=['GET'])
def get_page_image(doc_id, page_no):
    url = app.config['CASEWORK_API_URL'] + '/forms/' + str(doc_id) + '/' + str(page_no)
    data = requests.get(url)
    return data.content, data.status_code, data.headers.items()


# pull back page data as JSON
@app.route('/images/<int:doc_id>', methods=['GET'])
def get_form_images(doc_id):
    url = app.config['CASEWORK_API_URL'] + '/forms/' + str(doc_id)
    data = requests.get(url)
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
    data = requests.get(url)
    return Response(data, status=200, mimetype='application/json')


def get_translated_county(county_name):
    url = app.config['CASEWORK_API_URL'] + '/county/' + county_name
    response = requests.get(url)
    return response.json()


@app.route('/enquiries', methods=['GET'])
def enquiries():
    curr_data = {'reprint_selected': True, 'estate_owner': {'private': {"forenames": [], "surname": ""},
                                                            'local': {'name': "", "area": ""}, "complex": {"name": ""}}}
    return render_template('enquiries.html', curr_data=curr_data)


@app.route('/reprints', methods=['GET'])
def reprints():
    curr_data = {'reprint_selected': True, 'estate_owner_ind': 'Private Individual',
                 'estate_owner': {'private': {"forenames": [], "surname": ""},
                                  'local': {'name': "", "area": ""}, "complex": {"name": ""}}}
    if 'request_id' in request.args:  # search request id passed, generate pdf
        request_id = request.args["request_id"]

        url = app.config['CASEWORK_API_URL'] + '/reprints/search?request_id=' + request_id
        print("url -- ", url)
        response = requests.get(url)
        return send_file(BytesIO(response.content), as_attachment=False, attachment_filename='reprint.pdf',
                         mimetype='application/pdf')
    return render_template('reprint.html', curr_data=curr_data)


@app.route('/reprints', methods=['POST'])
def generate_reprints():
    curr_data = {"reprint_selected": True,
                 "estate_owner": {"private": {"forenames": [], "surname": ""}, "company": "",
                                  "local": {'name': "", "area": ""}, "complex": {"name": ""}}}
    if 'reprint_type' not in request.form:
        return Response('no reprint type supplied', status=400)
    reprint_type = request.form["reprint_type"]

    if reprint_type == 'k22':
        registration_no = request.form["k22_reg_no"]
        reg_date = request.form["k22_reg_date"].split("/")  # dd/mm/yyyy
        registration_date = '%s-%s-%s' % (reg_date[2], reg_date[1], reg_date[0])
        print('reg date***', registration_date)
        url = app.config['CASEWORK_API_URL'] + '/reprints/'
        url += 'registration?registration_no=' + registration_no + '&registration_date=' + registration_date
        response = requests.get(url)
        return send_file(BytesIO(response.content), as_attachment=False, attachment_filename='reprint.pdf',
                         mimetype='application/pdf')
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
    response = requests.post(url, data=json.dumps(curr_data))
    data = json.loads(response.content.decode('utf-8'))
    results = {'results': []}
    for result in data['results']:
        search_time = result['search_timestamp']
        search_time = search_time[0:16]
        res = {'request_id': result['request_id'], 'search_timestamp': search_time}
        if result['name_type'] == 'Private Individual':
            res['name'] = result['estate_owner']['private']['forenames'] + ' ' + \
                result['estate_owner']['private']['surname']
        elif result['name_type'] == 'Local Authority':
            res['name'] = result['estate_owner']['local']['name'] + ' - ' + \
                result['estate_owner']['local']['area']
        elif result['name_type'] == 'Company':
            res['name'] = result['estate_owner']['company']
        elif result['name_type'] == 'Complex':
            res['name'] = result['estate_owner']['complex']['name']
        elif result['name_type'] == 'Other':
            res['name'] = result['estate_owner']['other']
        results['results'].append(res)
    #  return Response(json.dumps(data), status=200, mimetype="application/json")
    #  return Response(json.dumps(results), status=200, mimetype="application/json")
    return render_template('reprint_k18_results.html', curr_data=results)
