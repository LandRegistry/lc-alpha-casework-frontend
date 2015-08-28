from application.routes import app
from unittest import mock
import os
import json
import requests
from tests import test_data
import xml.etree.ElementTree as ET

dir_ = os.path.dirname(__file__)
total_response = open(os.path.join(dir_, 'data/totals.json'), 'r').read()
application_response = open(os.path.join(dir_, 'data/application.json'), 'r').read()

registration = '{"new_registrations": [512344]}'
multi_name_reg = '{"new_registrations": [512344, 512345]}'

application_dict = {
    'application_type': 'PA(B)',
    'reg_nos': [50001],
    'date': '2015-08-28',
    'debtor_name': {
        'forenames': ['Bob'],
        'surname': 'Howard'
    },
    'document_id': '43'
}



class FakeResponse(requests.Response):
    def __init__(self, content='', status_code=200, response_file=''):
        super(FakeResponse, self).__init__()
        self._content = content
        self._content_consumed = True
        self.status_code = status_code
        self.response_file = response_file

    def json(self, **kwargs):
        data = json.loads(self.response_file)
        return data


class TestCaseworkFrontend:

    def setup_method(self, method):
        app.secret_key = 'djkghfkgfgd'
        self.app = app.test_client()


    @mock.patch('requests.get', return_value=FakeResponse('stuff', 200, total_response))
    def test_get_totals(self, mock_get):
        response = self.app.get('/')
        assert response.status_code == 200


    @mock.patch('requests.get', side_effect=Exception('Fail'))
    def test_get_totals_fail(self, mock_connect):
        response = self.app.get('/')
        assert response.status_code == 500


    @mock.patch('requests.get', return_value=FakeResponse('stuff', 200, total_response))
    def test_get_list(self, mock_get):
        response = self.app.get('/get_list?appn=bank_regn')
        assert response.status_code == 200

    @mock.patch('requests.get', side_effect=Exception('Fail'))
    def test_get_list_fail(self, mock_connect):
        response = self.app.get('/get_list?appn=bank_regn')
        assert response.status_code == 500

    @mock.patch('requests.get', return_value=FakeResponse('stuff', 200, application_response))
    def test_get_appliction(self, mock_get):
        response = self.app.get('/get_application/bank_regn/1')
        assert response.status_code == 200

    @mock.patch('requests.get', side_effect=Exception('Fail'))
    def test_get_appliction_fail(self, mock_get):
        response = self.app.get('/get_application/bank_regn/1')
        assert response.status_code == 500

    def test_process_name(self):
        with self.app as c:
            with c.session_transaction() as session:
                session['application_dict'] = application_dict
                session['images'] = ['/document/1/image/1']
        response = self.app.post('/process_banks_name', data=dict(forename='John', occupation='', surname='Smith'))
        html = response.data.decode('utf-8')
        tree = ET.fromstring(html)
        title_node = tree.find('.//*[@id="form_data"]/h4')
        address_node = tree.find('.//*[@id="address_area"]')
        assert title_node.text == "Debtor address"
        assert address_node.text.strip() == ""

    def test_alias_name(self):
        with self.app as c:
            with c.session_transaction() as session:
                session['application_dict'] = application_dict
                session['images'] = ['/document/1/image/1']
        response = self.app.post('/process_banks_name',
                                 data=dict(forename='John James', occupation='', surname='Smith',
                                           aliasforename0="Joan Jean", aliassurname0="Smyth",
                                           aliasforename1="John", aliassurname1="Smithers"))

        html = response.data.decode('utf-8')
        tree = ET.fromstring(html)
        title_node = tree.find('.//*[@id="form_data"]/h4')
        address_node = tree.find('.//*[@id="address_area"]')
        assert title_node.text == "Debtor address"
        assert address_node.text.strip() == ""

    def test_process_name_fail(self):
        response = self.app.post('/process_banks_name', data='John')
        assert ('error' in response.data.decode())

    def test_residence_empty(self):
        with self.app as c:
            with c.session_transaction() as session:
                session['application_dict'] = application_dict
                session['images'] = ['/document/1/image/1']
        response = self.app.post('/address', data={
            'county': '', 'postcode': ''
        })
        html = response.data.decode('utf-8')
        tree = ET.fromstring(html)
        node = tree.find('.//*[@id="form_data"]/form/div[2]/label')
        assert node.text == "Court name"
        assert response.status_code == 200

    def test_addresss_2_lines(self):
        with self.app as c:
            with c.session_transaction() as session:
                session['application_dict'] = application_dict
                session['images'] = ['/document/1/image/1']
        response = self.app.post('/address', data={
            "address1": '34 Haden Close', "address2": 'Little Horn',
            "county": 'North Shore', "postcode": 'AA1 1AA'
        })
        html = response.data.decode('utf-8')
        tree = ET.fromstring(html)
        node = tree.find('.//*[@id="form_data"]/form/div[2]/label')
        assert node.text == "Court name"
        assert response.status_code == 200

    def test_additional_address(self):
        with self.app as c:
            with c.session_transaction() as session:
                session['application_dict'] = application_dict
                session['images'] = ['/document/1/image/1']
        response = self.app.post('/address', data={
            "address1": '35 Haden Close', "address2": 'Little Horn', "address3": '',
            "county": 'North Shore', "postcode": 'AA1 1AA', "add_address": 'Add Address'
        })
        html = response.data.decode('utf-8')
        tree = ET.fromstring(html)
        title_node = tree.find('.//*[@id="form_data"]/h4')
        address_node = tree.find('.//*[@id="address_area"]/div')
        assert title_node.text == "Debtor address"
        assert "35 Haden Close" in address_node.text

    def test_residence(self):
        with self.app as c:
            with c.session_transaction() as session:
                session['application_dict'] = application_dict
                session['images'] = ['/document/1/image/1']
        response = self.app.post('/address', data={
            "address1": '34 Haden Close', "address2": 'Little Horn', "address3": '',
            "county": 'North Shore', "postcode": 'AA1 1AA'
        })
        html = response.data.decode('utf-8')
        tree = ET.fromstring(html)
        node = tree.find('.//*[@id="form_data"]/form/div[2]/label')
        assert node.text == "Court name"

    @mock.patch('requests.post', return_value=FakeResponse('stuff', 200, registration))
    @mock.patch('requests.delete', return_value=FakeResponse(status_code=204))
    def test_pab(self, mock_post, mock_delete):
        with self.app as c:
            with c.session_transaction() as session:
                session['application_dict'] = application_dict
                session['document_id'] = '17'
                session['worklist_id'] = '3'
        response = self.app.post('/court_details', data=test_data.process_pab)
        assert response.status_code == 200

    @mock.patch('requests.post', return_value=FakeResponse('stuff', 200, registration))
    @mock.patch('requests.delete', return_value=FakeResponse(status_code=204))
    def test_process_court(self, mock_post, mock_delete):
        with self.app as c:
            with c.session_transaction() as session:
                session['application_dict'] = application_dict
                session['document_id'] = '17'
                session['worklist_id'] = '3'
        response = self.app.post('/court_details', data=test_data.process_court)
        html = response.data.decode('utf-8')
        tree = ET.fromstring(html)
        button = tree.find('.//*[@id="main"]/div/div[2]/a')
        no_node = tree.find('.//*[@id="main"]/div/div[1]/div[3]/h3[1]')

        assert response.status_code == 200
        assert no_node.text == '512344'
        assert button.text == 'Return to Worklist'

    @mock.patch('requests.post', side_effect=Exception('Fail'))
    def test_process_court_fail(self, mock_post):
        with self.app as c:
            with c.session_transaction() as session:
                session['application_dict'] = application_dict
                session['document_id'] = '17'
                session['worklist_id'] = '3'
        response = self.app.post('/court_details', data=test_data.process_court)
        assert response.status_code == 500

    @mock.patch('requests.post', return_value=FakeResponse('stuff', 200, multi_name_reg))
    @mock.patch('requests.delete', return_value=FakeResponse(status_code=204))
    def test_multi_name(self, mock_post, mock_delete):
        with self.app as c:
            with c.session_transaction() as session:
                session['application_dict'] = application_dict
                session['document_id'] = '17'
                session['worklist_id'] = '3'
        response = self.app.post('/court_details', data=test_data.multi_name)
        assert response.status_code == 200

    def test_notification_screen(self):
        with self.app as c:
            with c.session_transaction() as session:
                session['application_dict'] = application_dict
        response = self.app.get('/notification')

        html = response.data.decode('utf-8')
        tree = ET.fromstring(html)
        name_node = tree.findall('.//*[@id="area"]/div/span[1]')[0]
        title_node = tree.find('.//head/title')
        assert name_node.text == "Bob Howard"
        assert response.status_code == 200
        assert title_node.text == "Form K22"



