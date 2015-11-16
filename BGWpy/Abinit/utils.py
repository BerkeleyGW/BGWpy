from __future__ import print_function, division

import collections 

from copy import deepcopy


def is_number(s):
    """Returns True if the argument can be made a float."""
    try:
        float(s)
        return True
    except:
        return False

def is_iter(obj):
    """Return True if the argument is list-like."""
    return hasattr(obj, '__iter__')

def is_scalar(obj):
    """Return True if the argument is not list-like."""
    return not is_iter

def flatten(iterable):
    """Make an iterable flat, i.e. a 1d iterable object."""
    iterator = iter(iterable)
    array, stack = collections.deque(), collections.deque()
    while True:
        try:
            value = next(iterator)
        except StopIteration:
            if not stack:
                return tuple(array)
            iterator = stack.pop()
        else:
            if not isinstance(value, str) \
               and isinstance(value, collections.Iterable):
                stack.append(iterator)
                iterator = iter(value)
            else:
                array.append(value)

def listify(obj):
    """Return a flat list out of the argument."""
    if not obj:
        obj = list()
    elif is_iter(obj):
        obj = list(flatten(obj))
    else:
        obj = [obj]
    return deepcopy(obj)

