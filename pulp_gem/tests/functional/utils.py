# coding=utf-8
"""Utilities for tests for the gem plugin."""
from functools import partial
from unittest import SkipTest

from pulp_smash import api, selectors
from pulp_smash.pulp3.constants import (
    REPO_PATH
)
from pulp_smash.pulp3.utils import (
    gen_remote,
    gen_repo,
    gen_publisher,
    get_content,
    require_pulp_3,
    require_pulp_plugins,
    sync
)

from pulp_gem.tests.functional.constants import (
    GEM_CONTENT_NAME,
    GEM_CONTENT_PATH,
    GEM_FIXTURE_URL,
    GEM_REMOTE_PATH,
)


def set_up_module():
    """Skip tests Pulp 3 isn't under test or if pulp_gem isn't installed."""
    require_pulp_3(SkipTest)
    require_pulp_plugins({'pulp_gem'}, SkipTest)


def gen_gem_remote(**kwargs):
    """Return a semi-random dict for use in creating a gem Remote.

    :param url: The URL of an external content source.
    """
    remote = gen_remote(GEM_FIXTURE_URL)
    gem_extra_fields = {
        **kwargs
    }
    remote.update(**gem_extra_fields)
    return remote


def gen_gem_publisher(**kwargs):
    """Return a semi-random dict for use in creating a Remote.

    :param url: The URL of an external content source.
    """
    publisher = gen_publisher()
    gem_extra_fields = {
        **kwargs
    }
    publisher.update(**gem_extra_fields)
    return publisher


def get_gem_content_paths(repo):
    """Return the relative path of content units present in a gem repository.

    :param repo: A dict of information about the repository.
    :returns: A list with the paths of units present in a given repository.
    """
    return [
        "gems/{}-{}.gem".format(content_unit['name'], content_unit['version'])
        for content_unit in get_content(repo)[GEM_CONTENT_NAME]
    ]


def gen_gem_content_attrs(artifact):
    """Generate a dict with content unit attributes for create.

    :param: artifact: A dict of info about the artifact.
    :returns: A semi-random dict for use in creating a content unit.
    """
    return {'artifact': artifact['_href']}


def gen_gem_content_verify_attrs(artifact):
    """Generate a dict with content unit attributes for verification.

    :param: artifact: A dict of info about the artifact.
    :returns: A dict for use in verifying a content unit.
    """
    # TODO get more information about that file
    return {'type': 'gem'}


def populate_pulp(cfg, url=GEM_FIXTURE_URL):
    """Add gem contents to Pulp.

    :param pulp_smash.config.PulpSmashConfig: Information about a Pulp application.
    :param url: The gem repository URL. Defaults to
        :data:`pulp_smash.constants.GEM_FIXTURE_URL`
    :returns: A list of dicts, where each dict describes one file content in Pulp.
    """
    client = api.Client(cfg, api.json_handler)
    remote = {}
    repo = {}
    try:
        remote.update(client.post(GEM_REMOTE_PATH, gen_gem_remote(url)))
        repo.update(client.post(REPO_PATH, gen_repo()))
        sync(cfg, remote, repo)
    finally:
        if remote:
            client.delete(remote['_href'])
        if repo:
            client.delete(repo['_href'])
    return client.get(GEM_CONTENT_PATH)['results']


skip_if = partial(selectors.skip_if, exc=SkipTest)
"""The ``@skip_if`` decorator, customized for unittest.

:func:`pulp_smash.selectors.skip_if` is test runner agnostic. This function is
identical, except that ``exc`` has been set to ``unittest.SkipTest``.
"""
