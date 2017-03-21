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
from argparse import RawTextHelpFormatter
# import from collections import OrderedDict
# import datetime
import glob
import hashlib
# import json
# import logging
# import multiprocessing
import os
# import pprint
# import pymongo
# import re
# import redis
# import shutil
import subprocess
import sys
# import time
# import unittest

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
import test_sets
import utils.log
import utils.site as site

# Software dependencies
VERSIONS = {
# "eiger2cbf": ("160415",)
}

def check_for_data(target, rapd_home, tprint):
    """Look to where test data should be to see if it is there"""

    tprint("Checking test data", level=10, color="white")

    # Establish targets
    target_def = test_sets.DATA_SETS[target]
    target_dir = os.path.join(rapd_home, "test_data", target)
    target_archive = os.path.join(rapd_home, "test_data", target_def["location"])

    # Does target directory exist?
    if not os.path.exists(target_dir):
        tprint("  Data directory not present", level=10, color="white")

        if os.path.exists(target_archive):
            tprint("  Data archive present", level=10, color="white")
            tprint("  Unpacking data archive", level=10, color="white")

            os.chdir(os.path.join(rapd_home, "test_data"))

            tar = subprocess.Popen(["tar", "xvjf", target_def["location"]])
            tar.wait()

            tprint("  Unpacking complete", level=10, color="green")

        else:

            return False

    # Check the sha digest
    data_dir_glob = os.path.join(target_dir, "data/*")
    files = glob.glob(data_dir_glob)
    final_hash = hashlib.sha1()
    for file in files:
        final_hash.update(open(file).read())
    local_sha = final_hash.hexdigest()

    # Read the known digest
    remote_sha_file = os.path.join(target_dir, "data.sha")
    remote_sha = open(remote_sha_file).readlines()[0].rstrip()

    if local_sha != remote_sha:
        tprint("  Data shasum not equal", level=40, color="red")
        return False

    return True

def download_data(target, rapd_home, tprint):
    """Fetch data from NE-CAT server"""

    tprint("Downloading test data", level=10, color="white")

    # Establish targets
    target_def = test_sets.DATA_SETS[target]
    target_dir = os.path.join(rapd_home, "test_data")
    download_path = test_sets.DATA_SERVER + target_def["location"]

    # Move to where the data goes
    os.chdir(target_dir)

    # Download the data
    wget = subprocess.Popen(["wget", download_path])
    wget.wait()

    tprint("  Download complete", level=10, color="green")

    return True

def print_welcome_message(printer):
    """Print a welcome message to the terminal"""

    message = """
------------
RAPD Testing
------------"""
    printer(message, 50, color="blue")

def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """
    # Get the environmental variables
    environmental_vars = site.get_environmental_variables()

    # Output log file is always verbose
    log_level = 10

    # Set up logging
    logger = utils.log.get_logger(logfile_dir="./",
                                  logfile_id="rapd_test",
                                  level=log_level,
                                  console=commandline_args.test)

    # Set up terminal printer
    # Verbosity
    if commandline_args.verbose:
        terminal_log_level = 10
    # elif commandline_args.json:
    #     terminal_log_level = 100
    else:
        terminal_log_level = 50

    tprint = utils.log.get_terminal_printer(verbosity=terminal_log_level,
                                            no_color=commandline_args.no_color)

    print_welcome_message(tprint)

    # Make sure targets are in common format
    if isinstance(args.targets, str):
        targets = [args.targets]
    else:
        targets = args.targets

    for target in targets:

        # Check that data exists
        data_present = check_for_data(target, environmental_vars["RAPD_HOME"], tprint)

        # Download data
        if not data_present:
            download_data(target, environmental_vars["RAPD_HOME"], tprint)

            # Check that data exists again
            data_present = check_for_data(target, environmental_vars["RAPD_HOME"], tprint)

            # We have a problem
            if not data_present:
                raise Exception("There is a problem getting valid test data")


    # Test plugin(s) on data


def get_commandline():
    """
    Grabs the commandline
    """

    # Parse the commandline arguments
    commandline_description = "Generate a generic RAPD file"
    parser = argparse.ArgumentParser(description=commandline_description,
                                     formatter_class=RawTextHelpFormatter)

    # A True/False flag
    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        dest="verbose",
                        help="Request more verbose output")

    # Test mode
    parser.add_argument("--test",
                        action="store_true",
                        dest="test",
                        help="Run in test mode")

    # No color in terminal printing
    parser.add_argument("--color",
                           action="store_false",
                           dest="no_color",
                           help="Use colors in CLI")

    # Test data sets
    targets = "\n".join(test_sets.DATA_SETS.keys())
    parser.add_argument("-t", "--targets",
                        action="store",
                        dest="targets",
                        default=["MINIMAL"],
                        help="Target tests available: \n-----------------------\n" + targets + "\n")

    # Plugins to test
    plugins = "\n".join(test_sets.PLUGINS)
    parser.add_argument("-p", "--plugins",
                        action="store",
                        dest="plugins",
                        # nargs="",
                        default=["index"],
                        help="Plugin(s) to test:\n-----------------\n" + plugins)

    # # Print help message is no arguments
    # if len(sys.argv[1:])==0:
    #     parser.print_help()

    return parser.parse_args()

if __name__ == "__main__":

    commandline_args = get_commandline()

    main(args=commandline_args)
