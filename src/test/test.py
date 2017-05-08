"""Test running for RAPD project"""

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
import json
# import logging
# import multiprocessing
import os
# from pprint import pprint
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
import utils.globals as rglobals
import utils.log
import utils.site as site

# Cache for test data
TEST_CACHE = rglobals.PDBQ_SERVER.TEST_CACHE

# Software dependencies
VERSIONS = {
    # "eiger2cbf": ("160415",)
}

def run_unit(plugin, tprint, mode="DEPENDENCIES", verbose=True):
    """Run unit testing for plugin"""

    tprint("  Running unit testing for %s" % plugin,
           10,
           "white")

    # Run unit testing
    if verbose:
        verbosity = 10
    else:
        verbosity = 1

    test_module = importlib.import_module(test_sets.PLUGINS[plugin]+".test")

    runner = unittest.TextTestRunner(verbosity=verbosity)

    if mode == "DEPENDENCIES":
        runner.run(test_module.get_dependencies_tests())

    elif mode == "ALL":
        runner.run(test_module.get_all_tests())

    tprint("  Finished running unit testing for %s" % plugin,
           10,
           "white")

def run_processing(target, plugin, rapd_home, tprint, verbose=True):
    """Run a processing test"""

    tprint("  Testing %s" % plugin, 99, "white")

    target_def = test_sets.DATA_SETS[target]
    command = target_def[plugin+"_command"]
    test_module = importlib.import_module(test_sets.PLUGINS[plugin]+".test")

    # Change to working directory
    work_dir = os.path.join(TEST_CACHE, target)
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
    os.chdir(work_dir)

    # Run the process
    tprint("    Running test with command `%s`" % command, 10, "white")
    if verbose:
        proc = subprocess.Popen(command, shell=True)
    else:
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.wait()

    # Read in the results
    tprint("    Comparing results", 10, "white")
    result_standard = json.loads(open(plugin+".json", "r").readlines()[0])
    result_test = json.loads(open(target_def[plugin+"_result"], "r").readlines()[0])

    test_successful = test_module.compare_results(result_standard, result_test, tprint)

    if test_successful:
        tprint("  %s tests sucessful" % plugin, 99, "green")
    else:
        tprint("  %s tests fail" % plugin, 10, "red")

    return test_successful

def check_for_data(target, rapd_home, tprint):
    """Look to where test data should be to see if it is there"""

    tprint("Checking test data", level=10, color="white")

    # Establish targets
    target_def = test_sets.DATA_SETS[target]
    target_dir = os.path.join(TEST_CACHE, target)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    target_archive = os.path.join(TEST_CACHE, target_def["location"])

    # Does target directory exist?
    if not os.path.exists(target_dir):
        tprint("  Data directory not present", level=10, color="white")

        if os.path.exists(target_archive):
            tprint("  Data archive present", level=10, color="white")
            tprint("  Unpacking data archive", level=10, color="white")

            os.chdir(TEST_CACHE)

            # Unpack archive
            tar = subprocess.Popen(["tar", "xvjf", target_def["location"]])
            tar.wait()

            # Remove archive
            os.unlink(target_def["location"])

            tprint("  Unpacking complete", level=10, color="green")

        else:
            return False
    else:
        tprint("  Data directory present", level=10, color="white")

    # Check the sha digest
    tprint("  Checking data integrity", level=10, color="white")
    data_dir_glob = os.path.join(target_dir, "data/*")
    files = glob.glob(data_dir_glob)
    files.sort()
    final_hash = hashlib.sha1()
    for my_file in files:
        final_hash.update(open(my_file).read())
    local_sha = final_hash.hexdigest()

    # Read the known digest
    remote_sha_file = os.path.join(target_dir, "data.sha")
    remote_sha = open(remote_sha_file).readlines()[0].rstrip()

    if local_sha != remote_sha:
        tprint("  Data shasum not equal", level=40, color="red")
        raise Exception("Data integrity compromised. Reccomend erase and \
redownload")
    else:
        tprint("  Data integrity OK", level=10, color="green")

    return True

def download_data(target, rapd_home, force, tprint):
    """Fetch data from NE-CAT server"""

    tprint("Downloading test data", level=50, color="white")

    # Establish targets
    target_def = test_sets.DATA_SETS[target]
    target_dir = os.path.join(TEST_CACHE)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    download_path = test_sets.DATA_SERVER + target_def["location"]

    # Move to where the data goes
    os.chdir(target_dir)

    # Check for data already present
    if os.path.exists(target_def["location"]):
        if force:
            tprint("  Erasing old test data", level=10, color="white")
            os.unlink(target_def["location"])
            os.unlink(target_def["location"].replace(".tar.bz2", ""))
        else:
            tprint("**Data already present. use --force option to allow overwriting**",
                   10,
                   "red")
            sys.exit(9)

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

    # pprint(args)
    # sys.exit()

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

    # Make sure targets are in common format
    if isinstance(args.targets, str):
        targets = [args.targets]
    else:
        targets = args.targets

    # Handle the all setting for plugins
    if "all" in args.plugins:
        plugins = []
        for plugin in test_sets.PLUGINS.keys():
            if not plugin == "all":
                plugins.append(plugin)
    else:
        plugins = args.plugins

    # Check dependencies first
    if "DEPENDENCIES" in targets:
        targets.pop(targets.index("DEPENDENCIES"))
        targets.insert(0, "DEPENDENCIES")

    for target in targets:

        if target == "DEPENDENCIES":

            tprint("Dependency testing", 10, "white")
            for plugin in plugins:
                # Run normal unit testing
                run_unit(plugin, tprint, "DEPENDENCIES", args.verbose)

        else:
            # Check that data exists
            data_present = check_for_data(target,
                                          environmental_vars["RAPD_HOME"],
                                          tprint)

            # Download data
            if not data_present:
                download_data(target,
                              environmental_vars["RAPD_HOME"],
                              args.force,
                              tprint)

                # Check that data exists again
                data_present = check_for_data(target,
                                              environmental_vars["RAPD_HOME"],
                                              tprint)

                # We have a problem
                if not data_present:
                    raise Exception("There is a problem getting valid test data")

            tprint("Plugin testing", 99, "white")
            for plugin in plugins:

                # Run unit testing
                run_unit(plugin, tprint, "ALL", args.verbose)

                run_processing(target,
                               plugin,
                               environmental_vars["RAPD_HOME"],
                               tprint,
                               args.verbose)


def get_commandline():
    """
    Grabs the commandline
    """

    # Parse the commandline arguments
    commandline_description = "RAPD project testing"
    parser = argparse.ArgumentParser(description=commandline_description,
                                     formatter_class=RawTextHelpFormatter)

    # A True/False flag
    parser.add_argument("-q", "--quiet",
                        action="store_false",
                        dest="verbose",
                        help="Request less output")

    # Test mode
    parser.add_argument("--test",
                        action="store_true",
                        dest="test",
                        help="Run in test mode")

    # Force
    parser.add_argument("-f", "--force",
                        action="store_true",
                        dest="force",
                        help="Allow overwrite of test data")

    # No color in terminal printing
    parser.add_argument("--color",
                        action="store_false",
                        dest="no_color",
                        help="Use colors in CLI")

    # Test data sets
    keys = test_sets.DATA_SETS.keys()
    keys.sort()
    targets = "\n".join(keys)
    parser.add_argument("-t", "--targets",
                        action="store",
                        dest="targets",
                        nargs="+",
                        default=["DEPENDENCIES"],
                        help="Target tests available: \n-----------------------\n" + targets + "\n")

    # Plugins to test
    plugins = test_sets.PLUGINS.keys()
    plugins.sort()
    plugins = "\n".join(plugins)
    parser.add_argument("-p", "--plugins",
                        action="store",
                        dest="plugins",
                        nargs="+",
                        default=["integrate"],
                        help="Plugin(s) to test:\n-----------------\n" + plugins)

    # Print help message is no arguments
    # if len(sys.argv[1:])==0:
    #     parser.print_help()
    #     sys.exit()

    args = parser.parse_args()

    return args

if __name__ == "__main__":

    commandline_args = get_commandline()

    main(args=commandline_args)
