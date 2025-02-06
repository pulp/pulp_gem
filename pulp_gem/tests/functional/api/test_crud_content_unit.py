"""Tests that perform actions over content unit."""

import pytest


def test_upload_content_unit(
    gem_bindings,
    gem_content_artifact,
    monitor_task,
    delete_orphans_pre,
):
    response = gem_bindings.ContentGemApi.create(file=str(gem_content_artifact))
    task = monitor_task(response.task)
    assert len(task.created_resources) == 1

    content = gem_bindings.ContentGemApi.read(task.created_resources[0])
    assert content.name == "amber"
    assert content.version == "1.0.0"

    # Upload again
    response = gem_bindings.ContentGemApi.create(file=str(gem_content_artifact))
    task = monitor_task(response.task)
    assert len(task.created_resources) == 1
    assert task.created_resources[0] == content.pulp_href


def test_crud_content_unit(
    pulpcore_bindings,
    gem_bindings,
    gem_content_artifact,
    monitor_task,
    delete_orphans_pre,
):
    """CRUD content unit."""
    # 01 test create
    artifact = pulpcore_bindings.ArtifactsApi.create(file=str(gem_content_artifact))
    response = gem_bindings.ContentGemApi.create(artifact=artifact.pulp_href)
    task = monitor_task(response.task)
    assert len(task.created_resources) == 1

    # 02 test read by href
    content = gem_bindings.ContentGemApi.read(task.created_resources[0])

    assert content.name == "amber"
    assert content.version == "1.0.0"

    # 03 test read(list) by name & version
    results = gem_bindings.ContentGemApi.list(name="amber", version="1.0.0")
    assert results.count == 1
    assert results.results[0] == content

    # 04 test partial update fails
    with pytest.raises(AttributeError) as exc:
        gem_bindings.ContentGemApi.partial_update(content.pulp_href, relative_path=str("amber2"))
    assert exc.value.args[0] == "'ContentGemApi' object has no attribute 'partial_update'"

    # 05 test full update fails
    with pytest.raises(AttributeError) as exc:
        gem_bindings.ContentGemApi.update(content.pulp_href, relative_path="amber2")
    assert exc.value.args[0] == "'ContentGemApi' object has no attribute 'update'"

    # 06 test delete fails
    with pytest.raises(AttributeError) as exc:
        gem_bindings.ContentGemApi.destroy(content.pulp_href)
    assert exc.value.args[0] == "'ContentGemApi' object has no attribute 'destroy'"
