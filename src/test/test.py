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

__created__ = "2017-03-20"
_maintainer__ = "Your name"
__email__ = "Your email"
__status__ = "Development"

# Standard imports
import argparse
# import from collections import OrderedDict
# import datetime
# import glob
# import json
# import logging
# import multiprocessing
# import os
# import pprint
# import pymongo
# import re
# import redis
# import shutil
# import subprocess
import sys
# import time
# import unittest

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils

# Software dependencies
VERSIONS = {
# "eiger2cbf": ("160415",)
}

def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    print "main"
    print args

def get_commandline():
    """
    Grabs the commandline
    """

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Generate a generic RAPD file"
    parser = argparse.ArgumentParser(description=commandline_description)

    # # A True/False flag
    # parser.add_argument("-c", "--commandline",
    #                     action="store_true",
    #                     dest="commandline",
    #                     help="Generate commandline argument parsing")

    # File name to be generated
    parser.add_argument(action="store",
                        dest="target",
                        nargs="?",
                        default=False,
                        help="Target test")

    # # Print help message is no arguments
    # if len(sys.argv[1:])==0:
    #     parser.print_help()

    return parser.parse_args()

if __name__ == "__main__":

    commandline_args = get_commandline()

    main(args=commandline_args)
