"""
Wrapper for manipulating the detector images
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2009-2018, Cornell University
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
import detectors.mar.mar as detector

# RAPD information
DETECTOR = "rayonix_mx300hs"
VENDORTYPE = "MARCCD"
# XDS information
XDS_FLIP_BEAM = True
XDSINP = [
    ('DETECTOR', 'MARCCD') ,
    ('DIRECTION_OF_DETECTOR_X-AXIS', '1 0 0') ,
    ('DIRECTION_OF_DETECTOR_Y-AXIS', '0 1 0') ,
    ('FRACTION_OF_POLARIZATION', '0.99') ,
    ('INCIDENT_BEAM_DIRECTION', '0 0 1') ,
    ('INCLUDE_RESOLUTION_RANGE', '100.0 0.0') ,
    ('INDEX_ORIGIN', '0 0 0') ,
    ('MAX_CELL_ANGLE_ERROR', '2.0') ,
    ('MAX_CELL_AXIS_ERROR', '0.030') ,
    ('MAX_FAC_Rmeas', '2.0') ,
    ('MINIMUM_VALID_PIXEL_VALUE', '0') ,
    ('MIN_RFL_Rmeas', '50.0') ,
    ('NX', '3840') ,
    ('NY', '3840') ,
    ('OVERLOAD', '65535') ,
    ('POLARIZATION_PLANE_NORMAL', '0 1 0') ,
    ('QX', '0.078200') ,
    ('QY', '0.078200') ,
    ('ROTATION_AXIS', '1 0 0') ,
    ('SPACE_GROUP_NUMBER', '0') ,
    ('TEST_RESOLUTION_RANGE', '50.0 2.0') ,
    ('TRUSTED_REGION', '0.0 0.99') ,
    ('VALUE_RANGE_FOR_TRUSTED_DETECTOR_PIXELS', '6000 30000') ,
    ('WFAC1', '1.0') ,
  ]


def read_header(image):
    """Read header from rayonix mx300hs"""
    return detector.read_header(image)

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
