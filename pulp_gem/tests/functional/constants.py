# coding=utf-8
from urllib.parse import urljoin

from pulp_smash.constants import PULP_FIXTURES_BASE_URL
from pulp_smash.pulp3.constants import (
    BASE_PUBLISHER_PATH,
    BASE_REMOTE_PATH,
    CONTENT_PATH
)

# FIXME: replace 'unit' with your own content type names, and duplicate as necessary for each type
GEM_CONTENT_PATH = urljoin(CONTENT_PATH, 'gem/units/')

GEM_REMOTE_PATH = urljoin(BASE_REMOTE_PATH, 'gem/')

GEM_PUBLISHER_PATH = urljoin(BASE_PUBLISHER_PATH, 'gem/')


# FIXME: replace this with your own fixture repository URL and metadata
# GEM_FIXTURE_URL = urljoin(PULP_FIXTURES_BASE_URL, 'gem/')
GEM_FIXTURE_URL = 'https://repos.fedorapeople.org/pulp/pulp/demo_repos/gems/repo/'

# FIXME: replace this with the actual number of content units in your test fixture
GEM_FIXTURE_COUNT = 3

# FIXME: replace this with the location of one specific content unit of your choosing
GEM_URL = urljoin(GEM_FIXTURE_URL, '')

# FIXME: replace this iwth your own fixture repository URL and metadata
GEM_LARGE_FIXTURE_URL = urljoin(PULP_FIXTURES_BASE_URL, 'gem_large/')

# FIXME: replace this with the actual number of content units in your test fixture
GEM_LARGE_FIXTURE_COUNT = 25
