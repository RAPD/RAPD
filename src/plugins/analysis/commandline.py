"""Wrapper for launching analysis"""

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

__created__ = "2017-04-06"
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
import utils.log
import utils.modules as modules
import utils.text as text
import utils.commandline_utils as commandline_utils
import detectors.detector_utils as detector_utils

def construct_command(commandline_args, logger):
    """Put together the command for the plugin"""

    # The task to be carried out
    command = {
        "command": "ANALYSIS",
        "process_id": uuid.uuid1().get_hex(),
        }

    # Working directory
    # image_numbers = []
    # image_template =
    # for _, header in image_headers.iteritems():
    #     image_numbers.append(str(header["image_number"]))
    #     image_template = header["image_template"]
    # image_numbers.sort()
    # run_repr = "rapd_index_" + image_template.replace(detector_module.DETECTOR_SUFFIX, "").replace("?", "")
    # run_repr += "+".join(image_numbers)

    command["directories"] = {
        "work": os.path.join(os.path.abspath(os.path.curdir), "analysis")
        }

    # Handle work directory
    commandline_utils.check_work_dir(command["directories"]["work"], True)

    # Information on input
    command["input_data"] = {
        "datafile": os.path.abspath(commandline_args.datafile)
    }

    # Plugin settings
    command["preferences"] = {}

    # JSON output?
    # command["preferences"]["json_output"] = commandline_args.json

    # Show plots
    # command["preferences"]["show_plots"] = commandline_args.plotting

    logger.debug("Command for index plugin: %s", command)

    return command

def get_commandline():
    """Grabs the commandline"""

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Launch analysis plugin"
    my_parser = argparse.ArgumentParser(description=commandline_description)

    # A True/False flag
    my_parser.add_argument("-l", "--logging-off",
                           action="store_false",
                           dest="logging",
                           help="Turn logging off")

    # A True/False flag
    my_parser.add_argument("-t", "--test",
                           action="store_true",
                           dest="test",
                           help="Turn test mode on")

    # A True/False flag
    my_parser.add_argument("-q", "--quiet",
                           action="store_false",
                           dest="verbose",
                           help="Reduce output")

    # A True/False flag
    my_parser.add_argument("-c", "--color",
                           action="store_false",
                           dest="no_color",
                           help="Colorize terminal output")

    # Positional argument
    my_parser.add_argument(action="store",
                           dest="datafile",
                           nargs="?",
                           default=False,
                           help="Name of file to be analyzed")

    # Print help message if no arguments
    if len(sys.argv[1:])==0:
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
    if commandline_args.logging:
        logger = utils.log.get_logger(logfile_dir="./",
                                      logfile_id="rapd_index",
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
        tprint(arg="  arg:%-20s  val:%s" % (pair[0], pair[1]), level=10, color="white")

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()
    logger.debug("" + text.info + "Environmental variables" + text.stop)
    tprint("\nEnvironmental variables", level=10, color="blue")
    for key, val in environmental_vars.iteritems():
        logger.debug("  " + key + " : " + val)
        tprint(arg="  arg:%-20s  val:%s" % (key, val), level=10, color="white")

        command = construct_command(commandline_args=commandline_args,
                                    logger=logger)

    plugin = modules.load_module(seek_module="plugin",
                                 directories=["plugins.analysis"],
                                 logger=logger)

    tprint(arg="\nPlugin information", level=10, color="blue")
    tprint(arg="  Plugin type:    %s" % plugin.PLUGIN_TYPE, level=10, color="white")
    tprint(arg="  Plugin subtype: %s" % plugin.PLUGIN_SUBTYPE, level=10, color="white")
    tprint(arg="  Plugin version: %s" % plugin.VERSION, level=10, color="white")
    tprint(arg="  Plugin id:      %s" % plugin.ID, level=10, color="white")

    plugin.RapdPlugin(command, tprint, logger)

if __name__ == "__main__":

    main()
