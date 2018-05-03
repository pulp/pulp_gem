from collections import namedtuple

import zlib
import gzip
import yaml
from tarfile import TarFile

import rubymarshal.classes
import rubymarshal.writer
import rubymarshal.reader


# Natural key.
Key = namedtuple('Key', ('name', 'version'))


def read_specs(relative_path):
    """
    Read rubygem specs from file.
    """
    try:
        with gzip.GzipFile(relative_path, 'rb') as fd:
            data = rubymarshal.reader.load(fd)
    except OSError:
        with open(relative_path, 'rb') as fd:
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
    specs = [[e.name, rubymarshal.classes.UsrMarshal('Gem::Version', [e.version]), 'ruby']
             for e in keys]
    # write uncompressed version
    with open(relative_path, 'wb') as fd:
        rubymarshal.writer.write(fd, specs)


def _yaml_ruby_constructor(loader, suffix, node):
    value = loader.construct_mapping(node)
    return rubymarshal.classes.UsrMarshal(suffix, value)


yaml.add_multi_constructor(u'!ruby/object:', _yaml_ruby_constructor, Loader=yaml.SafeLoader)


def analyse_gem(filename):
    """
    Extract name, version and specdata from gemfile.
    """
    with TarFile(filename, 'r') as archive:
        with archive.extractfile('metadata.gz') as md_file:
            data = yaml.safe_load(gzip.decompress(md_file.read()))
    # Workaroud
    del data.values['date']
    zdata = zlib.compress(rubymarshal.writer.writes(data))
    return data.values['name'], data.values['version'].values['version'], zdata
