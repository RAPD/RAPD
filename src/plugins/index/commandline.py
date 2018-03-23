"""
Wrapper for launching an index & strategy on images
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2016-2018 Cornell University
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
import importlib
import os
from pprint import pprint
import sys
import uuid

# RAPD imports
import utils.log
from utils.modules import load_module
from utils.r_numbers import try_float, try_int
import utils.text as text
import utils.commandline_utils as commandline_utils
import detectors.detector_utils as detector_utils

def construct_command(image_headers, commandline_args, detector_module):
    """
    Put together the command for the plugin
    """

    # The task to be carried out
    command = {
        "command": "INDEX",
        "process": {
            "process_id": uuid.uuid1().get_hex(),
            "parent_id": None,
            "source": "commandline",
            "status": 0
            }
        }

    # Working directory
    image_numbers = []
    image_template = ""
    h5 = ""
    for _, header in image_headers.iteritems():
        image_numbers.append(str(header["image_number"]))
        image_template = header["image_template"]
        if "hdf5_source" in header:
            if h5:
                h5 += "_"
            h5 += os.path.basename(header["hdf5_source"]).replace("_master.h5", "")
    image_numbers.sort()

    if h5:
        run_repr = "rapd_index_" + h5
    else:
        run_repr = "rapd_index_" + image_template.replace(detector_module.DETECTOR_SUFFIX, "").\
                   replace("?", "")
        run_repr += "+".join(image_numbers)

    work_dir = commandline_utils.check_work_dir(
        os.path.join(os.path.abspath(os.path.curdir), run_repr),
        active=True,
        up=commandline_args.dir_up)

    command["directories"] = {
        "work": work_dir
        }

    # Image data
    images = image_headers.keys()
    images.sort()
    counter = 0
    for image in images:
        counter += 1
        command["image%d" % counter] = image_headers[image]
    if counter == 1:
        command["image2"] = None

    # Plugin settings
    command["preferences"] = {}

    # JSON output?
    command["preferences"]["json"] = commandline_args.json
    command["preferences"]["json_fd"] = commandline_args.json_fd
    command["preferences"]["progress"] = commandline_args.progress
    command["preferences"]["no_color"] = commandline_args.no_color

    # Show plots
    command["preferences"]["show_plots"] = commandline_args.show_plots

    # Strategy type
    command["preferences"]["strategy_type"] = commandline_args.strategy_type

    # Best
    command["preferences"]["best_complexity"] = commandline_args.best_complexity
    command["preferences"]["shape"] = 2.0
    command["preferences"]["susceptibility"] = 1.0
    command["preferences"]["aimed_res"] = 0.0

    # Best & Labelit
    command["preferences"]["sample_type"] = commandline_args.sample_type
    command["preferences"]["spacegroup"] = commandline_args.spacegroup
    command["preferences"]["unitcell"] = commandline_args.unitcell

    # Labelit
    command["preferences"]["index_hi_res"] = try_float(commandline_args.hires, 0.0)
    command["preferences"]["x_beam"] = commandline_args.beamcenter[0]
    command["preferences"]["y_beam"] = commandline_args.beamcenter[1]
    command["preferences"]["beam_search"] = commandline_args.beam_search

    # Mosflm
    command["preferences"]["mosflm_rot"] = float(commandline_args.mosflm_range)
    command["preferences"]["mosflm_seg"] = int(commandline_args.mosflm_segments)
    command["preferences"]["mosflm_start"] = float(commandline_args.mosflm_start)
    command["preferences"]["mosflm_end"] = float(commandline_args.mosflm_end)
    command["preferences"]["reference_data"] = None
    command["preferences"]["reference_data_id"] = None
    # Change these if user wants to continue dataset with other crystal(s).
    # "reference_data_id": None, #MOSFLM
    # #"reference_data_id": 1,#MOSFLM
    # #"reference_data": [['/gpfs6/users/necat/Jon/RAPD_test/index09.mat', 0.0, 30.0, 'junk_1_1-30',
    #                      'P41212']],#MOSFLM
    # 'reference_data': [['/gpfs6/users/necat/Jon/RAPD_test/Output/junk/5/index12.mat',
    #                     0.0,
    #                     20.0,
    #                     'junk',
    #                     'P3'],
    #                    ['/gpfs6/users/necat/Jon/RAPD_test/Output/junk/5/index12.mat',
    #                     40.0,
    #                     50.0,
    #                     'junk2',
    #                     'P3']
    #                   ],#MOSFLM

    # Raddose
    command["preferences"]["crystal_size_x"] = 100.0
    command["preferences"]["crystal_size_y"] = 100.0
    command["preferences"]["crystal_size_z"] = 100.0
    command["preferences"]["solvent_content"] = commandline_args.solvent
    #command["preferences"][]

    # Unknown
    command["preferences"]["beam_flip"] = False
    #command["preferences"]["multiprocessing"] = False

    # Launches jobs at same time using more cores. Much Faster!!
    #command["preferences"]["multiprocessing"] = True
    command["preferences"]["nproc"] = commandline_args.nproc

    # The run mode for rapd
    command["preferences"]["run_mode"] = commandline_args.run_mode

    # Site parameters
    command["preferences"]["site_parameters"] = {}
    command["preferences"]["site_parameters"]["DETECTOR_DISTANCE_MAX"] = \
        commandline_args.site_det_dist_max
    command["preferences"]["site_parameters"]["DETECTOR_DISTANCE_MIN"] = \
        commandline_args.site_det_dist_min
    command["preferences"]["site_parameters"]["DIFFRACTOMETER_OSC_MIN"] = \
        commandline_args.site_osc_min
    command["preferences"]["site_parameters"]["DETECTOR_TIME_MIN"] = \
        commandline_args.site_det_time_min

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

    # Number of mosflm segments
    parser.add_argument("--beam_search",
                        action="store",
                        dest="beam_search",
                        default=0.2,
                        type=float,
                        help="Beam search scope")

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
                        type=int,
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

    # Site parameters
    parser.add_argument("--site_detector_max_dist",
                        action="store",
                        dest="site_det_dist_max",
                        default=1000.0,
                        type=float,
                        help="Maximum detector distance in mm")

    parser.add_argument("--site_detector_min_dist",
                        action="store",
                        dest="site_det_dist_min",
                        default=150.0,
                        type=float,
                        help="Minimum detector distance in mm")

    parser.add_argument("--site_oscillation_min",
                        action="store",
                        dest="site_osc_min",
                        default=0.2,
                        type=float,
                        help="Minimum oscillation width in degrees")

    parser.add_argument("--site_detector_min_time",
                        action="store",
                        dest="site_det_time_min",
                        default=0.2,
                        type=float,
                        help="Minimum detector time in seconds")

    # Directory or files
    parser.add_argument(action="store",
                        dest="sources",
                        nargs="*",
                        help="Directory or files")

    # No args? print help
    if len(sys.argv[1:]) == 0:
        parser.print_help()
        parser.exit()

    args = parser.parse_args()

    # Insert logic to check or modify args here

    # Running in interactive mode if this code is being called
    if args.json:
        args.run_mode = "json"
    else:
        args.run_mode = "interactive"

    # Regularize spacegroup
    if args.spacegroup:
        args.spacegroup = commandline_utils.regularize_spacegroup(args.spacegroup)

    # mosflm segments
    if args.mosflm_segments < 1 or args.mosflm_segments > 5:
        raise Exception("mosflm_segments must have a value between 1 and 5")

    if args.mosflm_start >= args.mosflm_end:
        raise Exception("mosflm_end must be greater than mosflm_start")

    if args.mosflm_segments > 1 and args.mosflm_range == 0.0:
        raise Exception("mosflm_range must be set to > 0 if mosflm_segments > 1")

    return args

def print_welcome_message(printer):
    """Print a welcome message to the terminal"""

    message = """
---------------------
RAPD Index & Strategy
---------------------"""
    printer(message, 98, color="blue")

def print_headers(tprint, image_headers):
    """Convenience function"""

    tprint(arg="\nImage headers", level=20, color="blue")
    count = 0
    for fullname, header in image_headers.iteritems():
        keys = header.keys()
        keys.sort()
        if count > 0:
            tprint(arg="", level=20, color="white")
        tprint(arg="  %s" % fullname, level=20, color="white")
        for key in keys:
            tprint(arg="    arg:%-22s  val:%s" % (key, header[key]), level=20, color="white")
        count += 1

def main():
    """ The main process
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
        terminal_log_level = 30

    tprint = utils.log.get_terminal_printer(verbosity=terminal_log_level,
                                            no_color=commandline_args.no_color,
                                            progress=commandline_args.progress,
                                            progress_fd=commandline_args.progress_fd)

    print_welcome_message(tprint)

    logger.debug("Commandline arguments:")
    tprint(arg="\nCommandline arguments:", level=10, color="blue")
    for pair in commandline_args._get_kwargs():
        logger.debug("  arg:%s  val:%s", pair[0], pair[1])
        tprint(arg="  arg:%-20s  val:%s" % (pair[0], pair[1]), level=10, color="white")

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()
    logger.debug("\n" + text.info + "Environmental variables" + text.stop)
    tprint("\nEnvironmental variables", level=10, color="blue")
    for key, val in environmental_vars.iteritems():
        logger.debug("  " + key + " : " + val)
        tprint(arg="  arg:%-20s  val:%s" % (key, val), level=10, color="white")

    # Should working directory go up or down?
    if environmental_vars.get("RAPD_DIR_INCREMENT") in ("up", "UP"):
        commandline_args.dir_up = True
    else:
        commandline_args.dir_up = False

    # List sites?
    if commandline_args.listsites:
        tprint(arg="\nAvailable sites", level=98, color="blue")
        commandline_utils.print_sites(left_buffer="  ")
        if not commandline_args.listdetectors:
            sys.exit()

    # List detectors?
    if commandline_args.listdetectors:
        tprint(arg="Available detectors", level=98, color="blue")
        commandline_utils.print_detectors(left_buffer="  ")
        sys.exit()

    # Get the data files
    data_files = commandline_utils.analyze_data_sources(sources=commandline_args.sources,
                                                        mode="index")
    if "hdf5_files" in data_files:
        logger.debug("HDF5 source file(s)")
        tprint(arg="\nHDF5 source file(s)", level=98, color="blue")
        logger.debug(data_files["hdf5_files"])
        for data_file in data_files["hdf5_files"]:
            tprint(arg="  " + data_file, level=98, color="white")
        logger.debug("CBF file(s) from HDF5 file(s)")
        tprint(arg="\nData files", level=98, color="blue")
    else:
        logger.debug("Data file(s)")
        tprint(arg="\nData file(s)", level=98, color="blue")

    if len(data_files) == 0:
        tprint(arg="  None", level=98, color="white")
    else:
        logger.debug(data_files["files"])
        for data_file in data_files["files"]:
            tprint(arg="  " + data_file, level=98, color="white")

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
    #detector = {}
    detector = False
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
    # if not (site or detector):
    """
    if site or detector == False:
        detector = detector_utils.get_detector_file(data_files["files"][0])
        if isinstance(detector, dict):
            if detector.has_key("site"):
                site_target = detector.get("site")
                site_file = utils.site.determine_site(site_arg=site_target)
                site_module = importlib.import_module(site_file)
                detector_target = site_module.DETECTOR.lower()
                detector_module = detector_utils.load_detector(detector_target)
            elif detector.has_key("detector"):
                site_module = False
                detector_target = detector.get("detector")
                detector_module = detector_utils.load_detector(detector_target)
    """
    if not detector:
        detector = detector_utils.get_detector_file(data_files["files"][0])
        if isinstance(detector, dict):
            if detector.has_key("site"):
                site_target = detector.get("site")
                site_file = utils.site.determine_site(site_arg=site_target)
                site_module = importlib.import_module(site_file)
                detector_target = site_module.DETECTOR.lower()
                detector_module = detector_utils.load_detector(detector_target)
            elif detector.has_key("detector"):
                site_module = False
                detector_target = detector.get("detector")
                detector_module = detector_utils.load_detector(detector_target)

    # If someone specifies the site or found in env.
    if site and not site_module:
        site_file = utils.site.determine_site(site_arg=site)
        site_module = importlib.import_module(site_file)

    # Have a detector - read in file data
    if detector_module:
        image_headers = {}
        for index, data_file in enumerate(data_files["files"]):
            if site_module:
                image_headers[data_file] = detector_module.read_header(data_file,
                                                                       #site_module.BEAM_SETTINGS)
                                                                       site_module.BEAM_INFO.get(site.upper(), {}))
            else:
                image_headers[data_file] = detector_module.read_header(data_file)
            # If this image is derived from an hdf5 master file, tag it
            if "hdf5_files" in data_files:
                image_headers[data_file]["hdf5_source"] = data_files["hdf5_files"][index]

        logger.debug("Image headers: %s", image_headers)
        # print_headers(tprint, image_headers)

        command = construct_command(image_headers=image_headers,
                                    commandline_args=commandline_args,
                                    detector_module=detector_module)
    else:
        if logger:
            logger.exception("No detector module found")
        raise Exception("No detector module found")

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
    # site_module = importlib.import_module(site_file)

	# Single process lock?
    # utils.lock.file_lock(site_module.CONTROL_LOCK_FILE)

    # Instantiate the plugin
    # Load the plugin from directories defined in site file

    # for d in sys.path:
    #     if d.endswith("src"):
    #         toplevel_dir = d+".plugins"

    plugin = load_module(seek_module="plugin",
                         directories=["plugins.index"],
                         logger=logger)

    tprint(arg="\nPlugin information", level=10, color="blue")
    tprint(arg="  Plugin type:    %s" % plugin.PLUGIN_TYPE, level=10, color="white")
    tprint(arg="  Plugin subtype: %s" % plugin.PLUGIN_SUBTYPE, level=10, color="white")
    tprint(arg="  Plugin version: %s" % plugin.VERSION, level=10, color="white")
    tprint(arg="  Plugin id:      %s" % plugin.ID, level=10, color="white")

    #plugin_instance = plugin.RapdPlugin(None, command, tprint, logger)
    plugin_instance = plugin.RapdPlugin(site_module, command, tprint, logger)
    plugin_instance.start()

if __name__ == "__main__":

	# # Set up terminal printer
    # tprint = utils.log.get_terminal_printer(verbosity=1)

    main()
