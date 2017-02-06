"""Generate a RAPD detector scaffold file"""

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

__created__ = "2017-1-19"
_maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
# import datetime
# import glob
# import logging
# import multiprocessing
# import os
# import pprint
# import pymongo
# import redis
# import shutil
# import subprocess
# import sys
# import time

# RAPD imports
from rapd_generate_basefile import CommandlineFileGenerator, split_text_blob
# import commandline_utils
# import import detectors.detector_utils as detector_utils
# import utils

class DetectorFileGenerator(CommandlineFileGenerator):
    """File generator for detector wrapper"""

    def run(self):
        """The main actions of the module"""

        self.preprocess()

        self.write_file_docstring()
        self.write_license()
        self.write_docstrings()
        self.write_imports(write_list=("json",
                                       "os",
                                       "re",
                                       "time"))
        self.write_detector()
        self.write_commandline()
        self.write_main_func(description="Parse image file header")
        self.write_main()

    def write_main_func(self, main_func_lines=False):
        """Write the main function"""

        main_func_lines = [
            "def main(args):",
            "    \"\"\"",
            "    The main process docstring",
            "    This function is called when this module is invoked from",
            "    the commandline",
            "    \"\"\"\n",
            "    print \"main\"\n",
            "    if args.file:",
            "        test_image = os.path.abspath(args.file)",
            "    else:",
            "        raise Error(\"No test image input!\")",
            "        # test_image = \"\"\n",
            "    # Read the header",
            "    header = read_header(test_image)\n",
            "    # And print it out",
            "    pprint.pprint(header)\n"]

        super(DetectorFileGenerator, self).write_main_func(main_func_lines=main_func_lines)

    def write_detector(self):
        """Write the detector-specific functions"""

        # Import generic detectors
        detector_imports = [
            "# ADSC Q315",
            "# import detectors.adsc.adsc_q315 as detector",
            "# Dectris Pilatus 6M",
            "# import detectors.dectris.dectris_pilatus6m as detector"
            "# Rayonix MX300",
            "# import detectors.rayonix.rayonix_mx300 as detector",
            "# Rayonix MX300HS",
            "# import detectors.rayonix.rayonix_mx300hs as detector\n"
        ]
        self.output_function(detector_imports)

        # Information for detector setup
        detector_information = [
            "# Detector information",
            "# The RAPD detector type",
            "DETECTOR = \"rayonix_mx300\"",
            "# The detector vendor as it appears in the header",
            "VENDORTYPE = \"MARCCD\"",
            "# The detector serial number as it appears in the header",
            "DETECTOR_SN = 7",
            "# The detector suffix \"\" if there is no suffix",
            "DETECTOR_SUFFIX = \"\"",
            "# Template for image name generation ? for frame number places",
            "IMAGE_TEMPLATE = \"%s.????\"",
            "# Is there a run number in the template?",
            "RUN_NUMBER_IN_TEMPLATE = False",
            "# This is a version number for internal RAPD use",
            "# If the header changes, increment this number",
            "HEADER_VERSION = 1\n"
        ]
        self.output_function(detector_information)

        # XDS information
        xds_info = [
            "# XDS information for constructing the XDS.INP file",
            "# Import from more generic detector",
            "# XDS_INP = detector.XDS_INP",
            "# Update the XDS information from the imported detector",
            "# XDS_INP.update({})",
            "# Overwrite XDS information with new data",
            "# XDS_INP = {}\n"
        ]
        self.output_function(xds_info)

        # parse_file_name function
        parse_file_name = [
            "def parse_file_name(fullname):",
            "    \"\"\"",
            "    Parse the fullname of an image and return",
            "    (directory, basename, prefix, run_number, image_number)",
            "    Keyword arguments",
            "    fullname -- the full path name of the image file",
            "    \"\"\"",
            "    # Directory of the file",
            "    directory = os.path.dirname(fullname)\n",
            "    # The basename of the file (i.e. basename - suffix)",
            "    basename = os.path.basename(fullname).rstrip(DETECTOR_SUFFIX)\n",
            "    # The prefix, image number, and run number",
            "    sbase = basename.split(\".\")",
            "    prefix = \".\".join(sbase[0:-1])",
            "    image_number = int(sbase[-1])",
            "    run_number = None",
            "    return directory, basename, prefix, run_number, image_number\n",
        ]
        self.output_function(parse_file_name)

        # create_image_fullname function
        create_image_fullname = [
            "def create_image_fullname(directory,",
            "                          image_prefix,",
            "                          run_number=None,",
            "                          image_number=None):",
            "    \"\"\"",
            "    Create an image name from parts - the reverse of parse\n",
            "    Keyword arguments",
            "    directory -- in which the image file appears",
            "    image_prefix -- the prefix before run number or image number",
            "    run_number -- number for the run",
            "    image_number -- number for the image",
            "    \"\"\"\n",
            "    if not run_number in (None, \"unknown\"):",
            "        filename = \"%s.%s.%04d\" % (image_prefix,",
            "                                   run_number,",
            "                                   image_number)",
            "    else:",
            "        filename = \"%s.%04d\" % (image_prefix,",
            "                                   image_number)\n",
            "    fullname = os.path.join(directory, filename)\n",
            "    return fullname\n",
        ]
        self.output_function(create_image_fullname)

        # create_image_template function
        create_image_template = [
            "def create_image_template(image_prefix, run_number):",
            "    \"\"\"",
            "    Create an image template for XDS",
            "    \"\"\"\n",
            "    image_template = IMAGE_TEMPLATE % image_prefix\n",
            "    return image_template\n"
        ]
        self.output_function(create_image_template)

        # get_data_root_dir function
        get_data_root_dir = [
            "def get_data_root_dir(fullname):",
            "    \"\"\"",
            "    Derive the data root directory from the user directory",
            "    The logic will most likely be unique for each site\n",
            "    Keyword arguments",
            "    fullname -- the full path name of the image file",
            "    \"\"\"\n",
            "    # Isolate distinct properties of the images path",
            "    path_split = fullname.split(os.path.sep)",
            "    data_root_dir = os.path.join(\"/\", *path_split[1:3])\n",
            "    # Return the determined directory",
            "    return data_root_dir\n"
        ]
        self.output_function(get_data_root_dir)

        # read_header function
        read_header = [
            "def read_header(fullname, beam_settings=False):",
            "    \"\"\"",
            "    Read header from image file and return dict\n",
            "    Keyword variables",
            "    fullname -- full path name of the image file to be read",
            "    beam_settings -- source information from site file",
            "    \"\"\"\n",
            "    # Perform the header read from the file",
            "    # If you are importing another detector, this should work",
            "    header = detector.read_header(fullname)\n",
            "    # Return the header",
            "    return header\n"
        ]

        self.output_function(read_header)

def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """Generate a RAPD detector file scaffold"""

    parser = argparse.ArgumentParser(description=commandline_description)

    # Verbosity
    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        dest="verbose",
                        help="Enable verbose feedback")

    # Test mode?
    parser.add_argument("-t", "--test",
                        action="store_true",
                        dest="test",
                        help="Run in test mode")

    # Test mode?
    parser.add_argument("-f", "--force",
                        action="store_true",
                        dest="force",
                        help="Allow overwriting of files")

    # Maintainer
    parser.add_argument("-m", "--maintainer",
                        action="store",
                        dest="maintainer",
                        default="Your name",
                        help="Maintainer's name")

    # Maintainer's email
    parser.add_argument("-e", "--email",
                        action="store",
                        dest="email",
                        default="Your email",
                        help="Maintainer's email")

    # File name to be generated
    parser.add_argument(action="store",
                        dest="file",
                        nargs="?",
                        default=False,
                        help="Name of file to be generated")

    return parser.parse_args()

def main():
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    # Get the commandline args
    commandline_args = get_commandline()

    print commandline_args

    file_generator = DetectorFileGenerator(commandline_args)
    file_generator.run()

if __name__ == "__main__":
    main()
