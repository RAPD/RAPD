"""
Wrapper for launching an index & strategy on images
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2016, Cornell University
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

# RAPD imports
import utils.log
from utils.modules import load_module
import utils.text as text
import commandline_utils
import detectors.detector_utils as detector_utils

def construct_command(image_headers, commandline_args, detector_module):
    """
    Put together the command for the agent
    """

    # The task to be carried out
    command = { "command":"AUTOINDEX+STRATEGY" }

    # Where to do the work
    command["directories"] = { "work": os.path.join(os.path.abspath(os.path.curdir), os.path.basename(image_headers.keys()[0]).replace(detector_module.DETECTOR_SUFFIX, "")) }
    if not os.path.exists(command["directories"]["work"]):
        os.makedirs(command["directories"]["work"])

    # Image data
    images = image_headers.keys()
    images.sort()
    counter = 0
    for image in images:
        counter += 1
        command["header%d" % counter] = image_headers[image]
    if counter == 1:
        command["header2"] = None

    # Agent settings
    command["preferences"] = {}

    # Strategy type
    command["preferences"]["strategy_type"] = commandline_args.strategy_type

    # Best
    command["preferences"]["best_complexity"] = commandline_args.best_complexity
    command["preferences"]["shape"] = "2.0"
    command["preferences"]["susceptibility"] = "1.0"
    command["preferences"]["aimed_res"] = 0.0

    # Best & Labelit
    command["preferences"]["sample_type"] = commandline_args.sample_type
    command["preferences"]["spacegroup"] = str(commandline_args.spacegroup)

    # Labelit
    command["preferences"]["a"] = 0.0
    command["preferences"]["b"] = 0.0
    command["preferences"]["c"] = 0.0
    command["preferences"]["alpha"] = 0.0
    command["preferences"]["beta"] = 0.0
    command["preferences"]["gamma"] = 0.0
    command["preferences"]["index_hi_res"] = str(commandline_args.hires)
    command["preferences"]["x_beam"] = str(commandline_args.beamcenter[0])
    command["preferences"]["y_beam"] = str(commandline_args.beamcenter[1])

    # Mosflm
    command["preferences"]["mosflm_rot"] = float(commandline_args.mosflm_range)
    command["preferences"]["mosflm_seg"] = int(commandline_args.mosflm_segments)
    command["preferences"]["mosflm_start"] = float(commandline_args.mosflm_start)
    command["preferences"]["mosflm_end"] = float(commandline_args.mosflm_start)
    command["preferences"]["reference_data"] = None
    command["preferences"]["reference_data_id"] = None
    # Change these if user wants to continue dataset with other crystal(s).
    # "reference_data_id": None, #MOSFLM
    # #"reference_data_id": 1,#MOSFLM
    # #"reference_data": [['/gpfs6/users/necat/Jon/RAPD_test/index09.mat', 0.0, 30.0, 'junk_1_1-30','P41212']],#MOSFLM
    # 'reference_data': [['/gpfs6/users/necat/Jon/RAPD_test/Output/junk/5/index12.mat',0.0,20.0,'junk','P3'],['/gpfs6/users/necat/Jon/RAPD_test/Output/junk/5/index12.mat',40.0,50.0,'junk2','P3']],#MOSFLM

    # Raddose
    command["preferences"]["crystal_size_x"] = "100"
    command["preferences"]["crystal_size_y"] = "100"
    command["preferences"]["crystal_size_z"] = "100"
    command["preferences"]["solvent_content"] = 0.55

    # Unknown
    command["preferences"]["beam_flip"] = "False"
    command["preferences"]["multiprocessing"] = "False"

    # Site parameters
    command["preferences"]["site_parameters"] = {}
    command["preferences"]["site_parameters"]["DETECTOR_DISTANCE_MAX"] = 1000
    command["preferences"]["site_parameters"]["DETECTOR_DISTANCE_MIN"] = 150
    command["preferences"]["site_parameters"]["DIFFRACTOMETER_OSC_MIN"] = 0.1
    command["preferences"]["site_parameters"]["DETECTOR_TIME_MIN"] = 0.1

    # Return address
    command["return_address"] = None

    pprint.pprint(command)
    return command


def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """Launch an index & strategy on input image(s)"""
    parser = argparse.ArgumentParser(parents=[commandline_utils.dp_parser],
                                     description=commandline_description)

    # Index only
    parser.add_argument("--index_only",
                        action="store",
                        dest="index_only",
                        help="Specify only indexing, no strategy calculation")

    # Strategy type
    parser.add_argument("--strategy_type",
                        action="store",
                        dest="strategy_type",
                        default="best",
                        # nargs=1,
                        choices=["best", "mosflm"],
                        help="Type of strategy")

    # Complexity of BEST strategy
    parser.add_argument("--best_complexity",
                        action="store",
                        dest="best_complexity",
                        # nargs=1,
                        default="none",
                        choices=["none", "min", "full"],
                        help="Complexity of BEST strategy")

    # Number of mosflm segments
    parser.add_argument("--mosflm_segments",
                        action="store",
                        dest="mosflm_segments",
                        default=1,
                        choices=[1, 2, 3, 4, 5],
                        help="Number of mosflm segments")

    # Rotation range for mosflm segments
    parser.add_argument("--mosflm_range",
                        action="store",
                        dest="mosflm_range",
                        default=0.0,
                        type=float,
                        help="Rotation range for mosflm segments")

    # Rotation range for mosflm segments
    parser.add_argument("--mosflm_start",
                        action="store",
                        dest="mosflm_start",
                        default=0.0,
                        type=float,
                        help="Start of allowable rotation range for mosflm segments")

    # Rotation range for mosflm segments
    parser.add_argument("--mosflm_end",
                        action="store",
                        dest="mosflm_end",
                        default=360.0,
                        type=float,
                        help="End of allowable rotation range for mosflm segments")


    return parser.parse_args()

def main():
    """ The main process
    Setup logging and instantiate the model"""

    # Get the commandline args
    commandline_args = get_commandline()
    # tprint(commandline_args)

    # verbosity
    if commandline_args.verbose:
        verbosity = 5
    else:
        verbosity = 1

    # Set up terminal printer
    tprint = utils.log.get_terminal_printer(verbosity=verbosity)

    # Print out commandline args
    if verbosity > 2:
        tprint("\n" + text.info + "Commandline arguments" + text.stop, 3)
        for key, val in vars(commandline_args).iteritems():
            tprint("  %s : %s" % (key, val), 3)

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()
    if verbosity > 2:
        tprint("\n" + text.info + "Environmental variables" + text.stop, 3)
        for key, val in environmental_vars.iteritems():
            tprint("  " + key + " : " + val, 3)

    # The data files to be processed
    data_files = commandline_utils.analyze_data_sources(sources=commandline_args.sources,
                                                        mode="index")
    if verbosity > 2:
        tprint("\n" + text.info + "Data files" + text.stop, 3)
        if len(data_files) == 0:
            tprint("  None", 3)
        else:
            for data_file in data_files["files"]:
                tprint("  " + data_file, 3)

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

    # Need data
    if len(data_files) == 0 and commandline_args.test == False:
        raise Exception, "No files input for indexing."

    # Too much data?
    if len(data_files) > 2:
        raise Exception, "Too many files for indexing. 1 or 2 images accepted."

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
        print data_files
        detector = detector_utils.get_detector_file(data_files["files"][0])
        print detector
        detector_module = detector_utils.load_detector(detector)

    # Have a detector - read in file data
    if detector_module:
        image_headers = {}
        for data_file in data_files["files"]:
            image_headers[data_file] = detector_module.read_header(data_file)
        pprint.pprint(image_headers)

    command = construct_command(image_headers=image_headers,
                                commandline_args=commandline_args,
                                detector_module=detector_module)



    # If no site, error
    # if site == False:
    #     print text.error+"Could not determine a site. Exiting."+text.stop
    #     sys.exit(9)

    # Determine the site_file
    # site_file = utils.site.determine_site(site_arg=site)

    # Error out if no site_file to import
    # if site_file == False:
    #     print text.error+"Could not find a site file. Exiting."+text.stop
    #     sys.exit(9)

    # Import the site settings
    # print "Importing %s" % site_file
    # SITE = importlib.import_module(site_file)

	# Single process lock?
    # utils.lock.file_lock(SITE.CONTROL_LOCK_FILE)

    # Set up logging
    if commandline_args.verbose:
        log_level = 10
    else:
        log_level = 5
    logger = utils.log.get_logger(logfile_dir="./",
                                  logfile_id="rapd_index",
                                  level=log_level)

    logger.debug("Commandline arguments:")
    for pair in commandline_args._get_kwargs():
        logger.debug("  arg:%s  val:%s" % pair)

    # Instantiate the agent
    # Load the agent from directories defined in site file
    for d in sys.path:
        if d.endswith("src"):
            toplevel_dir = d+".agents"

    agent_module = load_module(seek_module="rapd_agent_index+strategy",
                               directories=["agents"],
                               logger=logger)

    agent_module.RapdAgent(None, command, logger)

if __name__ == "__main__":

	# # Set up terminal printer
    # tprint = utils.log.get_terminal_printer(verbosity=1)

    main()
