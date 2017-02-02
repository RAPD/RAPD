"""
Wrapper for launching an integration on images
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2016-2017 Cornell University
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

__created__ = "2016-11-17"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
import os
import pprint
import sys
import uuid

# RAPD imports
import utils.log
from utils.modules import load_module
import utils.text as text
import commandline_utils
import detectors.detector_utils as detector_utils

def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """Launch an index & strategy on input image(s)"""
    parser = argparse.ArgumentParser(parents=[commandline_utils.dp_parser],
                                     description=commandline_description)

    # Start frame
    parser.add_argument("--start",
                        action="store",
                        dest="start_image",
                        default=False,
                        type=int,
                        help="First image")

    # End frame
    parser.add_argument("--end",
                        action="store",
                        dest="end_image",
                        default=False,
                        type=int,
                        help="Last image")

    # Directory or files
    parser.add_argument(action="store",
                        dest="template",
                        default=False,
                        help="Template for image files")

    return parser.parse_args()

def get_image_data(data_file, detector_module):
    """
    Get the image data and return given a filename
    """

    print "get_image_data", data_file

    return detector_module.read_header(data_file)

def get_run_data(detector_module, image_0_data, image_n_data):
    """
    Create and return run data
    {'distance' : '380.0',
                'image_prefix' : 'lysozym-1',
                'image_template' : 'lysozym-1.????',
                'run_number' : '1',
                'start' : 1,
                'time' : 1.0,
                'directory' : '/gpfs6/users/necat/test_data/lyso/',
                'total' : 500}
    """

    print "get_run_data"
    pprint.pprint(image_0_data)
    pprint.pprint(image_n_data)

    run_data = {
        "directory": image_0_data.get("directory"),
        "distance": str(image_0_data.get("distance")),
        "image_prefix": image_0_data.get("image_prefix"),
        "image_template": detector_module.create_image_template(image_0_data.get("image_prefix"), image_0_data.get("run_number")),
        "run_number": str(image_0_data.get("run_number")),
        "start": str(image_0_data.get("image_number")),
        "time": str(image_0_data.get("time")),
        "total": str(image_n_data.get("image_number") - image_0_data.get("image_number") + 1),
        }

    return run_data

def construct_command(image_0_data, run_data, commandline_args, detector_module, logger):
    """
    Put together the command for the agent
    """
    print "construct_command"

    # The task to be carried out
    command = {
        "command": "INTEGRATE",
        "process_id": uuid.uuid1()
        }

    # Where to do the work
    command["directories"] = { "work": os.path.join(os.path.abspath(os.path.curdir), os.path.basename(image_0_data["fullname"]).replace(detector_module.DETECTOR_SUFFIX, "")) }
    if not os.path.exists(command["directories"]["work"]):
        os.makedirs(command["directories"]["work"])

    # Data data
    command["data"] = {
        "image_data": image_0_data,
        "run_data": run_data
        }

    command["settings"] = {
        "spacegroup": commandline_args.spacegroup,
        "start_frame": commandline_args.start_image,
        "end_frame": commandline_args.end_image,
        "x_beam": commandline_args.beamcenter[0],
        "y_beam": commandline_args.beamcenter[1],
        "xdsinp": detector_module.XDSINP
    }

    pprint.pprint(command)

    return command

def main():
    """
    The main process
    Setup logging, gather information, and run the agent
    """

    # Get the commandline args
    commandline_args = get_commandline()

    # Verbosity
    if commandline_args.verbose:
        verbosity = 5
        log_level = 10
    else:
        verbosity = 1
        log_level = 50

    # Set up logging
    logger = utils.log.get_logger(logfile_dir="./",
                                  logfile_id="rapd_integrate",
                                  level=log_level,
                                  console=commandline_args.test)

    # Set up terminal printer
    tprint = utils.log.get_terminal_printer(verbosity=log_level)

    logger.debug("Commandline arguments:")
    for pair in commandline_args._get_kwargs():
        logger.debug("  arg:%s  val:%s", pair[0], pair[1])

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()
    logger.debug("\n" + text.info + "Environmental variables" + text.stop)
    for key, val in environmental_vars.iteritems():
        logger.debug("  " + key + " : " + val)

    # List sites?
    if commandline_args.listsites:
        print "\n" + text.info + "Available sites:" + text.stop
        commandline_utils.print_sites(left_buffer="  ")
        if not commandline_args.listdetectors:
            sys.exit()

    # List detectors?
    if commandline_args.listdetectors:
        print "\n" + text.info + "Available detectors:" + text.stop
        commandline_utils.print_detectors(left_buffer="  ")
        sys.exit()

    # Look for data based on the input template
    data_files = commandline_utils.analyze_data_sources(commandline_args.template, mode="integrate")

    # Need data
    if len(data_files) == 0 and commandline_args.test == False:
        raise Exception, "No files input for indexing."

    # Get site - commandline wins over the environmental variable
    site = False
    detector = False
    detector_module = False
    if commandline_args.site:
        site = commandline_args.site
    elif environmental_vars.has_key("RAPD_SITE"):
        site = environmental_vars["RAPD_SITE"]

    if commandline_args.detector:
        detector = commandline_args.detector
        detector_module = detector_utils.load_detector(detector)

    # If no site or detector, try to figure out the detector
    if not (site or detector):
        print "Have to figure out the detector"
        detector = detector_utils.get_detector_file(data_files[0])
        detector_module = detector_utils.load_detector(detector)

    # Get the image data
    # Have a detector - read in file data
    if detector_module:
        image_0_data = get_image_data(data_files[0], detector_module)
        image_n_data = get_image_data(data_files[-1], detector_module)
    else:
        raise Exception("No detector identified")

    # Get the run data
    run_data = get_run_data(detector_module, image_0_data, image_n_data)

    # Construct the command for the agent
    command = construct_command(image_0_data,
                                run_data,
                                commandline_args,
                                detector_module,
                                logger)

    # Load the agent
    agent_module = load_module(seek_module="rapd_agent_integrate",
                               directories=["agents"],
                               logger=logger)

    # Instantiate the agent
    agent_module.DataHandler(command, logger)

if __name__ == "__main__":

    main()
