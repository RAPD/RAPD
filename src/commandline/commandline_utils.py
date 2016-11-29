"""
Utilities for commandline running
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2016, Cornell University
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

__created__ = "2016-11-28"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
import os
import sys

# RAPD imports
# import utils.log
# import utils.lock
import utils.site
# import utils.text as text

# The data processing parser - to be used by commandline RAPD processes
dp_parser = argparse.ArgumentParser(add_help=False)

# Verbosity
dp_parser.add_argument("-v", "--verbose",
                       action="store_true",
                       dest="verbose",
                       help="Enable verbose feedback")
# The site
dp_parser.add_argument("-s", "--site",
                       action="store",
                       dest="site",
                       help="Define the site (ex. NECAT_C)")

# List possible sites
dp_parser.add_argument("-ls", "--listsites",
                       action="store_true",
                       dest="listsites",
                       help="List the available sites")

# The detector
dp_parser.add_argument("-d", "--detector",
                       action="store",
                       dest="detector",
                       help="Define the detector (ex. adsc_q315)")

# List possible detectors
dp_parser.add_argument("-ld", "--listdetectors",
                       action="store_true",
                       dest="listdetectors",
                       help="List the available detectors")

# Beam center
dp_parser.add_argument("-b", "--beamcenter",
                       action="store",
                       dest="beamcenter",
                       nargs=2,
                       type=float,
                       help="Define the beam center x,y")

# Spacegroup
dp_parser.add_argument("-sg", "--spacegroup",
                       action="store",
                       dest="spacegroup",
                       nargs=1,
                       help="Input a spacegroup")

# Resolution low
dp_parser.add_argument("-lo", "--lowres",
                       action="store",
                       dest="lowres",
                       nargs=1,
                       type=float,
                       help="Low resolution limit")

# Resolution hi
dp_parser.add_argument("-hi", "--hires",
                       action="store",
                       dest="hires",
                       nargs=1,
                       type=float,
                       help="High resolution limit")

# Directory or files
dp_parser.add_argument(action="store",
                       dest="sources",
                       nargs="*",
                       help="Directory or files")

# Frames
# Override XDS file?

def print_sites(left_buffer=""):
    """
    Print out all the sites
    """
    sites = utils.site.get_site_files()

    for site in sites:
        print left_buffer + os.path.basename(site)

def analyze_data_sources(sources, mode="index"):
    """
    Return information on files or directory from input
    """
    print "analyze_data_sources", sources

    return_data = {}

    for source in sources:
        print source
        source_abspath = os.path.abspath(source)

        if os.path.exists(source_abspath):
            if os.path.isdir(source_abspath):
                pass
            elif os.path.isfile(source_abspath):
                pass


if __name__ == "__main__":

    print "commandline_utils.py"

    parser = argparse.ArgumentParser(parents=[dp_parser],
                                     description="Testing")
    returned_args = parser.parse_args()
    print "\nVariables:"
    print "%20s  %-10s" % ("var", "val")
    print "%20s  %-10s" % ("=======", "=======")
    for pair in returned_args._get_kwargs():
        print "%20s  %-10s" % pair


    print "\nSites:"
    print_sites(left_buffer="  ")
