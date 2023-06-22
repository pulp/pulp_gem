Synchronize a Repository
========================

Users can populate their repositories with content from an external sources by syncing
their repository.

Create a Repository
-------------------

Start by creating a new repository named "foo"

.. literalinclude:: ../_scripts/repo.sh
   :language: bash

Response::

    {
      "pulp_href": "/pulp/api/v3/repositories/gem/gem/0188e4e3-1429-7411-89d7-c87288edf51a/",
      "pulp_created": "2023-06-22T20:54:27.113947Z",
      "versions_href": "/pulp/api/v3/repositories/gem/gem/0188e4e3-1429-7411-89d7-c87288edf51a/versions/",
      "pulp_labels": {},
      "latest_version_href": "/pulp/api/v3/repositories/gem/gem/0188e4e3-1429-7411-89d7-c87288edf51a/versions/0/",
      "name": "foo",
      "description": null,
      "retain_repo_versions": null,
      "remote": null
    }

Create a Remote
---------------

Creating a remote object informs Pulp about an external content source.

.. literalinclude:: ../_scripts/remote.sh
   :language: bash

Response::

  {
      "pulp_href": "/pulp/api/v3/remotes/gem/gem/0188e505-157c-7565-8474-e607e0dbc4a0/",
      "pulp_created": "2023-06-22T21:31:35.676442Z",
      "name": "gem",
      "url": "https://index.rubygems.org",
      "ca_cert": null,
      "client_cert": null,
      "tls_validation": true,
      "proxy_url": null,
      "pulp_labels": {},
      "pulp_last_updated": "2023-06-22T21:31:35.676454Z",
      "download_concurrency": null,
      "max_retries": null,
      "policy": "immediate",
      "total_timeout": null,
      "connect_timeout": null,
      "sock_connect_timeout": null,
      "sock_read_timeout": null,
      "headers": null,
      "rate_limit": null,
      "hidden_fields": [...],
      "prereleases": false,
      "includes": {
        "panda": null
      },
      "excludes": null
  }

.. note::

    You can also not specify anything in `includes` and have Pulp try to sync all gems available on the remote.

.. note::

    `includes` and `excludes` fields are JSON dictionaries with the key being the gem name and the value being
    the version specifier string, or `null` for syncing all versions.

Sync repository foo with remote
-------------------------------

Use the remote object to kick off a synchronize task by specifying the repository to
sync with. You are telling pulp to fetch content from the remote and add to the repository

.. literalinclude:: ../_scripts/sync.sh
   :language: bash

Repository Version Show Response (when complete)::

    {
      "pulp_href": "/pulp/api/v3/repositories/gem/gem/0188e4e3-1429-7411-89d7-c87288edf51a/versions/1/",
      "pulp_created": "2023-06-22T21:40:00.488466Z",
      "number": 1,
      "repository": "/pulp/api/v3/repositories/gem/gem/0188e4e3-1429-7411-89d7-c87288edf51a/",
      "base_version": null,
      "content_summary": {
        "added": {
          "gem.gem": {
            "count": 33,
            "href": "/pulp/api/v3/content/gem/gem/?repository_version_added=/pulp/api/v3/repositories/gem/gem/0188e4e3-1429-7411-89d7-c87288edf51a/versions/1/"
          }
        },
        "removed": {},
        "present": {
          "gem.gem": {
            "count": 33,
            "href": "/pulp/api/v3/content/gem/gem/?repository_version=/pulp/api/v3/repositories/gem/gem/0188e4e3-1429-7411-89d7-c87288edf51a/versions/1/"
          }
        }
      }
    }
