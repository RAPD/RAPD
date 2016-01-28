"""
This file is part of RAPD

Copyright (C) 2016 Cornell University
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

__created__ = "2016-01-28"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

import functools

def verbose_print(arg, level=1, verbosity=1):
    """Print to terminal window screened by verbosity setting

    Keyword arguments:
    arg -- object to be printed (default None)
    level -- the importance of the printing job (default 5)
    verbosity -- the value level must be less than or equal to to print (default 1)
    """
    if level <= verbosity:
        print arg

def get_terminal_printer(verbosity=1):
    """Returns a terminal printer

    Keyword arguments:
    verbosity - threshold to print (default 1)
    """

    terminal_print = functools.partial(verbose_print, verbosity=1)
    return terminal_print
