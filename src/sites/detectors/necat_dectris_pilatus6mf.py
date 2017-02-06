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
# argparse
# datetime
# glob
json
# logging
# multiprocessing
os
# pprint
# pymongo
re
# redis
# shutil
# subprocess
# sys
time

# RAPD imports
# commandline_utils
# detectors.detector_utils as detector_utils
# utils

# Dectris Pilatus 6M
import detectors.dectris.dectris_pilatus6m as detector

# Detector information
# The RAPD detector type
DETECTOR = "rayonix_mx300"
# The detector vendor as it appears in the header
VENDORTYPE = "MARCCD"
# The detector serial number as it appears in the header
DETECTOR_SN = 7
# The detector suffix "" if there is no suffixDETECTOR_SUFFIX = ""
# Template for image name generation ? for frame number placesIMAGE_TEMPLATE = "%s.????"
# Is there a run number in the template?
RUN_NUMBER_IN_TEMPLATE = False
# This is a version number for internal RAPD use
# If the header changes, increment this number
HEADER_VERSION = 1

# XDS information for constructing the XDS.INP file
# Import from more generic detector# XDS_INP = detector.XDS_INP
# Update the XDS information from the imported detector
# XDS_INP.update({})
# Overwrite XDS information with new data
# XDS_INP = {}

def parse_file_name(fullname):
    """
    Parse the fullname of an image and return
    (directory, basename, prefix, run_number, image_number)
    Keyword arguments
    fullname -- the full path name of the image file
    """
    # Directory of the file    directory = os.path.dirname(fullname)

    # The basename of the file (i.e. basename - suffix)
    basename = os.path.basename(fullname).rstrip(DETECTOR_SUFFIX)

    # The prefix, image number, and run number    sbase = basename.split(".")
    prefix = ".".join(sbase[0:-1])
    image_number = int(sbase[-1])
    run_number = None
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

    if not run_number in (None, "unknown"):
        filename = "%s.%s.%04d" % (image_prefix,
                                   run_number,
                                   image_number)
    else:
        filename = "%s.%04d" % (image_prefix,
                                   image_number)

    fullname = os.path.join(directory, filename)

    return fullname

def create_image_template(image_prefix):
    """
    Create an image template for XDS
    """

    image_template = IMAGE_TEMPLATE % image_prefix

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

    return parser.parse_args()

def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    print "main"

    if len(sys.argv) > 1:
        test_image = sys.argv[1]
    else:
        raise Error("No test image input!")
        # test_image = ""

    # Read the header
    header = read_header(test_image)

    # And print it out
    pprint.pprint(header)

if __name__ == "__main__":

    # Get the commandline args
    commandline_args = get_commandline()

    # Execute code
    main(args=commandline_args)
