# coding=utf-8
"""Utilities for tests for the gem plugin."""
from functools import partial
from unittest import SkipTest

from pulp_smash import api, selectors
from pulp_smash.pulp3.utils import (
    gen_remote,
    gen_repo,
    get_content,
    require_pulp_3,
    require_pulp_plugins,
    sync,
)

from pulp_gem.tests.functional.constants import (
    GEM_CONTENT_NAME,
    GEM_CONTENT_PATH,
    GEM_FIXTURE_URL,
    GEM_PUBLICATION_PATH,
    GEM_REMOTE_PATH,
    GEM_REPO_PATH,
)


def set_up_module():
    """Skip tests Pulp 3 isn't under test or if pulp_gem isn't installed."""
    require_pulp_3(SkipTest)
    require_pulp_plugins({"gem"}, SkipTest)


def gen_gem_remote(url=GEM_FIXTURE_URL, **kwargs):
    """Return a semi-random dict for use in creating a gem Remote.

    :param url: The URL of an external content source.
    """
    return gen_remote(url, **kwargs)


def get_gem_content_paths(repo, version_href=None):
    """Return the relative path of content units present in a gem repository.

    :param repo: A dict of information about the repository.
    :param version_href: The repository version to read.
    :returns: A list with the paths of units present in a given repository.
    """
    # FIXME: The "relative_path" is actually a file path and name
    # It's just an example -- this needs to be replaced with an implementation that works
    # for repositories of this content type.
    return [
        "gems/{name}-{version}.gem".format(**content_unit)
        for content_unit in get_content(repo, version_href)[GEM_CONTENT_NAME]
    ]


def gen_gem_content_attrs(artifact):
    """Generate a dict with content unit attributes.

    :param artifact: A dict of info about the artifact.
    :returns: A semi-random dict for use in creating a content unit.
    """
    # FIXME: Add content specific metadata here.
    return {"artifact": artifact["pulp_href"]}


def gen_gem_content_verify_attrs(artifact):
    """Generate a dict with content unit attributes.

    :param artifact: A dict of info about the artifact.
    :returns: A semi-random dict for use in creating a content unit.
    """
    # FIXME: Add content specific metadata here.
    return {}


def populate_pulp(cfg, url=GEM_FIXTURE_URL):
    """Add gem contents to Pulp.

    :param pulp_smash.config.PulpSmashConfig: Information about a Pulp application.
    :param url: The gem repository URL. Defaults to
        :data:`pulp_smash.constants.GEM_FIXTURE_URL`
    :returns: A list of dicts, where each dict describes one gem content in Pulp.
    """
    client = api.Client(cfg, api.json_handler)
    remote = {}
    repo = {}
    try:
        remote.update(client.post(GEM_REMOTE_PATH, gen_gem_remote(url)))
        repo.update(client.post(GEM_REPO_PATH, gen_repo()))
        sync(cfg, remote, repo)
    finally:
        if remote:
            client.delete(remote["pulp_href"])
        if repo:
            client.delete(repo["pulp_href"])
    return client.get(GEM_CONTENT_PATH)["results"]


def create_gem_publication(cfg, repo, version_href=None):
    """Create a gem publication.

    :param pulp_smash.config.PulpSmashConfig cfg: Information about the Pulp
        host.
    :param repo: A dict of information about the repository.
    :param version_href: A href for the repo version to be published.
    :returns: A publication. A dict of information about the just created
        publication.
    """
    if version_href:
        body = {"repository_version": version_href}
    else:
        body = {"repository": repo["pulp_href"]}

    client = api.Client(cfg, api.json_handler)
    call_report = client.post(GEM_PUBLICATION_PATH, body)
    tasks = tuple(api.poll_spawned_tasks(cfg, call_report))
    return client.get(tasks[-1]["created_resources"][0])


skip_if = partial(selectors.skip_if, exc=SkipTest)  # pylint:disable=invalid-name
"""The ``@skip_if`` decorator, customized for unittest.

:func:`pulp_smash.selectors.skip_if` is test runner agnostic. This function is
identical, except that ``exc`` has been set to ``unittest.SkipTest``.
"""
