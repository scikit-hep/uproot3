import unittest
import pytest

import uproot

from requests.exceptions import HTTPError


class Test(unittest.TestCase):
    url = "http://scikit-hep.org/uproot/examples/HZZ.root"
    url_auth = "http://scikit-hep.org/uproot/examples/HZZ.root"
    auth = ("scikit-hep", "uproot")

    def test_no_auth_needed_no_auth(self):
        f = uproot.open(self.url)
        assert type(f) == uproot.rootio.ROOTDirectory

    def test_no_auth_needed_with_auth(self):
        f = uproot.open(self.url, httpsource={"auth": self.auth})
        assert type(f) == uproot.rootio.ROOTDirectory

    def test_auth_needed_no_auth(self):
        with pytest.raises(HTTPError):
            f = uproot.open(self.url_auth)
        assert context_manager.exception.response.status_code == 401

    def test_auth_needed_correct_auth(self):
        f = uproot.open(self.url_auth, httpsource={"auth": self.auth})
        assert type(f) == uproot.rootio.ROOTDirectory

    def test_auth_needed_wrong_auth(self):
        with pytest.raises(HTTPError):
            f = uproot.open(self.url_auth, httpsource={"auth": ("", "")})
        assert context_manager.exception.response.status_code == 401
