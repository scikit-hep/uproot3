#!/usr/bin/env python

import unittest
import sys
import os
import tempfile
import subprocess
import papermill as pm


class Test(unittest.TestCase):
    def runTest(self):
        pass

    @unittest.skipUnless(sys.version_info >= (3, 5), 'requires modern Python')
    def test_notebooks(self):
        output_nb = os.path.join(tempfile.mkdtemp(), 'output.ipynb')
        common_kwargs = {
            'output': str(output_nb),
            'kernel_name': 'python{}'.format(sys.version_info.major)
        }

        subprocess.call('binder/postBuild', shell=True)

        cwd = os.getcwd()
        try:
            os.chdir(os.path.join(cwd, 'binder'))

            pm.execute_notebook('tutorial.ipynb', **common_kwargs)
            pm.execute_notebook('version-3-features.ipynb', **common_kwargs)
        finally:
            os.chdir(cwd)


if __name__ == '__main__':
    unittest.main()
