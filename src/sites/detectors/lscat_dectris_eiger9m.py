"""
Detector description for LS-CAT Eiger 9M
Designed to read the CBF version of the Eiger file
"""

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

__created__ = "2017-02-13"
_maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
import os
import pprint

# RAPD imports
# commandline_utils
# detectors.detector_utils as detector_utils
# utils

# Dectris Pilatus 6M
import detectors.dectris.dectris_eiger9m as detector
import detectors.detector_utils as utils

# Detector information
# The RAPD detector type
DETECTOR = "dectris_eiger9m"
# The detector vendor as it appears in the header
VENDORTYPE = "Eiger-9M"
# The detector serial number as it appears in the header
DETECTOR_SN = "Dectris Eiger 9M S/N E-18-0101"
# The detector suffix "" if there is no suffix
DETECTOR_SUFFIX = ".cbf"
# Is there a run number in the template?
RUN_NUMBER_IN_TEMPLATE = False
# Template for image name generation ? for frame number places
if RUN_NUMBER_IN_TEMPLATE:
    #IMAGE_TEMPLATE = "%s.%03d_??????.cbf" # prefix & run number
    IMAGE_TEMPLATE = "%s_%03d_??????.cbf" # prefix & run number
else:
    IMAGE_TEMPLATE = "%s_??????.cbf" # prefix
# This is a version number for internal RAPD use
# If the header changes, increment this number
HEADER_VERSION = 1

# XDS information for constructing the XDS.INP file
# Import from more generic detector
XDS_FLIP_BEAM = detector.XDS_FLIP_BEAM
# Import from more generic detector
XDSINP0 = detector.XDSINP
# Update the XDS information from the imported detector
# only if there are differnces or new keywords.
# The tuple should contain two items (key and value)
# ie. XDSINP1 = [("SEPMIN", "4"),]
XDSINP1 = [(),
          ]
XDSINP = utils.merge_xds_input(XDSINP0, XDSINP1)

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
    if RUN_NUMBER_IN_TEMPLATE:
        run_number = int(sbase[-2])
        prefix = "_".join(sbase[0:-3])
    else:
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
    if RUN_NUMBER_IN_TEMPLATE:
        filename = IMAGE_TEMPLATE.replace("??????", "%06d") % (image_prefix, run_number, image_number)
    else:
        filename = IMAGE_TEMPLATE.replace("??????", "%06d") % (image_prefix, image_number)

    fullname = os.path.join(directory, filename)

    return fullname

def create_image_template(image_prefix, run_number):
    """
    Create an image template for XDS
    """

    # print "create_image_template %s %d" % (image_prefix, run_number)
    if RUN_NUMBER_IN_TEMPLATE:
        image_template = IMAGE_TEMPLATE % (image_prefix, run_number)
    else:
        image_template = IMAGE_TEMPLATE % image_prefix

    # print "image_template: %s" % image_template

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

def read_header(input_file=False, beam_settings=False):
    """
    Read header from image file and return dict

    Keyword variables
    fullname -- full path name of the image file to be read
    beam_settings -- source information from site file
    """

    # Perform the header read from the file
    # If you are importing another detector, this should work
    if input_file.endswith(".h5"):
        header = utils.read_hdf5_header(input_file)

    elif input_file.endswith(".cbf"):
        header = detector.read_header(input_file)

        basename = os.path.basename(input_file)

        #header["image_prefix"] = ".".join(basename.replace(".cbf", "").split(".")[:-1])
        header["image_prefix"] ="_".join(basename.replace(".cbf", "").split("_")[:-1])
        
        # Add run_number (if used) and image template for processing
        if RUN_NUMBER_IN_TEMPLATE:
            #header["run_number"] = int(basename.replace(".cbf", "").split("_")[-1])
            header["run_number"] = int(basename.replace(".cbf", "").split("_")[-2])
            header["image_template"] = IMAGE_TEMPLATE % (header["image_prefix"], header["run_number"])
        else:
            header["run_number"] = None
            header["image_template"] = IMAGE_TEMPLATE % header["image_prefix"]

        # Add tag for module to header
        header["rapd_detector_id"] = "lscat_dectris_eiger9m"

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
    if test_image.endswith(".h5"):
        header = read_header(hdf5_file=test_image)
    elif test_image.endswith(".cbf"):
        header = read_header(cbf_file=test_image)

    # And print it out
    pprint.pprint(header)

if __name__ == "__main__":

    # Get the commandline args
    commandline_args = get_commandline()

    # Execute code
    main(args=commandline_args)
