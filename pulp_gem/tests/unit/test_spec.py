from pulp_gem.specs import ruby_ver_cmp, ruby_ver_includes


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
