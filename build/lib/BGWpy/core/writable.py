
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

    def __init__(self, variables={}, keywords=[], extra_lines=[]):

        self.variables = OrderedDict(variables)
        self.keywords = list(keywords)
        self.extra_lines = list(extra_lines)

    def __str__(self):

        lines = list()
        for key, val in self.variables.iteritems():
            lines.append('{} {}'.format(key, val))

        lines.extend(self.keywords)
        lines.extend(self.extra_lines)

        return '\n'.join(lines) + '\n'

    def append(self, line):
        self.keywords.append(line)

    def __setitem__(self, key, val):
        self.variables[key] = val

    def __delitem__(self, key):

        if key in self.variables:
            del self.variables[key]

        elif key in self.keywords:
            i = self.keywords.index(key)
            del self.keywords[i]

        elif key in self.extra_lines:
            i = self.extra_lines.index(key)
            del self.extra_lines[i]

        else:
            raise KeyError(key)


