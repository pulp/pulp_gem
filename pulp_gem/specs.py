from collections import namedtuple

import aiofiles
import zlib
import gzip
import re
import yaml
from itertools import zip_longest
from tarfile import TarFile

import rubymarshal.classes
import rubymarshal.writer
import rubymarshal.reader


NAME_REGEX = re.compile(r"[\w\.-]+")
VERSION_REGEX = re.compile(r"\d+(?:\.\d+)*")
PRERELEASE_VERSION_REGEX = NAME_REGEX

# Natural key.
Key = namedtuple("Key", ("name", "version"))


def _ver_tokens(version):
    numeric = True
    value = ""
    for char in version:
        if char >= "0" and char <= "9":
            if not numeric:
                if value:
                    yield value
                    value = ""
                numeric = True
            value += char
        elif char == ".":
            yield value
            value = ""
            numeric = True
        else:
            if numeric:
                if value:
                    yield value
                    value = ""
                numeric = False
            value += char
    yield value


def ruby_ver_cmp(ver1, ver2):
    # https://docs.ruby-lang.org/en/2.4.0/Gem/Version.html
    for part1, part2 in zip_longest(_ver_tokens(ver1), _ver_tokens(ver2), fillvalue="0"):
        try:
            val1 = [int(part1), ""]
        except ValueError:
            val1 = [-1, part1]
        try:
            val2 = [int(part2), ""]
        except ValueError:
            val2 = [-1, part2]
        if val1 > val2:
            return 1
        if val1 < val2:
            return -1
    return 0


def ruby_ver_includes(requirements, version):
    for requirement in requirements.split("&"):
        op, ver = requirement.split(" ", maxsplit=1)
        cmp = ruby_ver_cmp(version, ver)
        if op == "=" and cmp != 0:
            return False
        elif op == "<" and cmp != -1:
            return False
        elif op == "<=" and cmp == 1:
            return False
        elif op == ">" and cmp != 1:
            return False
        elif op == ">=" and cmp == -1:
            return False
    return True


async def read_versions(relative_path):
    # File starts with:
    #   created_at: <timestamp>
    #   ---
    async with aiofiles.open(relative_path, mode="r") as fp:
        results = {}
        preamble = True
        async for line in fp:
            line = line.strip()
            if line == "---":
                preamble = False
                continue
            if preamble:
                continue
            name, versions, md5_sum = line.split(" ", maxsplit=2)
            versions = versions.split(",")
            entry = results.get(name) or ([], "")
            results[name] = (entry[0] + versions, md5_sum)
    for name, (versions, md5_sum) in results.items():
        # Sanitize name
        if not NAME_REGEX.match(name):
            raise ValueError(f"Invalid gem name: {name}")
        yield name, versions, md5_sum


async def read_info(relative_path, versions):
    # File starts with:
    #   ---
    async with aiofiles.open(relative_path, mode="r") as fp:
        preamble = True
        async for line in fp:
            line = line.strip()
            if line == "---":
                preamble = False
                continue
            if preamble:
                continue
            gem_info = {}
            front, back = line.split("|")
            version, dependencies = front.split(" ", maxsplit=1)
            if version not in versions:
                continue
            # Sanitize version
            if VERSION_REGEX.match(version):
                gem_info["prerelease"] = False
            elif PRERELEASE_VERSION_REGEX.match(version):
                gem_info["prerelease"] = True
            else:
                raise ValueError(f"Invalid version string: {version}")
            gem_info["version"] = version
            dependencies = dependencies.strip()
            if dependencies:
                gem_info["dependencies"] = dict(
                    (item.split(":", maxsplit=1) for item in dependencies.split(","))
                )
            for stmt in back.split(","):
                key, value = stmt.split(":")
                if key == "checksum":
                    gem_info["checksum"] = value
                elif key == "ruby":
                    gem_info["required_ruby_version"] = value
                elif key == "rubygems":
                    gem_info["required_rubygems_version"] = value
                else:
                    raise ValueError(f"Invalid requirement: {stmt}")
            yield gem_info


def read_specs(relative_path):
    """
    Read rubygem specs from file.
    """
    try:
        with gzip.GzipFile(relative_path, "rb") as fd:
            data = rubymarshal.reader.load(fd)
    except OSError:
        with open(relative_path, "rb") as fd:
            data = rubymarshal.reader.load(fd)
    for item in data:
        name = item[0]
        if name.__class__ is bytes:
            name = name.decode()
        version = item[1].values[0]
        if version.__class__ is bytes:
            version = version.decode()
        yield Key(name, version)


def write_specs(keys, relative_path):
    """
    Write rubygem specs to file.
    """
    specs = [
        [e.name, rubymarshal.classes.UsrMarshal("Gem::Version", [e.version]), "ruby"] for e in keys
    ]
    # write uncompressed version
    with open(relative_path, "wb") as fd:
        rubymarshal.writer.write(fd, specs)


class RubyMarshalYamlLoader(yaml.SafeLoader):
    pass


def _yaml_ruby_constructor(loader, suffix, node):
    value = loader.construct_mapping(node)
    return rubymarshal.classes.UsrMarshal(suffix, value)


yaml.add_multi_constructor("!ruby/object:", _yaml_ruby_constructor, Loader=RubyMarshalYamlLoader)


def _collapse_requirement(data):
    return "&".join([f"{req[0]} {req[1].values['version']}" for req in data.values["requirements"]])


def analyse_gem(file_obj):
    """
    Extract name, version and specdata from gemfile.
    """
    with TarFile(fileobj=file_obj) as archive:
        with archive.extractfile("metadata.gz") as md_file:
            data = yaml.load(gzip.decompress(md_file.read()), Loader=RubyMarshalYamlLoader)
    gem_info = {
        "name": data.values["name"],
        "version": data.values["version"].values["version"],
    }
    # Sanitize name
    if not NAME_REGEX.match(gem_info["name"]):
        raise ValueError(f"Invalid gem name: {gem_info['name']}")
    # Sanitize version
    if VERSION_REGEX.match(gem_info["version"]):
        gem_info["prerelease"] = False
    elif PRERELEASE_VERSION_REGEX.match(gem_info["version"]):
        gem_info["prerelease"] = True
    else:
        raise ValueError(f"Invalid version string: {gem_info['version']}")
    for key in ("required_ruby_version", "required_rubygems_version"):
        if (requirement := data.values.get(key)) is not None:
            gem_info[key] = _collapse_requirement(requirement)
    if (dependencies := data.values.get("dependencies")) is not None:
        gem_info["dependencies"] = {
            dep.values["name"]: _collapse_requirement(dep.values["requirement"])
            for dep in dependencies
        }
    # Workaroud
    del data.values["date"]
    zdata = zlib.compress(rubymarshal.writer.writes(data))
    return gem_info, zdata
