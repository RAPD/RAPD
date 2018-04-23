"""Simulate a data collection"""

"""
This file is part of RAPD

Copyright (C) 2018, Cornell University
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

__created__ = "2018-04-21"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
from argparse import RawTextHelpFormatter
# import from collections import OrderedDict
# import datetime
import glob
import hashlib
import importlib
# import logging
# import multiprocessing
import os
from pprint import pprint
# import pymongo
# import re
# import redis
# import shutil
import subprocess
import sys
# import time
import unittest

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
import test_sets
import utils.global_vars as rglobals
import utils.log
import utils.site as site
import utils.text as r_text
from bson.objectid import ObjectId

# Cache for test data
TEST_CACHE = rglobals.TEST_CACHE

# Software dependencies
VERSIONS = {
    # "eiger2cbf": ("160415",)
}

def print_welcome_message(printer):
    """Print a welcome message to the terminal"""

    message = """
RAPD Run Simulation
-------------------"""
    printer(message, 50, color="blue")

def main():
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    commandline_args = get_commandline()

    pprint(commandline_args)

    # Get the environmental variables
    environmental_vars = site.get_environmental_variables()

    # Output log file is always verbose
    log_level = 10

    # Set up logging
    # logger = utils.log.get_logger(logfile_dir="./",
    #                               logfile_id="rapd_test",
    #                               level=log_level,
    #                               console=commandline_args.test)

    # Set up terminal printer
    # Verbosity
    if commandline_args.verbose:
        terminal_log_level = 10
    else:
        terminal_log_level = 50

    tprint = utils.log.get_terminal_printer(verbosity=terminal_log_level,
                                            no_color=commandline_args.no_color)

    print_welcome_message(tprint)

    # Make sure directories are there
    if not os.path.exists(commandline_args.source):
        raise IOError("Source directory %s does not exist" % commandline_args.source)
    if not os.path.exists(commandline_args.target):
        raise IOError("Target directory %s does not exist" % commandline_args.target)

    # Gather the images
    source_template = os.path.join(commandline_args.source, commandline_args.template)



    sys.exit()

    # Make sure targets are in common format
    if isinstance(commandline_args.targets, str):
        targets = [commandline_args.targets]
    else:
        targets = commandline_args.targets

    # Handle the all setting for plugins
    if "all" in commandline_args.plugins:
        plugins = []
        for plugin in test_sets.PLUGINS.keys():
            if not plugin == "all":
                plugins.append(plugin)
    else:
        plugins = commandline_args.plugins

    # Check dependencies first
    if "DEPENDENCIES" in targets:
        targets.pop(targets.index("DEPENDENCIES"))
        targets.insert(0, "DEPENDENCIES")

    for target in targets:

        if target == "DEPENDENCIES":

            tprint("Dependency testing", 10, "white")
            for plugin in plugins:
                # Run normal unit testing
                run_unit(plugin, tprint, "DEPENDENCIES", commandline_args.verbose)

        else:
            # Check that data exists
            data_present = check_for_data(target,
                                          tprint)

            # Download data
            if not data_present:
                download_data(target,
                              commandline_args.force,
                              tprint)

                # Check that data exists again
                data_present = check_for_data(target,
                                              tprint)

                # We have a problem
                if not data_present:
                    raise Exception("There is a problem getting valid test \
data")

            tprint("Plugin testing", 99, "white")
            for plugin in plugins:

                # Run unit testing
                run_unit(plugin, tprint, "ALL", commandline_args.verbose)

                run_processing(target,
                               plugin,
                               tprint,
                               commandline_args.verbose)


def get_commandline():
    """
    Grabs the commandline
    """

    # Parse the commandline arguments
    commandline_description = "RAPD project testing"
    parser = argparse.ArgumentParser(description=commandline_description,
                                     formatter_class=RawTextHelpFormatter)

    # No color in terminal printing
    parser.add_argument("--color",
                        action="store_false",
                        dest="no_color",
                        help="Use colors in CLI")

    # Delay before frames are moved
    parser.add_argument("-d", "--delay",
                        action="store",
                        dest="delay",
                        type=float,
                        default=5.0,
                        help="Delay in seconds before first frame is copied")

    # Interval beween frames copying
    parser.add_argument("-i", "--interval",
                        action="store",
                        dest="interval",
                        type=float,
                        default=0.2,
                        help="Interval in seconds between copying frames")

    # Force
    parser.add_argument("-f", "--force",
                        action="store_true",
                        dest="force",
                        help="Allow overwrite of test data")

    # Quiet output
    parser.add_argument("-q", "--quiet",
                        action="store_false",
                        dest="verbose",
                        help="Request less output")

    # Source directory
    parser.add_argument("-s", "--source",
                        action="store",
                        dest="source",
                        default="./",
                        help="The source directory of images to use for simulation")

    # Target directory
    parser.add_argument("-t", "--target",
                        action="store",
                        dest="target",
                        default="./",
                        help="The target directory of images to use for simulation")

    # Template for images
    parser.add_argument("--template",
                        action="store",
                        dest="template",
                        default="*.cbf",
                        help="The template for images to use for simulation in glob-format")

    # Test mode
    parser.add_argument("--test",
                        action="store_false",
                        dest="active",
                        help="Run in test mode")

    args = parser.parse_args()

    if args.source == args.target:
        print "\n"+r_text.error+"!!ERROR!! Source and target directories cannot be the same"+r_text.stop+"\n"
        parser.print_help()
        sys.exit(-1)

    return args

if __name__ == "__main__":

    main()
