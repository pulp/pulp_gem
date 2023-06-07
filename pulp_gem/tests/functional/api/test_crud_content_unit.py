"""Tests that perform actions over content unit."""
import pytest
import uuid

from pulp_gem.tests.functional.constants import GEM_URL


def test_crud_content_unit(
    gem_content_api_client,
    artifacts_api_client,
    gen_object_with_cleanup,
    http_get,
    monitor_task,
    tmp_path,
    delete_orphans_pre,
):
    """CRUD content unit."""
    # 01 test create
    temp_file = tmp_path / str(uuid.uuid4())
    content = http_get(GEM_URL)
    temp_file.write_bytes(content)
    artifact = gen_object_with_cleanup(artifacts_api_client, temp_file)
    response = gem_content_api_client.create(artifact=artifact.pulp_href)
    task = monitor_task(response.task)
    assert len(task.created_resources) == 1

    # 02 test read by href
    content = gem_content_api_client.read(task.created_resources[0])

    assert content.name == "amber"
    assert content.version == "1.0.0"

    # 03 test read(list) by name & version
    results = gem_content_api_client.list(name="amber", version="1.0.0")
    assert results.count == 1
    assert results.results[0] == content

    # 04 test partial update fails
    with pytest.raises(AttributeError) as exc:
        gem_content_api_client.partial_update(content.pulp_href, relative_path=str("amber2"))
    assert exc.value.args[0] == "'ContentGemApi' object has no attribute 'partial_update'"

    # 05 test full update fails
    with pytest.raises(AttributeError) as exc:
        gem_content_api_client.update(content.pulp_href, relative_path="amber2")
    assert exc.value.args[0] == "'ContentGemApi' object has no attribute 'update'"

    # 06 test delete fails
    with pytest.raises(AttributeError) as exc:
        gem_content_api_client.destroy(content.pulp_href)
    assert exc.value.args[0] == "'ContentGemApi' object has no attribute 'destroy'"
