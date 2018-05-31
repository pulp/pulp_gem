import rubymarshal.classes
import rubymarshal.writer
import rubymarshal.reader

from collections import namedtuple


# Natural key.
Key = namedtuple('Key', ('name', 'version'))


class Specs(list):
    def read(self, fd):
        data = rubymarshal.reader.load(fd)
        for item in data:
            name = item[0]
            if name.__class__ is bytes:
                name = name.decode()
            version = item[1].values[0]
            if version.__class__ is bytes:
                version = version.decode()
            self.append(Key(name, version))

    def write(self, fd):
        specs = [[e.name, rubymarshal.classes.UsrMarshal('Gem::Version', [e.version]), 'ruby']
                 for e in self]
        rubymarshal.writer.write(fd, specs)
