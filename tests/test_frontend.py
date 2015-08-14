from application.routes import app
from unittest import mock
import os
import json
import requests
from tests import test_data

dir_ = os.path.dirname(__file__)
total_response = open(os.path.join(dir_, 'data/totals.json'), 'r').read()
application_response = open(os.path.join(dir_, 'data/application.json'), 'r').read()

registration = '{"new_registrations": [512344]}'
multi_name_reg = '{"new_registrations": [512344, 512345]}'


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
        self.app = app.test_client()

    @mock.patch('requests.get', return_value= FakeResponse('stuff', 200, total_response))
    def test_get_totals(self, mock_get):
        response = self.app.get('/')
        assert response.status_code == 200


    @mock.patch('requests.get', side_effect=Exception('Fail'))
    def test_get_totals_fail(self, mock_connect):
        response = self.app.get('/')
        assert response.status_code == 200


    @mock.patch('requests.get', return_value= FakeResponse('stuff', 200, total_response))
    def test_get_list(self, mock_get):
        response = self.app.get('/get_list?appn=bank_regn')
        assert response.status_code == 200

    @mock.patch('requests.get', side_effect=Exception('Fail'))
    def test_get_list_fail(self, mock_connect):
        response = self.app.get('/get_list?appn=bank_regn')
        assert response.status_code == 200

    @mock.patch('requests.get', return_value= FakeResponse('stuff', 200, application_response))
    def test_get_appliction(self, mock_get):
        response = self.app.get('/get_application/pab/1')
        assert response.status_code == 200

    @mock.patch('requests.get', side_effect=Exception('Fail'))
    def test_get_appliction_fail(self, mock_get):
        response = self.app.get('/get_application/pab/1')
        assert response.status_code == 200

    def test_process_name(self):
        response = self.app.post('/process_banks_name', data=dict(forename='John', occupation='', surname='Smith'))
        assert ('John' in response.data.decode())

    def test_multi_forename(self):
        response = self.app.post('/process_banks_name', data=dict(forename='John James', occupation='', surname='Smith'))
        assert ('John' in response.data.decode())
        assert ('James' in response.data.decode())

    def test_alias_name(self):
        response = self.app.post('/process_banks_name',
                                 data=dict(forename='John James', occupation='',surname='Smith',
                                           aliasforename0="Joan Jean", aliassurname0="Smyth",
                                           aliasforename1="John", aliassurname1="Smithers"))
        assert ('Joan' in response.data.decode())
        assert ('Jean' in response.data.decode())
        assert ('Smithers' in response.data.decode())

    def test_process_name_fail(self):
        response = self.app.post('/process_banks_name', data='John')
        assert ('error' in response.data.decode())

    def test_residence_empty(self):
        response = self.app.post('/address', data=test_data.data_no_residence)
        assert ('application' in response.data.decode())
        assert ('John' in response.data.decode())
        assert response.status_code == 200

    def test_address(self):
        response = self.app.post('/address', data=test_data.address)
        assert ('application' in response.data.decode())
        assert ('John' in response.data.decode())
        assert ('North Shore' in response.data.decode())
        assert response.status_code == 200

    def test_addresss_2_lines(self):
        response = self.app.post('/address', data=test_data.address_2_lines)
        assert ('application' in response.data.decode())
        assert ('John' in response.data.decode())
        assert ('North Shore' in response.data.decode())
        assert response.status_code == 200

    def test_additional_address(self):
        response = self.app.post('/address', data=test_data.additional_address)
        assert ('application' in response.data.decode())
        assert ('John' in response.data.decode())
        assert ('Add Address' in response.data.decode())
        assert response.status_code == 200

    def test_residence(self):
        response = self.app.post('/address', data=test_data.residence)
        assert ('application' in response.data.decode())
        assert ('John' in response.data.decode())
        assert response.status_code == 200

    @mock.patch('requests.post', return_value=FakeResponse('stuff', 200))
    def test_pab(self, mock_post):
        response = self.app.post('/court_details', data=test_data.process_pab)
        assert response.status_code == 200

    @mock.patch('requests.post', return_value=FakeResponse('stuff', 200))
    def test_pab(self, mock_post):
        response = self.app.post('/court_details', data=test_data.process_wob)
        assert response.status_code == 200

    @mock.patch('requests.post', return_value=FakeResponse('stuff', 200, registration))
    def test_process_court(self, mock_post):
        response = self.app.post('/court_details', data=test_data.process_court)
        assert response.status_code == 200

    @mock.patch('requests.post', return_value=FakeResponse('stuff', 500, registration))
    def test_process_court_fail(self, mock_post):
        response = self.app.post('/court_details', data=test_data.process_court)
        assert response.status_code == 200

    @mock.patch('requests.post', return_value=FakeResponse('stuff', 200, multi_name_reg))
    def test_multi_name(self, mock_post):
        response = self.app.post('/court_details', data=test_data.multi_name)
        assert response.status_code == 200