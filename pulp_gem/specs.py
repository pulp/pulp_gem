import gzip

import rubymarshal.classes
import rubymarshal.writer
import rubymarshal.reader

from collections import namedtuple


# Natural key.
Key = namedtuple('Key', ('name', 'version'))


class Specs:

    def __init__(self, relative_path):
        self.relative_path = relative_path

    def read(self):
        with gzip.open(self.relative_path, 'rb') as fd:
            data = rubymarshal.reader.load(fd)
        for item in data:
            name = item[0]
            if name.__class__ is bytes:
                name = name.decode()
            version = item[1].values[0]
            if version.__class__ is bytes:
                version = version.decode()
            yield Key(name, version)

    def write(self, keys):
        specs = [[e.name, rubymarshal.classes.UsrMarshal('Gem::Version', [e.version]), 'ruby']
                 for e in keys]
        with gzip.open(self.relative_path, 'wb') as fd:
            rubymarshal.writer.write(fd, specs)
