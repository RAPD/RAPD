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
import importlib
import os
# from pprint import pprint
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

def get_image_data(data_file, detector_module, site_module):
    """
    Get the image data and return given a filename
    """

    # print "get_image_data", data_file

    if site_module:
        header = detector_module.read_header(data_file, site_module.BEAM_SETTINGS)
    else:
        header = detector_module.read_header(data_file)

    return header

def get_run_data(detector_module, image_0_data, image_n_data, commandline_args):
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

    # print "get_run_data"
    # pprint(image_0_data)
    # pprint(image_n_data)

    run_data = {
        "directory": image_0_data.get("directory"),
        "distance": image_0_data.get("distance"),
        "image_prefix": image_0_data.get("image_prefix"),
        "image_template": detector_module.create_image_template(
            image_0_data.get("image_prefix"),
            image_0_data.get("run_number")),
        "run_number": image_0_data.get("run_number"),
        "time": image_0_data.get("time"),
        }

    # Set starting image
    if commandline_args.start_image:
        run_data["start"] = commandline_args.start_image
    else:
        run_data["start"] = image_0_data.get("image_number")

    # Set end image and total number of images
    if commandline_args.end_image:
        run_data["end"] = commandline_args.end_image
        run_data["total"] = commandline_args.end_image - run_data["start"] + 1

    else:
        run_data["end"] = image_n_data.get("image_number")
        run_data["total"] = image_n_data.get("image_number") - run_data["start"] + 1

    # The repr for the run
    run_data["repr"] = detector_module.create_image_template(image_0_data.get("image_prefix"), image_0_data.get("run_number")).rstrip(detector_module.DETECTOR_SUFFIX).replace("?", "") + ("%d-%d" % (run_data.get("start"), run_data.get("end")))

    return run_data

def construct_command(image_0_data, run_data, commandline_args, detector_module):
    """
    Put together the command for the plugin
    """

    # The task to be carried out
    command = {
        "command": "XDS", #"INTEGRATE",
        "process_id": uuid.uuid1().get_hex()
        }

    # Where to do the work
    command["directories"] = {
        "work": os.path.join(
            os.path.abspath(os.path.curdir),
            "rapd_integrate_" + run_data["repr"])
        }
    if not os.path.exists(command["directories"]["work"]):
        os.makedirs(command["directories"]["work"])

    # Data data
    command["data"] = {
        "image_data": image_0_data,
        "run_data": run_data
        }

    command["preferences"] = {
        "start_frame": commandline_args.start_image,
        "end_frame": commandline_args.end_image,
        "flip_beam": detector_module.XDS_FLIP_BEAM,
        "x_beam": commandline_args.beamcenter[0],
        "y_beam": commandline_args.beamcenter[1],
        "spacegroup": commandline_args.spacegroup,
        "low_res": commandline_args.lowres,
        "hi_res": commandline_args.hires,
        "json_output": commandline_args.json,
        "show_plots": commandline_args.plotting,
        "xdsinp": detector_module.XDSINP,
    }

    if commandline_args.beamcenter[0]:
        command["preferences"]["beam_center_override"] = True

    return command

def print_welcome_message(printer):
    """Print a welcome message to the terminal"""

    message = """
---------------
RAPD Intgration
---------------"""
    printer(message, 50, color="blue")


def main():
    """
    The main process
    Setup logging, gather information, and run the plugin
    """

    # Get the commandline args
    commandline_args = get_commandline()

    # Output log file is always verbose
    log_level = 10

    # Set up logging
    logger = utils.log.get_logger(logfile_dir="./",
                                  logfile_id="rapd_integrate",
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

    # Print out commandline arguments
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

    # List sites?
    if commandline_args.listsites:
        tprint(arg="\nAvailable sites", level=99, color="blue")
        commandline_utils.print_sites(left_buffer="  ")
        if not commandline_args.listdetectors:
            sys.exit()

    # List detectors?
    if commandline_args.listdetectors:
        print "\n" + text.info + "Available detectors:" + text.stop
        commandline_utils.print_detectors(left_buffer="  ")
        sys.exit()

    # Look for data based on the input template
    data_files = commandline_utils.analyze_data_sources(
        commandline_args.template,
        mode="integrate",
        start_image=commandline_args.start_image,
        end_image=commandline_args.end_image)

    if "hdf5_files" in data_files:
        logger.debug("HDF5 source file(s)")
        tprint(arg="\nHDF5 source file(s)", level=99, color="blue")
        logger.debug(data_files["hdf5_files"])
        for data_file in data_files["hdf5_files"]:
            tprint(arg="  " + data_file, level=99, color="white")
        logger.debug("CBF file(s) from HDF5 file(s)")
        tprint(arg="\nData files", level=99, color="blue")
    else:
        logger.debug("Data to be integrated")
        tprint(arg="\nData to be integrated", level=99, color="blue")
        tprint(arg="  From %s" % data_files["data_files"][0], level=99, color="white")
        tprint(arg="    To %s" % data_files["data_files"][-1], level=99, color="white")

    # Need data
    if len(data_files) == 0 and commandline_args.test == False:
        raise Exception("No files input for integration.")

    # Get site - commandline wins over the environmental variable
    site = False
    site_module = False
    detector = {}
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
        detector = detector_utils.get_detector_file(data_files["data_files"][0])
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
    if not detector_module:
        raise Exception("No detector identified")

    # Get header information
    image_0_data = get_image_data(data_file=data_files["data_files"][0],
                                  detector_module=detector_module,
                                  site_module=site_module)
    image_n_data = get_image_data(data_file=data_files["data_files"][-1],
                                  detector_module=detector_module,
                                  site_module=site_module)

    logger.debug("Image header: %s, %s", image_0_data, image_n_data)
    tprint(arg="\nImage headers", level=10, color="blue")
    count = 0
    for header in (image_0_data, image_n_data):
        keys = header.keys()
        keys.sort()
        if count > 0:
            tprint(arg="", level=10, color="white")
        tprint(arg="  %s" % header["fullname"], level=10, color="white")
        for key in keys:
            tprint(arg="    arg:%-22s  val:%s" % (key, header[key]), level=10, color="white")
        count += 1

    # Get the run data
    run_data = get_run_data(detector_module, image_0_data, image_n_data, commandline_args)

    logger.debug("Run data: %s", run_data)
    tprint(arg="\nRun data", level=10, color="blue")
    keys = run_data.keys()
    keys.sort()
    for key in keys:
        tprint(arg="    arg:%-22s  val:%s" % (key, run_data[key]), level=10, color="white")

    # Construct the command for the plugin
    command = construct_command(image_0_data,
                                run_data,
                                commandline_args,
                                detector_module)

    # Load the plugin
    plugin = load_module(seek_module="plugin",
                         directories=["plugins.integrate"],
                         logger=logger)

    tprint(arg="\nPlugin information", level=10, color="blue")
    tprint(arg="  Plugin type:    %s" % plugin.PLUGIN_TYPE, level=10, color="white")
    tprint(arg="  Plugin subtype: %s" % plugin.PLUGIN_SUBTYPE, level=10, color="white")
    tprint(arg="  Plugin version: %s" % plugin.VERSION, level=10, color="white")
    tprint(arg="  Plugin id:      %s" % plugin.ID, level=10, color="white")

    # Instantiate the plugin
    plugin.RapdPlugin(site=None,
                     command=command,
                     tprint=tprint,
                     logger=logger)

if __name__ == "__main__":

    main()
