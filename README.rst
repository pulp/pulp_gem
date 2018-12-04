.. image:: https://travis-ci.org/ATIX-AG/pulp_gem.svg?branch=master
    :target: https://travis-ci.org/ATIX-AG/pulp_gem

``pulp_gem`` Plugin
===================

This is the ``pulp_gem`` Plugin for `Pulp Project
3.0+ <https://pypi.python.org/pypi/pulpcore/>`__. This plugin adds importers and distributors
for rubygems.

All REST API examples below use `httpie <https://httpie.org/doc>`__ to perform the requests.
The ``httpie`` commands below assume that the user executing the commands has a ``.netrc`` file
in the home directory. The ``.netrc`` should have the following configuration:

.. code-block::

    machine localhost
    login admin
    password admin

If you configured the ``admin`` user with a different password, adjust the configuration
accordingly. If you prefer to specify the username and password with each request, please see
``httpie`` documentation on how to do that.

This documentation makes use of the `jq library <https://stedolan.github.io/jq/>`_
to parse the json received from requests, in order to get the unique urls generated
when objects are created. To follow this documentation as-is please install the jq
library with:

``$ sudo dnf install jq``

Install ``pulpcore``
--------------------

Follow the `installation
instructions <https://docs.pulpproject.org/en/3.0/nightly/installation/instructions.html>`__
provided with pulpcore.

Install ``pulp-gem`` from source
--------------------------------

1)  sudo -u pulp -i
2)  source ~/pulpvenv/bin/activate
3)  git clone https://github.com/ATIX-AG/pulp_gem
4)  cd pulp\_gem
5)  python setup.py develop
6)  pulp-manager makemigrations pulp\_gem
7)  pulp-manager migrate pulp\_gem
8)  django-admin runserver
9)  sudo systemctl restart pulp\_resource\_manager
10) sudo systemctl restart pulp\_worker@1
11) sudo systemctl restart pulp\_worker@2

Install ``pulp-gem`` From PyPI
------------------------------

1) sudo -u pulp -i
2) source ~/pulpvenv/bin/activate
3) pip install pulp-gem
4) pulp-manager makemigrations pulp\_gem
5) pulp-manager migrate pulp\_gem
6) django-admin runserver
7) sudo systemctl restart pulp\_resource\_manager
8) sudo systemctl restart pulp\_worker@1
9) sudo systemctl restart pulp\_worker@2

Create a repository ``foo``
---------------------------

``$ http POST http://localhost:8000/pulp/api/v3/repositories/ name=foo``

.. code:: json

    {
        "_href": "/pulp/api/v3/repositories/1/",
        "...": "..."
    }

``$ export REPO_HREF=$(http :8000/pulp/api/v3/repositories/ | jq -r '.results[] | select(.name == "foo") | ._href')``

Add a remote
------------

``$ http POST http://localhost:8000/pulp/api/v3/remotes/gem/ name='bar' url='https://rubygems.org/'``

.. code:: json

    {
        "_href": "/pulp/api/v3/remotes/gem/1/",
        "..." : "..."
    }

``$ export REMOTE_HREF=$(http :8000/pulp/api/v3/remotes/gem/ | jq -r '.results[] | select(.name == "bar") | ._href')``

Sync repository ``foo`` using remote ``bar``
--------------------------------------------

``$ http POST ':8000'${REMOTE_HREF}'sync/' repository=$REPO_HREF``

Upload ``foo-0.0.1.gem`` to Pulp
--------------------------------

Create an Artifact by uploading the gemfile to Pulp.

``$ http --form POST http://localhost:8000/pulp/api/v3/artifacts/ file@./foo-0.0.1.gem``

.. code:: json

    {
        "_href": "/pulp/api/v3/artifacts/1/",
        "...": "..."
    }

You need to upload the corresponding ``foo-0.0.1.gemspec.rz`` in the same way.

Create ``gem`` content from an Artifact
---------------------------------------

``$ http POST http://localhost:8000/pulp/api/v3/content/gem/gems/ artifact="/pulp/api/v3/artifacts/1/"``

.. code:: json

    {
        "_href": "/pulp/api/v3/content/gem/gems/1/",
        "artifacts": {
            "gems/foo-0.0.1.gem":"/pulp/api/v3/artifacts/1/",
            "quick/Marshal.4.8/foo-0.0.1.gemspec.rz":"/pulp/api/v3/artifacts/2/"
        },
        "name": "foo",
        "notes": {},
        "type": "gem",
        "version": "0.0.1"
    }

``$ export CONTENT_HREF=$(http :8000/pulp/api/v3/content/gem/gems/ | jq -r '.results[] | select(.name == "foo") | ._href')``
