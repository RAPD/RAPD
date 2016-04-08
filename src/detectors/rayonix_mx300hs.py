"""
Wrapper for manipulating the detector images
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2009-2016, Cornell University
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

__created__ = "2016-02-26"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

# Standard imports
import sys

# RAPD imports
import mar

def read_header(image):
    """Read header from rayonix mx300hs"""
    return mar.MarReadHeader(image)

if __name__ == "__main__":

    # Test the header reading
    test_image = "/Users/frankmurphy/workspace/rapd_github/src/test/sercat_id/test_data/THAU10_r1_1.0001"

    # Commandline for image
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
        print "Image read from command line %s" % test_image


    header = read_header(test_image)
    import pprint
    pp = pprint.PrettyPrinter()
    pp.pprint(header)
