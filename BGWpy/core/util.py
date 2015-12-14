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

def last_lines_contain(fname, tag, nlines=60):
    """True if the last nlines of fname contain tag."""
    nlines = int(nlines)
    with open(fname, 'r') as f:
        lines = f.readlines()
        lines.reverse()

        for i in range(nlines):
            try:
                line = lines[i]
            except:
                return False

            if tag in line:
                return True
    return False

