import gzip

import rubymarshal.classes
import rubymarshal.writer
import rubymarshal.reader

from collections import namedtuple


# Natural key.
Key = namedtuple('Key', ('name', 'version'))


def read_specs(relative_path):
    """
    Read rubygem specs from file.
    """
    # read compressed version
    with gzip.open(relative_path, 'rb') as fd:
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
