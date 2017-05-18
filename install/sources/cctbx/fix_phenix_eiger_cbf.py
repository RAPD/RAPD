"""Fix a Phenix distribution to handle Eiger HDF5 files that have been turned into CBF"""

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

__created__ = "2017-05-11"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
# import from collections import OrderedDict
# import datetime
from distutils.spawn import find_executable
# import glob
# import json
# import logging
# import multiprocessing
import os
# import pprint
# import pymongo
# import re
# import redis
import shutil
# import subprocess
import sys
# import time
# import unittest
# import urllib2
# import uuid

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
# import utils.credits as credits

# Software dependencies
VERSIONS = {
# "eiger2cbf": ("160415",)
}

def main():
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    # print "main"

    # Determine the location of the phenix install
    labelit_executable = find_executable("labelit.index")
    # /programs/i386-mac/phenix/1.11.1-2575/phenix-1.11.1-2575/build/bin/labelit.index

    labelit_executable_split = labelit_executable.split(os.path.sep)
    # print labelit_executable_split
    build_index = labelit_executable_split.index("build")
    detectors_dir = os.path.join(os.path.sep.join(labelit_executable_split[:build_index]),
                                 "modules/cctbx_project/iotbx/detectors")
    # print detectors_dir

    config_detector_orig = os.path.join(detectors_dir, "context/config_detector.py")
    pilatus_minicbf = os.path.join(detectors_dir, "pilatus_minicbf.py")

    # print config_detector_orig, os.path.exists(config_detector_orig)
    # print pilatus_minicbf, os.path.exists(pilatus_minicbf)

    for target_file in (config_detector_orig, pilatus_minicbf):
        print "\nFixing %s" % os.path.basename(target_file)
        shutil.move(target_file, target_file+"_orig")
        shutil.copy(os.path.basename(target_file), target_file)

    print "Done."

def get_commandline():
    """
    Grabs the commandline
    """

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Generate a generic RAPD file"

    my_parser = argparse.ArgumentParser(description=commandline_description)

    # A True/False flag
    my_parser.add_argument("-c", "--commandline",
                           action="store_true",
                           dest="commandline",
                           help="Generate commandline argument parsing")

    # File name to be generated
    my_parser.add_argument(action="store",
                           dest="file",
                           nargs="?",
                           default=False,
                           help="Name of file to be generated")

    # Print help message is no arguments
    if len(sys.argv[1:])==0:
        my_parser.print_help()
        my_parser.exit()

    return my_parser.parse_args()

if __name__ == "__main__":

    # Execute code
    main()
