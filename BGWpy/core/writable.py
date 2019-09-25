
from collections import OrderedDict

class Writable(object):

    def __init__(self, fname=None):
        self.fname = fname

    def write(self, fname=None):
        fname = fname if fname else self.fname
        with open(fname, 'w') as f:
            f.write(str(self))


class BasicFile(Writable):

    def __init__(self):
        self.lines = list()

    def __str__(self):
        return '\n'.join(self.lines) + '\n'


class BasicInputFile(Writable):

    def __init__(self, variables={}, keywords=[], **kwargs):

        super(BasicInputFile, self).__init__(**kwargs)

        self.variables = OrderedDict(variables)
        self.keywords = list(keywords)

    def __str__(self):

        lines = list()
        for key, val in self.variables.items():
            lines.append('{} {}'.format(key, val))

        lines.extend(self.keywords)

        return '\n'.join(lines) + '\n'

    def append(self, line):
        self.keywords.append(line)

    def __getitem__(self, key):
        return self.variables[key]

    def __setitem__(self, key, val):
        self.variables[key] = val

    def __delitem__(self, key):

        if key in self.variables:
            del self.variables[key]

        elif key in self.keywords:
            i = self.keywords.index(key)
            del self.keywords[i]

        else:
            raise KeyError(key)


