# coding=utf-8
from urllib.parse import urljoin

from pulp_smash.constants import PULP_FIXTURES_BASE_URL
from pulp_smash.pulp3.constants import (
    BASE_PUBLISHER_PATH,
    BASE_REMOTE_PATH,
    CONTENT_PATH
)


DOWNLOAD_POLICIES = ['immediate', 'streamed', 'on_demand']

GEM_CONTENT_NAME = 'gem'

GEM_CONTENT_PATH = urljoin(CONTENT_PATH, 'gem/gems/')

GEM_REMOTE_PATH = urljoin(BASE_REMOTE_PATH, 'gem/')

GEM_PUBLISHER_PATH = urljoin(BASE_PUBLISHER_PATH, 'gem/')


# GEM_FIXTURE_URL = urljoin(PULP_FIXTURES_BASE_URL, 'gem/')
GEM_FIXTURE_URL = 'https://repos.fedorapeople.org/pulp/pulp/demo_repos/gems/repo/'

GEM_FIXTURE_COUNT = 3

GEM_FIXTURE_SUMMARY = {
    GEM_CONTENT_NAME: GEM_FIXTURE_COUNT
}

GEM_URL = urljoin(GEM_FIXTURE_URL, 'gems/panda-0.1.0.gem')

# FIXME: replace this iwth your own fixture repository URL and metadata
GEM_LARGE_FIXTURE_URL = urljoin(PULP_FIXTURES_BASE_URL, 'gem_large/')

# FIXME: replace this with the actual number of content units in your test fixture
GEM_LARGE_FIXTURE_COUNT = 25
