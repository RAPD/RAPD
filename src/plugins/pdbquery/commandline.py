"""Wrapper for launching pdbquery"""

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

__created__ = "2017-04-20"
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

def construct_command(image_headers, commandline_args, detector_module, logger):
    """Put together the command for the plugin"""

    # The task to be carried out
    command = {
        "command": "INDEX",
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
        "work": os.path.join(os.path.abspath(os.path.curdir), "pdbquery")# run_repr)
        }

    # Handle work directory
    commandline_utils.check_work_dir(command["directories"]["work"], True)

    # Image data
    images = image_headers.keys()
    images.sort()
    counter = 0
    for image in images:
        counter += 1
        command["header%d" % counter] = image_headers[image]
    if counter == 1:
        command["header2"] = None

    # Plugin settings
    command["preferences"] = {}

    # JSON output?
    command["preferences"]["json_output"] = commandline_args.json

    # Show plots
    command["preferences"]["show_plots"] = commandline_args.plotting

    logger.debug("Command for pdbquery plugin: %s", command)

    return command

def get_commandline():
    """Grabs the commandline"""

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Launch pdbquery plugin"
    my_parser = argparse.ArgumentParser(description=commandline_description)

    # A True/False flag
    my_parser.add_argument("-c", "--commandline",
                           action="store_true",
                           dest="commandline",
                           help="Generate commandline argument parsing")

    # Positional argument
    my_parser.add_argument(action="store",
                           dest="file",
                           nargs="?",
                           default=False,
                           help="Name of file to be generated")

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
        terminal_log_level = 30
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

    # List sites?
    if commandline_args.listsites:
        tprint(arg="\nAvailable sites", level=99, color="blue")
        commandline_utils.print_sites(left_buffer="  ")
        if not commandline_args.listdetectors:
            sys.exit()

    # List detectors?
    if commandline_args.listdetectors:
        tprint(arg="Available detectors", level=99, color="blue")
        commandline_utils.print_detectors(left_buffer="  ")
        sys.exit()

    # Get the data files
    data_files = commandline_utils.analyze_data_sources(sources=commandline_args.sources,
                                                        mode="index")

    if "hdf5_files" in data_files:
        logger.debug("HDF5 source file(s)")
        tprint(arg="\nHDF5 source file(s)", level=99, color="blue")
        logger.debug(data_files["hdf5_files"])
        for data_file in data_files["hdf5_files"]:
            tprint(arg="  " + data_file, level=99, color="white")
        logger.debug("CBF file(s) from HDF5 file(s)")
        tprint(arg="\nData files", level=99, color="blue")
    else:
        logger.debug("Data file(s)")
        tprint(arg="\nData file(s)", level=99, color="blue")

    if len(data_files) == 0:
        tprint(arg="  None", level=99, color="white")
    else:
        logger.debug(data_files["files"])
        for data_file in data_files["files"]:
            tprint(arg="  " + data_file, level=99, color="white")

    # Need data
    if len(data_files) == 0 and commandline_args.test == False:
        if logger:
            logger.exception("No files input for indexing.")
        raise Exception, "No files input for indexing."

    # Too much data?
    if len(data_files) > 2:
        if logger:
            logger.exception("Too many files for indexing. 1 or 2 images accepted")
        raise Exception, "Too many files for indexing. 1 or 2 images accepted"

    # Get site - commandline wins over the environmental variable
    site = False
    site_module = False
    detector = {}
    detector_module = False
    if commandline_args.site:
        site = commandline_args.site
    elif environmental_vars.has_key("RAPD_SITE"):
        site = environmental_vars["RAPD_SITE"]

    # Detector is defined by the user
    if commandline_args.detector:
        detector = commandline_args.detector
        detector_module = detector_utils.load_detector(detector)

    # If no site or detector, try to figure out the detector
    if not (site or detector):
        detector = detector_utils.get_detector_file(data_files["files"][0])
        if isinstance(detector, dict):
            if detector.has_key("site"):
                site_target = detector.get("site")
                site_file = utils.site.determine_site(site_arg=site_target)
                # print site_file
                site_module = importlib.import_module(site_file)
                detector_target = site_module.DETECTOR.lower()
                detector_module = detector_utils.load_detector(detector_target)
            elif detector.has_key("detector"):
                site_module = False
                detector_target = detector.get("detector")
                detector_module = detector_utils.load_detector(detector_target)

    # Have a detector - read in file data
    if detector_module:
        image_headers = {}
        for data_file in data_files["files"]:
            if site_module:
                image_headers[data_file] = detector_module.read_header(data_file,
                                                                       site_module.BEAM_SETTINGS)
            else:
                image_headers[data_file] = detector_module.read_header(data_file)

        logger.debug("Image headers: %s", image_headers)
        print_headers(tprint, image_headers)

        command = construct_command(image_headers=image_headers,
                                    commandline_args=commandline_args,
                                    detector_module=detector_module,
                                    logger=logger)
    else:
        if logger:
            logger.exception("No detector module found")
        raise Exception("No detector module found")

    plugin = modules.load_module(seek_module="plugin",
                                 directories=["plugins.pdbquery"],
                                 logger=logger)

    tprint(arg="\nPlugin information", level=10, color="blue")
    tprint(arg="  Plugin type:    %s" % plugin.PLUGIN_TYPE, level=10, color="white")
    tprint(arg="  Plugin subtype: %s" % plugin.PLUGIN_SUBTYPE, level=10, color="white")
    tprint(arg="  Plugin version: %s" % plugin.VERSION, level=10, color="white")
    tprint(arg="  Plugin id:      %s" % plugin.ID, level=10, color="white")

    plugin.RapdPlugin(None, command, tprint, logger)

if __name__ == "__main__":

    commandline_args = get_commandline()

    main(args=commandline_args)
