"""Some genering formatting functions for the input."""
from numpy import array
from collections import OrderedDict
from .writable import Writable

class Card(list, Writable):
    """A card used in fortran input files."""

    def __init__(self, name, option, quotes=True, *args, **kwargs):
        super(Card, self).__init__(*args, **kwargs)
        self.name = name
        self.option = option
        self.quotes = quotes

    def __str__(self):
        S = '{} {}\n'.format(self.name, self.option)
        for val in self:
            S += '   {}\n'.format(fortran_str(val, self.quotes))

        return S

    # TODO
    #def clear(self):
    #   del self[:]


class Namelist(OrderedDict, Writable):
    """A namelist used in fortran input files."""

    def __init__(self, name, quotes=True, *args, **kwargs):
        super(Namelist, self).__init__(*args, **kwargs)
        self.name = name
        self.update(kwargs)
        self.quotes = quotes

    def __str__(self):
        S = '&{}\n'.format(self.name)
        for key, val in self.items():
            S += '   {} = {}\n'.format(key, fortran_str(val, self.quotes))

        S += '/\n'
        return S


def fortran_str(obj, quotes=True):
    """Stringify an object for fortran-readable input."""
    if isinstance(obj, str):
        return str_str(obj, quotes)
    if isinstance(obj, bool):
        return bool_str(obj)
    if '__iter__' in dir(obj):
        try:
            return arr_str(array(obj, dtype=np.double))
        except:
            return ' '.join([fortran_str(o, quotes) for o in obj])

    else:
        return str(obj)


def str_str(s, quotes=True):
    if quotes:
        return "'{}'".format(s)
    else:
        return str(s)


def arr_str(arr):
    return str(arr).replace('[', ' ').replace(']', ' ').replace(',', ' ')


def bool_str(b):
    if b:
        return '.true.'
    return '.false.'
