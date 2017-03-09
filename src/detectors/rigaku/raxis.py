"""This is a docstring for this file"""

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

__created__ = "2017-03-09"
_maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
# import datetime
# import glob
import json
# import logging
# import multiprocessing
import os
from pprint import pprint
# import pymongo
import re
# import redis
# import shutil
# import subprocess
import sys
import time
# import unittest

from iotbx.detectors.raxis import RAXISImage as detector

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils

# ADSC Q315
# import detectors.adsc.adsc_q315 as detector
# Dectris Pilatus 6M
# import detectors.dectris.dectris_pilatus6m as detector# Rayonix MX300
# import detectors.rayonix.rayonix_mx300 as detector
# Rayonix MX300HS
# import detectors.rayonix.rayonix_mx300hs as detector

# Detector information
# The RAPD detector type
DETECTOR = "raxis"
# The detector vendor as it appears in the header
VENDORTYPE = "RAXIS"
# The detector serial number as it appears in the header
DETECTOR_SN = False
# The detector suffix "" if there is no suffix
DETECTOR_SUFFIX = ".osc"
# Template for image name generation ? for frame number places
IMAGE_TEMPLATE = "%s????.osc"
# Is there a run number in the template?
RUN_NUMBER_IN_TEMPLATE = False
# This is a version number for internal RAPD use
# If the header changes, increment this number
HEADER_VERSION = 1

# XDS information for constructing the XDS.INP file
# Import from more generic detector
# XDSINP = detector.XDSINP
# Update the XDS information from the imported detector
# XDSINP.update({})
# Overwrite XDS information with new data
# XDSINP = {}

# def parse_file_name(fullname):
#     """
#     Parse the fullname of an image and return
#     (directory, basename, prefix, run_number, image_number)
#     Keyword arguments
#     fullname -- the full path name of the image file
#     """
#     # Directory of the file
#     directory = os.path.dirname(fullname)
#
#     # The basename of the file (i.e. basename - suffix)
#     basename = os.path.basename(fullname).rstrip(DETECTOR_SUFFIX)
#
#     # The prefix, image number, and run number
#     sbase = basename.split(".")
#     prefix = ".".join(sbase[0:-1])
#     image_number = int(sbase[-1])
#     run_number = None
#     return directory, basename, prefix, run_number, image_number
#
# def create_image_fullname(directory,
#                           image_prefix,
#                           run_number=None,
#                           image_number=None):
#     """
#     Create an image name from parts - the reverse of parse
#
#     Keyword arguments
#     directory -- in which the image file appears
#     image_prefix -- the prefix before run number or image number
#     run_number -- number for the run
#     image_number -- number for the image
#     """
#
#     if not run_number in (None, "unknown"):
#         filename = "%s.%s.%04d" % (image_prefix,
#                                    run_number,
#                                    image_number)
#     else:
#         filename = "%s.%04d" % (image_prefix,
#                                    image_number)
#
#     fullname = os.path.join(directory, filename)
#
#     return fullname
#
# def create_image_template(image_prefix, run_number):
#     """
#     Create an image template for XDS
#     """
#
#     image_template = IMAGE_TEMPLATE % image_prefix
#
#     return image_template
#
# def get_data_root_dir(fullname):
#     """
#     Derive the data root directory from the user directory
#     The logic will most likely be unique for each site
#
#     Keyword arguments
#     fullname -- the full path name of the image file
#     """
#
#     # Isolate distinct properties of the images path
#     path_split = fullname.split(os.path.sep)
#     data_root_dir = os.path.join("/", *path_split[1:3])
#
#     # Return the determined directory
#     return data_root_dir

def read_header(fullname, beam_settings=False):
    """
    Read header from image file and return dict

    Keyword variables
    fullname -- full path name of the image file to be read
    beam_settings -- source information from site file

    This code is based on the RAXIS header from UCLA courtesy of Dr. D Cascio
    """

    # Perform the header read from the file
    # If you are importing another detector, this should work
    image = detector(fullname)
    image.readHeader()
    # for k, v in image.head.iteritems():
    #     print k, ":", v

    header = {
        "axis": "phi",
        "beam_x": image.head.get("beampixels_x", None),
        "beam_y": image.head.get("beampixels_y", None),
        "chi": image.head.get("chi", None),
        "date": image.head.get("date", None),
        "detector": "RAXIS",
        "detector_sn": image.head.get("operatorname", None),
        "distance": image.head.get("distance", None),
        "filter": image.head.get("filter", None),
        "ip_num": image.head.get("IP_num", None),
        "kv":  image.head.get("kV", None),
        "ma":  image.head.get("mA", None),
        "omega": image.head.get("omega", None),
        "osc_range": image.head.get("phiend", 0.0) - image.head.get("phistart", 0.0),
        "osc_start": image.head.get("phistart", None),
        "plate_type": image.head.get("plate_type", None),
        "scan_template": image.head.get("scan_template", None),
        "pixel_size": image.head.get("sizeFast", None),
        "pixel_size2": image.head.get("sizeSlow", None),
        "target": image.head.get("target", None),
        "time": image.head.get("minutes", 0.0) * 60.0,
        "twotheta":  image.head.get("twotheta", None),
        "wavelength": image.head.get("wavelength", None),
    }

    # Clean up header
    if header["detector_sn"]:
        header["detector_sn"] = header["detector_sn"].strip()

    # Calculate beam center in mm
    header["x_beam"] = header["beam_x"] * header["pixel_size"]
    header["y_beam"] = header["beam_x"] * header["pixel_size2"]

    # Return the header
    return header

def get_commandline():
    """
    Grabs the commandline
    """

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Parse image file header"
    parser = argparse.ArgumentParser(description=commandline_description)

    # A True/False flag
    parser.add_argument("-c", "--commandline",
                        action="store_true",
                        dest="commandline",
                        help="Generate commandline argument parsing")

    # File name to be generated
    parser.add_argument(action="store",
                        dest="file",
                        nargs="?",
                        default=False,
                        help="Name of file to be generated")

    # Print help message is no arguments
    if len(sys.argv[1:])==0:
        parser.print_help()
        parser.exit()

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
        raise Exception("No test image input!")
        # test_image = ""

    header = read_header(test_image)

    pprint.pprint(header)

if __name__ == "__main__":

    commandline_args = get_commandline()

    main(args=commandline_args)
