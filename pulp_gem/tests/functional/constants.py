# coding=utf-8
"""Constants for Pulp Gem plugin tests."""
from urllib.parse import urljoin

from pulp_smash.constants import PULP_FIXTURES_BASE_URL
from pulp_smash.pulp3.constants import (
    BASE_CONTENT_PATH,
    BASE_DISTRIBUTION_PATH,
    BASE_PUBLICATION_PATH,
    BASE_REMOTE_PATH,
    BASE_REPO_PATH,
)


DOWNLOAD_POLICIES = ["immediate", "streamed", "on_demand"]

GEM_CONTENT_NAME = "gem.gem"

GEM_CONTENT_PATH = urljoin(BASE_CONTENT_PATH, "gem/gem/")

GEM_DISTRIBUTION_PATH = urljoin(BASE_DISTRIBUTION_PATH, "gem/gem/")

GEM_REMOTE_PATH = urljoin(BASE_REMOTE_PATH, "gem/gem/")

GEM_REPO_PATH = urljoin(BASE_REPO_PATH, "gem/gem/")

GEM_PUBLICATION_PATH = urljoin(BASE_PUBLICATION_PATH, "gem/gem/")

GEM_FIXTURE_URL = urljoin(PULP_FIXTURES_BASE_URL, "gem/")
"""The URL to a gem repository."""

GEM_FIXTURE_COUNT = 4
"""The number of content units available at :data:`GEM_FIXTURE_URL`."""
# This is 4 stable gems. There are also 2 prerelease gems not currently synced.

GEM_FIXTURE_SUMMARY = {GEM_CONTENT_NAME: GEM_FIXTURE_COUNT}
"""The desired content summary after syncing :data:`GEM_FIXTURE_URL`."""

GEM_URL = urljoin(GEM_FIXTURE_URL, "gems/amber-1.0.0.gem")
"""The URL to an gem file at :data:`GEM_FIXTURE_URL`."""

# FIXME: replace this with your own fixture repository URL and metadata
GEM_INVALID_FIXTURE_URL = urljoin(PULP_FIXTURES_BASE_URL, "gem-invalid/")
"""The URL to an invalid gem repository."""

# FIXME: replace this with your own fixture repository URL and metadata
GEM_LARGE_FIXTURE_URL = urljoin(PULP_FIXTURES_BASE_URL, "gem_large/")
"""The URL to a gem repository containing a large number of content units."""

# FIXME: replace this with the actual number of content units in your test fixture
GEM_LARGE_FIXTURE_COUNT = 25
"""The number of content units available at :data:`GEM_LARGE_FIXTURE_URL`."""
