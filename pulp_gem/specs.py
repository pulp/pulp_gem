from collections import namedtuple
from logging import getLogger

import aiofiles
import datetime
import zlib
import gzip
import re
import yaml
from itertools import zip_longest
from tarfile import TarFile

import rubymarshal.classes
import rubymarshal.writer
import rubymarshal.reader


log = getLogger(__name__)

NAME_REGEX = re.compile(r"[\w\.-]+")
VERSION_REGEX = re.compile(r"\d+(?:\.\d+)*")
PRERELEASE_VERSION_REGEX = NAME_REGEX

GemKey = namedtuple("GemKey", ("name", "version", "platform"))


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


def split_ext_version(ext_version):
    """Returns the tuple (version, platform, prerelease)."""
    if "-" in ext_version:
        version, platform = ext_version.split("-", maxsplit=1)
    else:
        version, platform = ext_version, "ruby"
    prerelease = not VERSION_REGEX.fullmatch(version)
    return {"version": version, "platform": platform, "prerelease": prerelease}


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
            # Dirty trick to make the md5sum default to None
            split_line = line.split(" ", maxsplit=2) + [None]
            name = split_line[0]
            versions_str = split_line[1]
            md5_sum = split_line[2]
            ext_versions = versions_str.split(",")
            entry = results.get(name) or ([], "")
            results[name] = (entry[0] + ext_versions, md5_sum)
    for name, (ext_versions, md5_sum) in results.items():
        # Sanitize name
        if not NAME_REGEX.fullmatch(name):
            raise ValueError(f"Invalid gem name: {name}")
        yield name, ext_versions, md5_sum


async def read_info(relative_path, versions_info):
    """
    Emit gem_info entries from the info file when they exist in versions_info.

    The resulting gem_info dicts are missing the "name" field.
    """
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
            front, back = line.split("|")
            ext_version, dependencies = front.split(" ", maxsplit=1)
            if ext_version not in versions_info:
                continue

            gem_info = versions_info[ext_version]  # version, platform, prerelease
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


class GemVersion(rubymarshal.classes.UsrMarshal):
    ruby_class_name = "Gem::Version"

    @classmethod
    def yaml_constructor(cls, loader, node):
        result = cls()
        yield result
        values = loader.construct_mapping(node, deep=True)
        result.marshal_load([values["version"]])

    @property
    def version(self):
        return self._private_data[0]

    def __repr__(self):
        return f"{self.ruby_class_name}('{self.version}')"

    def __str__(self):
        return f"{self.ruby_class_name}('{self.version}')"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._private_data == self._private_data


class GemSpecification(rubymarshal.classes.UserDef):
    ruby_class_name = "Gem::Specification"

    FIELDS = [
        "rubygems_version",
        "specification_version",
        "name",
        "version",
        "date",
        "summary",
        "required_ruby_version",
        "required_rubygems_version",
        "original_platform",
        "dependencies",
        "rubyforge_project",  # This got removed...
        "email",
        "authors",
        "description",
        "homepage",
        "has_rdoc",
        "new_platform",
        "licenses",
        "metadata",
    ]

    @classmethod
    def yaml_constructor(cls, loader, node):
        result = cls()
        yield result

        value = loader.construct_mapping(node, deep=True)
        platform = value.pop("platform")
        value.setdefault("original_platform", platform)
        value.setdefault("new_platform", platform)
        value.setdefault("has_rdoc", True)
        value.setdefault("rubyforge_project", "")
        value["date"] = RubyTime.from_datetime(value["date"])
        result._private_data = {key: value.get(key) for key in cls.FIELDS}

    @property
    def platform(self):
        return self._private_data["new_platform"]

    def _load(self, data):
        arguments = rubymarshal.reader.loads(data)
        self._private_data = {name: value for name, value in zip(self.FIELDS, arguments)}

    def _dump(self):
        count = len(self._private_data)
        arguments = [
            self._private_data[name] if name is not None else "" for name in self.FIELDS[:count]
        ]
        return rubymarshal.writer.writes(arguments)


class GemRequirement(rubymarshal.classes.UsrMarshal):
    ruby_class_name = "Gem::Requirement"

    @classmethod
    def yaml_constructor(cls, loader, node):
        result = cls()
        yield result
        values = loader.construct_mapping(node, deep=True)
        result.marshal_load([values["requirements"]])

    @property
    def requirements(self):
        return self._private_data[0]

    def __repr__(self):
        return f"{self.ruby_class_name}('{self.requirements}')"

    def __str__(self):
        return f"{self.ruby_class_name}('{self.requirements}')"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._private_data == self._private_data

    def to_s(self):
        return "&".join([f"{req[0]} {req[1].version}" for req in self.requirements])


class GemDependency(rubymarshal.classes.RubyObject):
    ruby_class_name = "Gem::Dependency"

    @classmethod
    def yaml_constructor(cls, loader, node):
        result = cls()
        yield result
        values = loader.construct_mapping(node, deep=True)
        result.attributes = {f"@{key}": value for key, value in values.items()}
        result.attributes["@type"] = rubymarshal.classes.Symbol(result.attributes["@type"][1:])

    @property
    def requirement(self):
        # From:
        # File lib/rubygems/dependency.rb, line 116

        # @version_requirements and @version_requirement are legacy ivar
        # names, and supported here because older gems need to keep
        # working and Dependency doesn't implement marshal_dump and
        # marshal_load. In a happier world, this would be an
        # attr_accessor. The horrifying instance_variable_get you see
        # below is also the legacy of some old restructurings.
        #
        # Note also that because of backwards compatibility (loading new
        # gems in an old RubyGems installation), we can't add explicit
        # marshaling to this class until we want to make a big
        # break. Maybe 2.0.
        #
        # Children, define explicit marshal and unmarshal behavior for
        # public classes. Marshal formats are part of your public API.

        if result := self.attributes.get("@requirement"):
            return result
        if version_requirement := self.attributes.pop("@version_requirement", None):
            log.warn(
                "You are attempting to process a really old gem. "
                "If this codepath fails, please report an issue with this gem "
                "so we actually have something to experiment on."
            )
            version = GemVersion()
            version.marshal_load([version_requirement.attributes["@version"]])
            requirement = GemRequirement()
            requirement._private_data[0] = [[">=", version]]
            self.attributes["@version_requirements"] = requirement
        return self.attributes.get("@version_requirements")


class RubyTime(rubymarshal.classes.UserDef):
    ruby_class_name = "Time"

    @classmethod
    def from_datetime(cls, value):
        year_val = value.year - 1900
        month_val = value.month - 1
        assert 0 <= year_val <= 0xFFFF
        result = cls(attributes={"zone": value.tzname()})
        p = 0x80000000 | year_val << 14 | month_val << 10 | value.day << 5 | value.hour
        if value.tzinfo is datetime.timezone.utc:
            p |= 0x40000000
        s = value.minute << 26 | value.second << 20 | value.microsecond
        result._private_data = p.to_bytes(4, "little") + s.to_bytes(4, "little")
        return result


rubymarshal.classes.registry.register(GemVersion)
rubymarshal.classes.registry.register(GemSpecification)
rubymarshal.classes.registry.register(GemRequirement)
rubymarshal.classes.registry.register(GemDependency)
rubymarshal.classes.registry.register(RubyTime)


class RubyMarshalYamlLoader(yaml.SafeLoader):
    pass


def _yaml_ruby_constructor(loader, suffix, node):
    try:
        return rubymarshal.classes.registry[suffix].yaml_constructor(loader, node)
    except KeyError:
        raise NotImplementedError(f"Unknown ruby class {suffix}.")


yaml.add_multi_constructor("!ruby/object:", _yaml_ruby_constructor, Loader=RubyMarshalYamlLoader)


def write_specs(gem_keys, relative_path):
    """
    Write rubygem specs to file.
    """
    specs = [[e.name, GemVersion(e.version), e.platform] for e in gem_keys]
    # write uncompressed version
    with open(relative_path, "wb") as fd:
        rubymarshal.writer.write(fd, specs)


def analyse_gem(file_obj):
    """
    Extract name, version and specdata from gemfile.

    The resulting gem_info is missing the checksum field.
    """
    with TarFile(fileobj=file_obj) as archive:
        with archive.extractfile("metadata.gz") as md_file:
            data = yaml.load(gzip.decompress(md_file.read()), Loader=RubyMarshalYamlLoader)
    gem_info = {
        "name": data._private_data["name"],
        "version": data._private_data["version"].version,
        "platform": data.platform,
    }
    # Sanitize name
    if not NAME_REGEX.fullmatch(gem_info["name"]):
        raise ValueError(f"Invalid gem name: {gem_info['name']}")
    # Sanitize version
    if VERSION_REGEX.fullmatch(gem_info["version"]):
        gem_info["prerelease"] = False
    elif PRERELEASE_VERSION_REGEX.fullmatch(gem_info["version"]):
        gem_info["prerelease"] = True
    else:
        raise ValueError(f"Invalid version string: {gem_info['version']}")
    for key in ("required_ruby_version", "required_rubygems_version"):
        if (requirement := data._private_data.get(key)) is not None:
            gem_info[key] = requirement.to_s()
    if (dependencies := data._private_data.get("dependencies")) is not None:
        gem_info["dependencies"] = {
            dep.attributes["@name"]: dep.requirement.to_s() for dep in dependencies
        }
    zdata = zlib.compress(rubymarshal.writer.writes(data))
    return gem_info, zdata
