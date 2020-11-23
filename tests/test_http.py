#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot3/blob/master/LICENSE

import pytest
import mock
HTTPError = pytest.importorskip('requests.exceptions').HTTPError

import uproot3

FILE = "foriter"
LOCAL = "tests/samples/{FILE}.root".format(FILE=FILE)
URL = "http://scikit-hep.org/uproot3/examples/{FILE}.root".format(FILE=FILE)
URL_AUTH = "http://scikit-hep.org/uproot3/authentication/{FILE}.root".format(FILE=FILE)
AUTH = ("scikit-hep", "uproot3")

def mock_get_local_instead_of_http(url="", headers={}, auth=None, **kwargs):
    class MockResponse:
        def __init__(self, status_code):
            self.status_code = status_code
            if self.status_code == 200:
                with open(LOCAL, "rb") as f:
                    self.content = f.read()
                self.headers = {"Content-Range": str(len(self.content))}

        def raise_for_status(self):
            if self.status_code == 401:  # Authentication Error
                raise HTTPError
            elif self.status_code == 200:  # Ok
                pass

    if url == URL:
        return MockResponse(200)
    elif url == URL_AUTH and auth == None:
        return MockResponse(401)
    elif url == URL_AUTH and auth == AUTH:
        return MockResponse(200)
    elif url == URL_AUTH:
        return MockResponse(401)

@mock.patch("requests.get", mock_get_local_instead_of_http)
class Test(object):
    def test_no_auth_needed_no_auth(self):
        f = uproot3.open(URL)
        assert type(f) == uproot3.rootio.ROOTDirectory

    def test_no_auth_needed_with_auth(self):
        f = uproot3.open(URL, httpsource={"auth": AUTH})
        assert type(f) == uproot3.rootio.ROOTDirectory

    def test_auth_needed_no_auth(self):
        with pytest.raises(HTTPError):
            f = uproot3.open(URL_AUTH)

    def test_auth_needed_correct_auth(self):
        f = uproot3.open(URL_AUTH, httpsource={"auth": AUTH})
        assert type(f) == uproot3.rootio.ROOTDirectory

    def test_auth_needed_wrong_auth(self):
        with pytest.raises(HTTPError):
            f = uproot3.open(URL_AUTH, httpsource={"auth": ("", "")})
