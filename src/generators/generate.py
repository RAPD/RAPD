"""Script for coordinating multiple types of file generation"""

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
# import from collections import OrderedDict
# import datetime
# import glob
import importlib
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
# import utils.log
import utils.site as site_utils
import utils.text as text


# Possible types of files to generate
MODES = [
    "base",
    "detector",
    "plugin",
    "test",
    ]

def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    # print "main"

    mode = args.pop(0)

    # Allowed mode?
    if mode not in MODES:
        print "rapd.generate helps make rapd files"
        if mode in ("--help", "help", "-h"):
            print "  For help with a particular command use `rapd.generate <command> -h`"
            print "  Availabe commands:"
        else:
            print "%s is not an understood type. Your choices:" % mode
        for allowed_mode in MODES:
            print "      %s" % allowed_mode

        sys.exit(9)

    else:
        # Load the module
        module = importlib.import_module("generators."+mode)

        # Get the commandline args
        commandline_args = module.get_commandline(args)

        # Get the environmental variables
        environmental_vars = site_utils.get_environmental_variables()

        # Look to use environmental_vars to set args
        if commandline_args.maintainer == "Your name":
            if "RAPD_AUTHOR_NAME" in environmental_vars:
                commandline_args.maintainer = environmental_vars["RAPD_AUTHOR_NAME"]

        if commandline_args.email == "Your email":
            if "RAPD_AUTHOR_EMAIL" in environmental_vars:
                commandline_args.email = environmental_vars["RAPD_AUTHOR_EMAIL"]

        print commandline_args

        # Instantiate the FileGenerator
        file_generator = module.FileGenerator(commandline_args)

        # Run
        file_generator.run()

def get_commandline():
    """
    Grabs the commandline. This is a little different from the normal RAPD
    commandline handling - made to pass through to called methods
    """

    # print "get_commandline"

    args = sys.argv[:]

    if len(args) < 2:
        print text.red + "The specified command is invalid. For available options, see `rapd.generate help`." + text.stop
        sys.exit(9)

    else:
        args = args[1:]

    return args

    # # Parse the commandline arguments
    # commandline_description = "Generate RAPD files"
    # parser = argparse.ArgumentParser(description=commandline_description)
    #
    # # A True/False flag
    # parser.add_argument("-v", "--verbise",
    #                     action="store_true",
    #                     dest="verbose",
    #                     help="Control verbosity")
    #
    # # File name to be generated
    # parser.add_argument(action="store",
    #                     dest="type",
    #                     nargs=1,
    #                     default="base",
    #                     choices=TYPES,
    #                     help="Type of file to be generated")
    #
    # # File name to be generated
    # parser.add_argument(action="store",
    #                     dest="file",
    #                     nargs="?",
    #                     default=False,
    #                     help="Name of file to be generated")
    #
    # # Print help message is no arguments
    # if len(sys.argv[1:])==0:
    #     parser.print_help()
    #     parser.exit()
    #
    # return parser.parse_args()

if __name__ == "__main__":

    main_commandline_args = get_commandline()

    main(args=main_commandline_args)
