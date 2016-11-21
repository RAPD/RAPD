"""
Utilities for detectors
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

__created__ = "2016-11-19"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import sys

def print_details(image):
    """
    Print out the details for a given image
    """
    from iotbx.detectors import ImageFactory

    # Read in the image
    i = ImageFactory(image)

    

    # No idea
    return True

if __name__ == "__main__":

    # Commandline for image
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
        print "Image read from command line %s" % test_image

    print_details(test_image)