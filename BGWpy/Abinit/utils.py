from __future__ import annotations

import collections
from collections.abc import Iterable, Iterator
from copy import deepcopy
from typing import Any


def is_number(s: Any) -> bool:
    """Returns True if the argument can be made a float."""
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False


def is_iter(obj: Any) -> bool:
    """Return True if the argument is list-like."""
    return hasattr(obj, "__iter__")


def is_scalar(obj: Any) -> bool:
    """Return True if the argument is not list-like."""
    return not is_iter(obj)


def flatten(iterable: Iterable[Any]) -> tuple[Any, ...]:
    """Make an iterable flat, i.e. a 1d iterable object."""
    iterator: Iterator[Any] = iter(iterable)
    array: collections.deque[Any] = collections.deque()
    stack: collections.deque[Iterator[Any]] = collections.deque()
    while True:
        try:
            value = next(iterator)
        except StopIteration:
            if not stack:
                return tuple(array)
            iterator = stack.pop()
        else:
            if not isinstance(value, str) and isinstance(value, collections.abc.Iterable):
                stack.append(iterator)
                iterator = iter(value)
            else:
                array.append(value)


def listify(obj: Any) -> list[Any]:
    """Return a flat list out of the argument."""
    if not obj:
        obj = []
    elif is_iter(obj):
        obj = list(flatten(obj))
    else:
        obj = [obj]
    return deepcopy(obj)
