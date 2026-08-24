import pytest

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


@pytest.fixture
def gem_info_file(tmp_path):
    gem_info_file = tmp_path / "geminfo"
    gem_info_file.write_text("""# Ignore this Preamble
---
0.3.1 |checksum:46ee4daadda796c1e9433b45015ff43f67ea47c8cf10e6f224ff5d87126d3302,created_at:2009-08-04T23:57:00Z
0.3.0 |checksum:c90db69e215d0caa267149111284bb35558cf9640bfa03c73317218397df2363,created_at:2009-08-04T23:57:03Z
0.4.0 |checksum:fe921f0123736bf47ddbea0ea4714b6f5666fd5aa1929e2d916437b3bb028080,rubygems:>= 1.3.5,created_at:2009-08-19T05:33:25Z
0.4.1 |checksum:e9265ccb8c92eb64a530165449028791e30b27b8fbc302ac83b8d351f8ee90d4,rubygems:>= 1.3.5,created_at:2009-08-20T05:37:18Z
0.7.3.pre |checksum:d867e96bf15e396337d462f89e83732ad4c92868fa760f6c840e5837c07b0196,rubygems:>= 1.3.5,created_at:2010-01-03T21:41:32Z
1.1.rc.8 |checksum:a2a51612aa484af260597733889f174db984813809770927acecd27a71da5018,ruby:>= 1.8.7,rubygems:>= 1.3.6,created_at:2012-03-03T09:56:16Z
1.1.0 |checksum:e1075ee2a6d1e6460d80ef1421db686e08885286bc3db9216f1abc7ee20d3a2d,ruby:>= 1.8.7,rubygems:>= 1.3.6,created_at:2012-03-07T20:30:57Z
""")
    return gem_info_file


@pytest.mark.asyncio
async def test_read_info_with_empty_filter_returns_nothing(gem_info_file):
    result = [gi async for gi in read_info(gem_info_file, {})]
    assert result == []


@pytest.mark.asyncio
async def test_read_info_emits_gem_info_for_matching_versions(gem_info_file):
    result = [
        gi
        async for gi in read_info(
            gem_info_file, {"1.0.0": {"name": "bundler"}, "1.1.0": {"name": "bundler"}}
        )
    ]
    assert result == [
        {
            "name": "bundler",
            "checksum": "e1075ee2a6d1e6460d80ef1421db686e08885286bc3db9216f1abc7ee20d3a2d",
            "required_ruby_version": ">= 1.8.7",
            "required_rubygems_version": ">= 1.3.6",
        }
    ]
