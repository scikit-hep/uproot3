import pytest

import uproot


# export S3_SECRET_ACCESS_KEY=
# export S3_ACCESS_KEY_ID=

# use these by now
# export AWS_ACCESS_KEY_ID=
# export AWS_SECRET_ACCESS_KEY=

URL = "s3http://rgw.fisica.unimi.it/test-ruggero/test.root"

class Test(object):
    def test_s3(self):
        f = uproot.open(URL)
        assert type(f) == uproot.rootio.ROOTDirectory
        histo = f.get("H")
        assert(histo.name == b'H')
