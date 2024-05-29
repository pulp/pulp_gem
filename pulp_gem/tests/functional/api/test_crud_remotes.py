"""Tests that CRUD gem remotes."""

import pytest
import uuid
from random import choice


from pulpcore.client.pulp_gem import ApiException
from pulp_gem.tests.functional.constants import DOWNLOAD_POLICIES, GEM_FIXTURE_URL


@pytest.mark.parallel
def test_crud_remotes(gem_bindings, gem_remote_factory, monitor_task):
    """CRUD Remotes."""
    # 01 test create
    remote = gem_remote_factory()
    assert remote.policy == "immediate"
    assert remote.url == GEM_FIXTURE_URL

    # 02 test create w/ same name
    body = {"url": remote.url, "policy": remote.policy, "name": remote.name}
    with pytest.raises(ApiException) as exc:
        gem_bindings.RemotesGemApi.create(body)

    assert exc.value.status == 400
    assert "name" in exc.value.body

    # 03 test read remote
    remote2 = gem_bindings.RemotesGemApi.read(remote.pulp_href)
    assert remote == remote2

    # 04 test read(list) remote by name
    result = gem_bindings.RemotesGemApi.list(name=remote.name)
    assert result.count == 1
    assert result.results[0] == remote

    # 05 test partial update
    update_body = _gen_verbose_options()
    result = gem_bindings.RemotesGemApi.partial_update(remote.pulp_href, update_body)
    monitor_task(result.task)
    updated_remote = gem_bindings.RemotesGemApi.read(remote.pulp_href)

    assert updated_remote.name == remote.name
    assert updated_remote.url == remote.url
    hidden_fields = [f.name for f in updated_remote.hidden_fields if f.is_set]
    assert "username" in hidden_fields
    assert "password" in hidden_fields
    assert updated_remote.policy == update_body["policy"]

    # 06 test full update
    update_body = _gen_verbose_options(name=str(uuid.uuid4()), url="http://testing")
    result = gem_bindings.RemotesGemApi.update(remote.pulp_href, update_body)
    monitor_task(result.task)
    updated_remote = gem_bindings.RemotesGemApi.read(remote.pulp_href)

    assert updated_remote.name == update_body["name"]
    assert updated_remote.url == update_body["url"]
    hidden_fields = [f.name for f in updated_remote.hidden_fields if f.is_set]
    assert "username" in hidden_fields
    assert "password" in hidden_fields
    assert updated_remote.policy == update_body["policy"]

    # 07 test delete
    result = gem_bindings.RemotesGemApi.delete(remote.pulp_href)
    monitor_task(result.task)
    with pytest.raises(ApiException) as exc:
        gem_bindings.RemotesGemApi.read(remote.pulp_href)

    assert exc.value.status == 404


def _gen_verbose_options(**kwargs):
    """Return a semi-random dict for use in defining a remote."""
    attrs = {
        "password": str(uuid.uuid4()),
        "username": str(uuid.uuid4()),
        "policy": choice(DOWNLOAD_POLICIES),
    }
    attrs.update(kwargs)
    return attrs
