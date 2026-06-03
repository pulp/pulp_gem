import asyncio

from pulp_gem.specs import read_info, ruby_ver_cmp, ruby_ver_includes


def test_version_cmp():
    assert ruby_ver_cmp("0.0.0", "0") == 0
    assert ruby_ver_cmp("0", "0.0.0") == 0
    assert ruby_ver_cmp("1.0.0", "0") == 1
    assert ruby_ver_cmp("0", "1.0.0") == -1
    assert ruby_ver_cmp("1a", "1.a") == 0
    assert ruby_ver_cmp("1.0", "1.a") == 1
    assert ruby_ver_cmp("1.0", "1.0a") == 1
    assert ruby_ver_cmp("1.0a2", "1.0.a.1") == 1
    assert ruby_ver_cmp("1.0b1", "1.0.a.2") == 1


def test_version_includes():
    assert ruby_ver_includes(">= 1&< 3", "1.0.0")
    assert ruby_ver_includes(">= 1&< 3", "2.0.0")
    assert not ruby_ver_includes(">= 1&< 3", "3.0.0")
    assert ruby_ver_includes(">= 1&< 3", "1.5.a0")
    assert ruby_ver_includes(">= 1&< 3", "3.0.0a5")
    assert not ruby_ver_includes(">= 1&< 3", "3.0.1a5")


def test_read_info_colon_in_value(tmp_path):
    info_file = tmp_path / "info"
    info_file.write_text(
        "---\n7.0.1 activesupport:= 7.0.1|checksum:abc123,ruby:>= 2.7.0,rubygems:>= 1.8.11\n"
    )
    versions_info = {"7.0.1": {"version": "7.0.1", "platform": "ruby", "prerelease": False}}

    async def _collect():
        return [info async for info in read_info(str(info_file), versions_info)]

    results = asyncio.run(_collect())
    assert len(results) == 1
    assert results[0]["checksum"] == "abc123"
    assert results[0]["required_ruby_version"] == ">= 2.7.0"
    assert results[0]["required_rubygems_version"] == ">= 1.8.11"
    assert results[0]["dependencies"] == {"activesupport": "= 7.0.1"}
