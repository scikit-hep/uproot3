#!/usr/bin/env python

# Copyright (c) 2019, IRIS-HEP
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import unittest

import pytest
import mock
from requests.exceptions import HTTPError

import uproot

FILE = "foriter"
LOCAL = "tests/samples/{FILE}.root".format(FILE=FILE)
URL = "http://scikit-hep.org/uproot/examples/{FILE}.root".format(FILE=FILE)
URL_AUTH = "http://scikit-hep.org/uproot/authentication/{FILE}.root".format(FILE=FILE)
AUTH = ("scikit-hep", "uproot")

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
class Test(unittest.TestCase):
    def test_no_auth_needed_no_auth(self):
        f = uproot.open(URL)
        assert type(f) == uproot.rootio.ROOTDirectory

    def test_no_auth_needed_with_auth(self):
        f = uproot.open(URL, httpsource={"auth": AUTH})
        assert type(f) == uproot.rootio.ROOTDirectory

    def test_auth_needed_no_auth(self):
        with pytest.raises(HTTPError):
            f = uproot.open(URL_AUTH)

    def test_auth_needed_correct_auth(self):
        f = uproot.open(URL_AUTH, httpsource={"auth": AUTH})
        assert type(f) == uproot.rootio.ROOTDirectory

    def test_auth_needed_wrong_auth(self):
        with pytest.raises(HTTPError):
            f = uproot.open(URL_AUTH, httpsource={"auth": ("", "")})
