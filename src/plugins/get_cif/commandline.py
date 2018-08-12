"""Wrapper for launching get_cif"""

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

__created__ = "2017-04-24"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
# import from collections import OrderedDict
# import datetime
# import glob
# import json
# import logging
# import multiprocessing
import os
# import pprint
# import pymongo
# import re
# import redis
# import shutil
# import subprocess
import sys
# import time
# import unittest
import uuid

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
# import utils.credits as credits
import utils.credits as credits
import utils.log
import utils.modules as modules
import utils.text as text
import utils.commandline_utils as commandline_utils
import detectors.detector_utils as detector_utils

def construct_command(commandline_args, logger):
    """Put together the command for the plugin"""

    # The task to be carried out
    command = {
        "command": "GET_CIF",
        "process_id": uuid.uuid1().get_hex(),
        "status": 0,
        }

    # Information on input
    command["input_data"] = {
        # "data_file": os.path.abspath(commandline_args.data_file)
        "pdb_codes": commandline_args.pdb_codes
    }

    # Plugin settings
    command["preferences"] = {
        "cached": commandline_args.cached,
        "force": commandline_args.force,
        "json": commandline_args.json,
        # "nproc": commandline_args.nproc,
        "pdb": commandline_args.pdb,
        "test": commandline_args.test,
        }

    logger.debug("Command for get_pdb plugin: %s" %command)

    return command

def get_commandline():
    """Grabs the commandline"""

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Launch get_cif plugin"
    my_parser = argparse.ArgumentParser(description=commandline_description)

    # Run in test mode
    my_parser.add_argument("-t", "--test",
                           action="store_true",
                           dest="test",
                           help="Run in test mode")

    # Force
    my_parser.add_argument("-f", "--force",
                           action="store_true",
                           dest="force",
                           help="Allow overwrite of the target files")

    # Verbose
    #my_parser.add_argument("-v", "--verbose",
    #                       action="store_true",
    #                       dest="verbose",
    #                       help="More output")

    # Quiet
    my_parser.add_argument("-q", "--quiet",
                           action="store_false",
                           dest="verbose",
                           help="More output")

    # Color
    #my_parser.add_argument("--color",
    #                       action="store_false",
    #                       dest="no_color",
    #                       help="Color the terminal output")

    # No color
    my_parser.add_argument("--nocolor",
                           action="store_true",
                           dest="no_color",
                           help="Do not color the terminal output")

    # JSON Output
    my_parser.add_argument("-j", "--json",
                           action="store_true",
                           dest="json",
                           help="Output JSON format string")

    # Ignore cached file
    my_parser.add_argument("--nocache",
                           action="store_false",
                           dest="cached",
                           help="Ignore cached version and download file")

    # Run in test mode
    my_parser.add_argument("--pdb",
                           action="store_true",
                           dest="pdb",
                           help="Retrieve PDB files, not CIF")

    # Positional argument
    my_parser.add_argument(action="store",
                           dest="pdb_codes",
                           nargs="+",
                           default=False,
                           help="PDB codes to be retrieved")

    # Print help message if no arguments
    if len(sys.argv[1:]) == 0:
        my_parser.print_help()
        my_parser.exit()

    args = my_parser.parse_args()

    # Insert logic to check or modify args here

    # ALL CAPS PDB CODES
    tmp_args = []
    for pdb_code in args.pdb_codes:
        tmp_args.append(pdb_code.upper())
    args.pdb_codes = tmp_args

    return args

def print_welcome_message(printer):
    """Print a welcome message to the terminal"""
    message = """
------------
RAPD Example
------------"""
    printer(message, 50, color="blue")

def main():
    """
    The main process
    Setup logging and instantiate the model"""

    # Get the commandline args
    commandline_args = get_commandline()

    # Output log file is always verbose
    log_level = 10

    # Set up logging
    logger = utils.log.get_logger(logfile_dir="./",
                                  logfile_id="rapd_get_cif",
                                  level=log_level,
                                  console=commandline_args.test)

    # Set up terminal printer
    # Verbosity
    if commandline_args.verbose:
        terminal_log_level = 10
    elif commandline_args.json:
        terminal_log_level = 100
    else:
        terminal_log_level = 50

    tprint = utils.log.get_terminal_printer(verbosity=terminal_log_level,
                                            no_color=commandline_args.no_color)

    print_welcome_message(tprint)

    logger.debug("Commandline arguments:")
    tprint(arg="\nCommandline arguments:", level=10, color="blue")
    for pair in commandline_args._get_kwargs():
        logger.debug("  arg:%s  val:%s", pair[0], pair[1])
        tprint(arg="  arg:%-20s  val:%s" % (pair[0], pair[1]), level=10,             color="white")

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()
    logger.debug("" + text.info + "Environmental variables" + text.stop)
    tprint("\nEnvironmental variables", level=10, color="blue")
    for key, val in environmental_vars.iteritems():
        logger.debug("  " + key + " : " + val)
        tprint(arg="  arg:%-20s  val:%s" % (key, val), level=10, color="white")

    # Construct the command
    command = construct_command(commandline_args=commandline_args,
                                logger=logger)

    # Load the plugin
    plugin = modules.load_module(seek_module="plugin",
                                 directories=["plugins.get_cif"],
                                 logger=logger)

    # Print plugin info
    tprint(arg="\nPlugin information", level=10, color="blue")
    tprint(arg="  Plugin type:    %s" % plugin.PLUGIN_TYPE, level=10,             color="white")
    tprint(arg="  Plugin subtype: %s" % plugin.PLUGIN_SUBTYPE, level=10,             color="white")
    tprint(arg="  Plugin version: %s" % plugin.VERSION, level=10, color="white")
    tprint(arg="  Plugin id:      %s" % plugin.ID, level=10, color="white")

    # Run the plugin
    plugin.RapdPlugin(command, tprint, logger)

if __name__ == "__main__":


    main()
