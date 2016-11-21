"""
Detector utilities
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

__created__ = "2016-11-21"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import sys

# RAPD imports
import utils.text as text

def print_detector_info(image):
    """
    Print out information on the detector given an image
    """

    from iotbx.detectors import ImageFactory

    i = ImageFactory(image)

    print "%20s: %s" % ("vendortype", str(i.vendortype))
    print "\nParameters:"
    print "==========="
    for key, val in i.parameters.iteritems():
        print "%20s: %s" % (key, val)

if __name__ == "__main__":

    # Get image name from the commandline
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
    else:
        print text.red + "No input image" + text.stop
        sys.exit(9)

    print_detector_info(test_image)
