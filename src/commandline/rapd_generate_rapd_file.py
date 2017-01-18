"""Generate a generic rapd file"""

"""
This file is part of RAPD

Copyright (C) 2017, Cornell University
All rights reserved.

RAPD is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3.

RAPD is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__created__ = "2017-01-18"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
import time

# RAPD imports

_NOW = time.localtime()
_LICENSE = """
This file is part of RAPD

Copyright (C) %d, Cornell University
All rights reserved.

RAPD is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3.

RAPD is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
""" % _NOW.tm_year


def print_file_docstring(filename):
    """Print the docstring for file"""
    if filename:
        pass
    else:
        print "\"\"\"This is a docstring for this file\"\"\"\n"

def print_license(filename):
    """Print the license"""
    if filename:
        pass
    else:
        print "\"\"\""+_LICENSE+"\"\"\"\n"

def print_docstrings(filename):
    """Print file author docstrings"""
    if filename:
        pass
    else:
        print "__created__ = \"%d-%d-%d\"" % (_NOW.tm_year, _NOW.tm_mon, _NOW.tm_mday)
        print "__maintainer__ = \"Your Name\""
        print "__email__ = \"Your E-mail\""
        print "__status__ = \"Development\"\n"

def main():

    filename = False #"foo.py"

    print_file_docstring(filename)
    print_license(filename)
    print_docstrings(filename)

if __name__ == "__main__":

    print "rapd_generate_rapd_file.py"

    main()
