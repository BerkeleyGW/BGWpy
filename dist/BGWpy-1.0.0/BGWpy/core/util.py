import os
import contextlib

@contextlib.contextmanager
def exec_from_dir(dirname):
    original = os.path.realpath(os.curdir)
    os.chdir(dirname)
    try:
        yield
    finally:
        os.chdir(original)
