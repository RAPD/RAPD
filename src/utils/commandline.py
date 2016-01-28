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

__created__ = "2016-01-27"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

import argparse

"""
commandline.py holds utilities for parsing the commandline for rapd processes
"""

# The base parser - used by rapd.py
base_parser = argparse.ArgumentParser(add_help=False)
base_parser.add_argument("-s",
                         action="store",
                         dest="site",
                         help="Define the site (ex. NECAT_C)")
base_parser.add_argument("-v",
                         action="store_true",
                         dest="verbose",
                         help="Enable verbose feedback")

if __name__ == "__main__":

    print "commandline.py"
    print "=============="

    parser = argparse.ArgumentParser(parents=[base_parser],
                                     description="Testing")
    returned_args = parser.parse_args()
    print "%10s  %-10s" % ("var", "val")
    print "%10s  %-10s" % ("=======", "=======")
    for pair in returned_args._get_kwargs():
        print "%10s  %-10s" % pair
