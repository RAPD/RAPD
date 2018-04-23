"""Wrapper for launching echo"""

"""
This file is part of RAPD

Copyright (C) 2017-2018, Cornell University
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

__created__ = "2017-07-11"
__maintainer__ = "Your name"
__email__ = "Your email"
__status__ = "Development"

# Standard imports
import argparse
# import from collections import OrderedDict
# import datetime
# import glob
# import json
# import logging
import multiprocessing
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
# import urllib2
import uuid

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
# import utils.credits as credits
import utils.credits as credits
import utils.global_vars as rglobals
import utils.log
import utils.modules as modules
import utils.text as text
import utils.commandline_utils as commandline_utils
import detectors.detector_utils as detector_utils

def construct_command(commandline_args):
    """Put together the command for the plugin"""

    # The task to be carried out
    command = {
        "command": "ECHO",
        "process_id": uuid.uuid1().get_hex(),
        "status": 0,
        }

    # Work directory
    work_dir = commandline_utils.check_work_dir(
        os.path.join(os.path.abspath(os.path.curdir), run_repr),
        active=True,
        up=commandline_args.dir_up)

    command["directories"] = {
        "work": work_dir
        }

    # Check the work directory
    commandline_utils.check_work_dir(command["directories"]["work"], True)

    # Information on input
    command["input_data"] = {
        "datafile": os.path.abspath(commandline_args.datafile)
    }

    # Plugin settings
    command["preferences"] = {
        "clean": commandline_args.clean,
        "json": commandline_args.json,
        "no_color": commandline_args.no_color,
        "nproc": commandline_args.nproc,
        "progress": commandline_args.progress,
        "test": commandline_args.test,
        "verbose": commandline_args.verbose,
    }

    return command

def get_commandline():
    """Grabs the commandline"""

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Launch echo plugin"
    my_parser = argparse.ArgumentParser(description=commandline_description)

    # Run in test mode
    my_parser.add_argument("-t", "--test",
                           action="store_true",
                           dest="test",
                           help="Run in test mode")

    # Verbose/Quiet are a pair of opposites
    # Recommend defaulting to verbose during development and to
    # quiet during production
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

    # Messy/Clean are a pair of opposites.
    # Recommend defaulting to messy during development and to
    # clean during production
    # Messy
    #my_parser.add_argument("--messy",
    #                       action="store_false",
    #                       dest="clean",
    #                       help="Keep intermediate files")

    # Clean
    my_parser.add_argument("--clean",
                           action="store_true",
                           dest="clean",
                           help="Clean up intermediate files")

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

    # Output progress
    my_parser.add_argument("--progress",
                           action="store_true",
                           dest="progress",
                           help="Output progess to terminal")

    # Multiprocessing
    my_parser.add_argument("--nproc",
                           dest="nproc",
                           type=int,
                           default=max(1, multiprocessing.cpu_count() - 1),
                           help="Number of processors to employ")

    # Positional argument
    my_parser.add_argument(action="store",
                           dest="datafile",
                           nargs="?",
                           default=False,
                           help="Name of file to be analyzed")

    # Print help message if no arguments
    if len(sys.argv[1:]) == 0:
        my_parser.print_help()
        my_parser.exit()

    args = my_parser.parse_args()

    # Insert logic to check or modify args here

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
                                  logfile_id="rapd_echo",
                                  level=log_level,
                                  console=commandline_args.test)

    # Set up terminal printer
    # tprint prints to the terminal, taking the arguments
    #     arg - the string to be printed (if using level of "progress" this needs to be an int)
    #     level - value 0 to 99 or "progress". Do NOT use a value of 100 or above
    #             50 - alert
    #             40 - error
    #             30 - warning
    #             20 - info
    #             10 - debug
    #     color - color to print ("red" and so forth. See list in utils/text)
    #     newline - put in False if you don't want a newline at the end of your print
    #     
    # Verbosity
    if commandline_args.verbose:
        terminal_log_level = 10
    elif commandline_args.json:
        terminal_log_level = 100
    else:
        terminal_log_level = 50

    tprint = utils.log.get_terminal_printer(verbosity=terminal_log_level,
                                            no_color=commandline_args.no_color,
                                            progress=commandline_args.progress)

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

    # Should working directory go up or down?
    if environmental_vars.get("RAPD_DIR_INCREMENT") in ("up", "UP"):
        commandline_args.dir_up = True
    else:
        commandline_args.dir_up = False

    # Construct the command
    command = construct_command(commandline_args=commandline_args,
                                logger=logger)

    # Load the plugin
    plugin = modules.load_module(seek_module="plugin",
                                 directories=["plugins.echo"],
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

    # Execute code
    main()
