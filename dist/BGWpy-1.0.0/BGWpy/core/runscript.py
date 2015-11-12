from collections import OrderedDict
import subprocess

from .writable import Writable

class RunScript(Writable):

    def __init__(self, variables=None, links=None, main=None,
                 first_line = '#!/usr/bin/env bash', **kwargs):
        """
        Just a run script. Starts with a few declarations (variables),
        then create symbolic links, and finally execute a list of commands (main).

        Arguments
        ---------

        variables: A dict or an OrderedDict, for which the keys are
                   the variable names and the values are interpreted
                   as strings, for which quotation marks will be added.

        links: A list of pairs (target, dest), which give statements as
               ln -nfs target dest

        main: A list of executions, e.g.
              '$MPIRUN $EXECUTABLE < $INPUT >& $OUTPUT'

        """

        self.first_line = first_line
        self.variables = OrderedDict()  # Variables declared in the preemble
        self.links = list()             # Symbolic links to be made
        self.main = list()              # Main execution lines

        if variables is not None:
            self.variables.update(variables)

        if links is not None:
            for link in links:
                try:
                    l = len(link)
                    if l != 2:
                        raise Exception('')
                except:
                    raise Exception("The variable 'links' must contains pairs of two elements")

                self.add_link(*link)

        if isinstance(main, str):
            self.main.append(main)
        elif main is not None:
            self.main.extend(main)

    def append(self, line):
        """Append a command to the script."""
        self.main.append(line)

    def extend(self, lines):
        """Append a list of commands to the script."""
        self.main.extend(lines)

    def add_link(self, target, dest):
        self.links.append([target, dest])

    def merge(self, other):
        """ 
        Merge an other RunScript, executing the lines sequentially,
        assuming that both scripts are in the same directory.
        """
        self.variables.update(other.variables)
        self.links.extend(other.links)
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

    def __str__(self):
        S = ''
        S += self.first_line + 2 * '\n'

        for name, value in self.variables.items():

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

            S += '{}={}\n'.format(name, value)

        S += '\n'
        for target, dest in self.links:
            # Don't attempt to create a link if the names match.
            if target == dest:
                continue
            S += 'ln -nfs {} {}\n'.format(target, dest)

        S += '\n'
        for line in self.main:
            S += line + '\n'

        return S

    def run(self):
        subprocess.call(['bash', self.fname])
