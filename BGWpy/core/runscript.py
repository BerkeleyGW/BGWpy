from collections import OrderedDict
import subprocess

from ..config import default_runscript
from .writable import Writable

class RunScript(Writable):

    def __init__(self, variables=None, links=None, copies=None, main=None,
                 **kwargs):
        """
        Just a run script. Starts with a few declarations (variables),
        then create symbolic links, and finally execute a list of commands (main).

        Keyword arguments
        -----------------

        variables : dict or OrderedDict
            Variables to be declared in the script. The keys of the given dict
            are the variable names, and the values are interpreted as strings,
            for which quotation marks will be added.

        links :
            A list of pairs (target, dest), that will be linked with
            ln -nfs target dest

        copies :
            A list of pairs (src, dest), that will be copied with
            cp -f src dest

        main :
            A list of executions, e.g.
            '$MPIRUN $EXECUTABLE < $INPUT >& $OUTPUT'

        header :
            A list of executions that occur before all other executions.
            Can be used to transform the script into a submission file.

        footer :
            A list of executions that occur after all other executions.
            Can be used to add some cleaning up.

        first_line :
            The first line of the script, e.g. '#!/bin/bash'.

        """

        self.first_line = str()
        self.header = list()
        self.variables = OrderedDict()
        self.links = list()
        self.copies = list()
        self.main = list()
        self.footer = list()

        if variables is not None:
            self.variables.update(variables)

        if links is not None:
            for link in links:
                if not self._check_pair(link):
                    raise Exception(
                    "The variable 'links' must contain pairs of two elements")
                self.add_link(*link)

        if copies is not None:
            for copy in copies:
                if not self._check_pair(copy):
                    raise Exception(
                    "The variable 'copies' must contain pairs of two elements")
                self.add_copy(*copy)

        if isinstance(main, str):
            self.main.append(main)
        elif main is not None:
            self.main.extend(main)

        self.first_line = kwargs.get('first_line',
                                     default_runscript['first_line'])

        header = kwargs.get('header', default_runscript['header'])
        if isinstance(header, str):
            self.header.append(header)
        elif header is not None:
            self.header.extend(header)

        footer = kwargs.get('footer', default_runscript['footer'])
        if isinstance(footer, str):
            self.footer.append(footer)
        elif footer is not None:
            self.footer.extend(footer)

    def _check_pair(self, pair):
        """Check that an object is a pair of two elements."""
        try:
            if len(pair) == 2:
                return True
        except:
            pass
        return False

    def append(self, line):
        """Append a command to the script."""
        self.main.append(line)

    def extend(self, lines):
        """Append a list of commands to the script."""
        self.main.extend(lines)

    def add_link(self, target, dest):
        self.links.append([target, dest])

    def add_copy(self, src, dest):
        self.copies.append([src, dest])

    def merge(self, other):
        """ 
        Merge an other RunScript, executing the lines sequentially,
        assuming that both scripts are in the same directory.
        """
        self.variables.update(other.variables)
        self.links.extend(other.links)
        self.copies.extend(other.copies)
        self.main.extend(['\n'] + other.main)

    def __setitem__(self, key, value):
        """Declare a variable."""
        self.variables[key] = value

    def __getitem__(self, key):
        """Get a variable."""
        return self.variables[key]

    def __delitem__(self, key):
        """Delete a variable."""
        del self.variables[key]

    def _get_quoted_string(self, value):

        # Strip the value of single or double quotes
        # but strip a single occurence ...
        single, double = "'", '"'
        for quote in (single, double):
            if value.startswith(quote):
                value = value[1:]
                if value.endswith(quote):
                    value = value[:-1]

        if single not in value and double not in value:
            value = single + value + single
        elif single in value and double not in value:
            value = double + value + double
        elif double in value and single not in value:
            value = single + value + single
        else:
            raise Exception("Cannot process the quotes for variable named " +
                            "{}\nwith value {}.\n".format(name, value) +
                            "Action: simply add this declaration " + 
                            "in the 'main' list of commands.")

        return value

    def __str__(self):
        S = ''
        S += self.first_line + 2 * '\n'

        S += '\n'
        for line in self.header:
            S += line + '\n'

        for name, value in self.variables.items():
            value = self._get_quoted_string(value)
            S += '{}={}\n'.format(name, value)

        if self.links:
            S += '\n'
            for target, dest in self.links:
                # Don't attempt to create a link if the names match.
                if target == dest:
                    continue
                S += 'ln -nfs {} {}\n'.format(target, dest)

        if self.copies:
            S += '\n'
            for src, dest in self.copies:
                S += 'cp -f {} {}\n'.format(src, dest)

        S += '\n'
        for line in self.main:
            S += line + '\n'

        S += '\n'
        for line in self.footer:
            S += line + '\n'

        return S

    def run(self):
        subprocess.call(['bash', self.fname])
