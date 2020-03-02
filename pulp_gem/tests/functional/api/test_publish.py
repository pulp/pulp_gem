# coding=utf-8
"""Tests that publish gem plugin repositories."""
import unittest
from random import choice

from requests.exceptions import HTTPError

from pulp_smash import api, config
from pulp_smash.pulp3.utils import gen_repo, get_content, get_versions, modify_repo, sync

from pulp_gem.tests.functional.constants import (
    GEM_CONTENT_NAME,
    GEM_PUBLICATION_PATH,
    GEM_REMOTE_PATH,
    GEM_REPO_PATH,
)
from pulp_gem.tests.functional.utils import create_gem_publication, gen_gem_remote
from pulp_gem.tests.functional.utils import set_up_module as setUpModule  # noqa:F401


class PublishAnyRepoVersionTestCase(unittest.TestCase):
    """Test whether a particular repository version can be published.

    This test targets the following issues:

    * `Pulp #3324 <https://pulp.plan.io/issues/3324>`_
    * `Pulp Smash #897 <https://github.com/PulpQE/pulp-smash/issues/897>`_
    """

    def test_all(self):
        """Test whether a particular repository version can be published.

        1. Create a repository with at least 2 repository versions.
        2. Create a publication by supplying the latest ``repository_version``.
        3. Assert that the publication ``repository_version`` attribute points
           to the latest repository version.
        4. Create a publication by supplying the non-latest ``repository_version``.
        5. Assert that the publication ``repository_version`` attribute points
           to the supplied repository version.
        6. Assert that an exception is raised when providing two different
           repository versions to be published at same time.
        """
        cfg = config.get_config()
        client = api.Client(cfg, api.json_handler)

        body = gen_gem_remote()
        remote = client.post(GEM_REMOTE_PATH, body)
        self.addCleanup(client.delete, remote["pulp_href"])

        repo = client.post(GEM_REPO_PATH, gen_repo())
        self.addCleanup(client.delete, repo["pulp_href"])

        sync(cfg, remote, repo)

        # Step 1
        repo = client.get(repo["pulp_href"])
        for gem_content in get_content(repo)[GEM_CONTENT_NAME]:
            modify_repo(cfg, repo, remove_units=[gem_content])
        version_hrefs = tuple(ver["pulp_href"] for ver in get_versions(repo))
        non_latest = choice(version_hrefs[:-1])

        # Step 2
        publication = create_gem_publication(cfg, repo)

        # Step 3
        self.assertEqual(publication["repository_version"], version_hrefs[-1])

        # Step 4
        publication = create_gem_publication(cfg, repo, non_latest)

        # Step 5
        self.assertEqual(publication["repository_version"], non_latest)

        # Step 6
        with self.assertRaises(HTTPError):
            body = {"repository": repo["pulp_href"], "repository_version": non_latest}
            client.post(GEM_PUBLICATION_PATH, body)
