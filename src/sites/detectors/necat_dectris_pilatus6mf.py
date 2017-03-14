"""Detector description for NE-CAT Pilatus 6M"""

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

__created__ = "2017-02-06"
_maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
# datetime
# glob
# import json
# logging
# multiprocessing
import os
import pprint
# pymongo
# import re
# redis
# shutil
# subprocess
# sys
# import time

# RAPD imports
# commandline_utils
# detectors.detector_utils as detector_utils
# utils

# Dectris Pilatus 6M
import detectors.dectris.dectris_pilatus6m as detector

# Detector information
# The RAPD detector type
DETECTOR = "dectris_pilatus6m"
# The detector vendor as it appears in the header
VENDORTYPE = "DECTRIS"
# The detector serial number as it appears in the header
DETECTOR_SN = "60-0112-F"
# The detector suffix "" if there is no suffix
DETECTOR_SUFFIX = ".cbf"
# Template for image name generation ? for frame number places
IMAGE_TEMPLATE = "%s_%s_????.cbf" # prefix & run number
# Is there a run number in the template?
RUN_NUMBER_IN_TEMPLATE = True
# This is a version number for internal RAPD use
# If the header changes, increment this number
HEADER_VERSION = 1

# XDS information for constructing the XDS.INP file
XDS_FLIP_BEAM = detector.XDS_FLIP_BEAM
# Import from more generic detector
XDSINP = detector.XDSINP
# Update the XDS information from the imported detector
XDSINP.update({
    "UNTRUSTED_RECTANGLE14": "   0 2463  2103 2121",
    "UNTRUSTED_RECTANGLE15": "   0 2463  2315 2333",
    "UNTRUSTED_RECTANGLE12": "   0 2463  1679 1697",
    "UNTRUSTED_RECTANGLE13": "   0 2463  1891 1909",
    "UNTRUSTED_RECTANGLE10": "   0 2463  1255 1273",
    "UNTRUSTED_RECTANGLE11": "   0 2463  1467 1485",
    "STRONG_PIXEL": "6",
    "MAX_CELL_ANGLE_ERROR": "2.0",
    "NUMBER_OF_PROFILE_GRID_POINTS_ALONG_ALPHA/BETA": "13",
    "MINIMUM_NUMBER_OF_PIXELS_IN_A_SPOT": "4",
    "REFINE(INTEGRATE)": "POSITION BEAM ORIENTATION CELL",
    "REFINE(CORRECT)": "BEAM ORIENTATION CELL AXIS POSITION",
    "INCLUDE_RESOLUTION_RANGE": "200.0 0.0",
    "REFINE(IDXREF)": "BEAM AXIS ORIENTATION CELL",
    "NX": "2463",
    "NY": "2527",
    "STRICT_ABSORPTION_CORRECTION": "TRUE",
    "MINIMUM_ZETA": "0.05",
    "OVERLOAD": "1048500",
    "UNTRUSTED_RECTANGLE4": "1969 1977     0 2527",
    "UNTRUSTED_RECTANGLE5": "   0 2463   195  213",
    "UNTRUSTED_RECTANGLE6": "   0 2463   407  425",
    "UNTRUSTED_RECTANGLE7": "   0 2463   619  637",
    "UNTRUSTED_RECTANGLE1": " 487  495     0 2527",
    "UNTRUSTED_RECTANGLE2": " 981  989     0 2527",
    "UNTRUSTED_RECTANGLE3": "1475 1483     0 2527",
    "NUMBER_OF_PROFILE_GRID_POINTS_ALONG_GAMMA": "9",
    "UNTRUSTED_RECTANGLE8": "   0 2463   831  849",
    "UNTRUSTED_RECTANGLE9": "   0 2463  1043 1061",
    "FRACTION_OF_POLARIZATION": "0.99",
    "MAX_CELL_AXIS_ERROR": "0.03",
    "VALUE_RANGE_FOR_TRUSTED_DETECTOR_PIXELS": " 7000 30000",
    "MIN_RFL_Rmeas": " 50",
    "DIRECTION_OF_DETECTOR_X-AXIS": " 1.0 0.0 0.0",
    "SENSOR_THICKNESS": "0.32",
    "POLARIZATION_PLANE_NORMAL": " 0.0 1.0 0.0",
    "MAX_FAC_Rmeas": "2.0",
    "TRUSTED_REGION": "0.0 1.05",
    "ROTATION_AXIS": " 1.0 0.0 0.0",
    "MINIMUM_VALID_PIXEL_VALUE": "0 ",
    "QY": "0.172",
    "QX": "0.172 ",
    "INCIDENT_BEAM_DIRECTION": "0.0 0.0 1.0",
    "SEPMIN": "4",
    "CLUSTER_RADIUS": "2",
    "DETECTOR": "PILATUS"
    })

# Testing information
TEST_DATA_DIR = "APS/NECAT/24-ID-C"
TEST_INDEX_COMMANDS = [
    "rapd.index --json images/run_1_0001.cbf",
    "rapd.index --json images/run_1_0001.cbf  images/run_1_0091.cbf"
    ]
TEST_INTEGRATE_COMMAND = "rapd.integrate --json images/run_1_####.cbf"

def parse_file_name(fullname):
    """
    Parse the fullname of an image and return
    (directory, basename, prefix, run_number, image_number)
    Keyword arguments
    fullname -- the full path name of the image file
    """
    # Directory of the file
    directory = os.path.dirname(fullname)

    # The basename of the file (i.e. basename - suffix)
    basename = os.path.basename(fullname).rstrip(DETECTOR_SUFFIX)

    # The prefix, image number, and run number
    sbase = basename.split("_")
    prefix = "_".join(sbase[0:-2])
    image_number = int(sbase[-1])
    run_number = int(sbase[-2])
    return directory, basename, prefix, run_number, image_number

def create_image_fullname(directory,
                          image_prefix,
                          run_number=None,
                          image_number=None):
    """
    Create an image name from parts - the reverse of parse

    Keyword arguments
    directory -- in which the image file appears
    image_prefix -- the prefix before run number or image number
    run_number -- number for the run
    image_number -- number for the image
    """

    filename = IMAGE_TEMPLATE.replace("????", "%04d") % (image_prefix, run_number, image_number)

    fullname = os.path.join(directory, filename)

    return fullname

def create_image_template(image_prefix, run_number):
    """
    Create an image template for XDS
    """

    image_template = IMAGE_TEMPLATE % (image_prefix, run_number)

    return image_template

def get_data_root_dir(fullname):
    """
    Derive the data root directory from the user directory
    The logic will most likely be unique for each site

    Keyword arguments
    fullname -- the full path name of the image file
    """

    # Isolate distinct properties of the images path
    path_split = fullname.split(os.path.sep)
    data_root_dir = os.path.join("/", *path_split[1:3])

    # Return the determined directory
    return data_root_dir

def read_header(fullname, beam_settings=False):
    """
    Read header from image file and return dict

    Keyword variables
    fullname -- full path name of the image file to be read
    beam_settings -- source information from site file
    """

    # Perform the header read from the file
    # If you are importing another detector, this should work
    header = detector.read_header(fullname)

    # The image template for processing
    header["image_template"] = IMAGE_TEMPLATE % (header["image_prefix"], header["run_number"])
    header["run_number_in_template"] = RUN_NUMBER_IN_TEMPLATE

    # Return the header
    return header

def get_commandline():
    """
    Grabs the commandline
    """

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Generate a generic RAPD file"
    parser = argparse.ArgumentParser(description=commandline_description)

    # File name to be generated
    parser.add_argument(action="store",
                        dest="file",
                        nargs="?",
                        default=False,
                        help="Name of file to be generated")

    return parser.parse_args()

def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    print "main"

    if args.file:
        test_image = os.path.abspath(args.file)
    else:
        raise Error("No test image input!")

    # Read the header
    header = read_header(test_image)

    # And print it out
    pprint.pprint(header)

if __name__ == "__main__":

    # Get the commandline args
    commandline_args = get_commandline()

    # Execute code
    main(args=commandline_args)
