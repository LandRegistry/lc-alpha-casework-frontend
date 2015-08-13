from application.routes import app
from unittest import mock
import os
import json
import requests

dir_ = os.path.dirname(__file__)
total_response = open(os.path.join(dir_, 'data/totals.json'), 'r').read()
application_response = open(os.path.join(dir_, 'data/application.json'), 'r').read()
name = "{'debtor_name': {'forenames': ['John', 'James'], 'surname': 'Smith'}, 'residence': [], 'occupation': '', 'debtor_alternative_name': []}"
forename = "'forenames': ['John', 'James']"
test_data = [
    {
        "input": "forename='John James', occupation='', surname='Smith'",
        "expected": "{'debtor_name': {'forenames': ['John', 'James'], 'surname': 'Smith'}, 'residence': [], 'occupation': '', 'debtor_alternative_name': []}"
        }
]

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
        data = test_data[0]
        data1 = data['input']
        response = self.app.post('/process_banks_name', data=dict(forename='John James', occupation='', surname='Smith'))
        # assert ("{'residence': [], 'occupation': '', 'debtor_name': {'surname': 'Smith', 'forenames': ['John', 'James']}, 'debtor_alternative_name': []}" in response.data.decode())
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










