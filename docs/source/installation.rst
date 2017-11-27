Installing uproot
=================

`uproot is on PyPI <https://pypi.python.org/pypi/uproot/>`_, so install it with

.. code-block:: bash

    pip install uproot --user

or your preferred variation.

You can also get the latest from GitHub.

.. code-block:: bash

    git clone https://github.com/scikit-hep/uproot.git
    python setup.py install --user           

New features are developed in git branches that first merge into git ``master``, then get released to PyPI. Therefore non-``master`` branches are experimental, the ``master`` branch is bleeding edge but usually not broken, and pip-installation is for production use.
