from application.routes import app
from unittest import mock
import os
import json


get_totals_result = open(os.path.join(dir, 'data/totals.json'), 'r').read()


class FakeResponse(requests.Response):
    def __init__(self, content='', status_code=200):
        super(FakeResponse, self).__init__()
        self._content = content
        self._content_consumed = True
        self.status_code = status_code




class TestCaseworkFrontend:

    # test for successful registration where debtor has 1 residence
    fake_success = FakeResponse('stuff', 200)


    @mock.patch('requests.post', return_value=fake_success)
    def test_get_totals(self, mock_post):
        headers = {'Content-Type': 'application/json'}
        response = self.app.get('/', data=get_totals_result, headers=headers)
        assert response.status_code == 200
        assert ('pabs' in response.data.decode())





