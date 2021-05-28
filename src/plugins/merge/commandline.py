"""Wrapper for launching HCMerge"""

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

__created__ = "2012-08-09"
__maintainer__ = "Kay Perry"
__email__ = "kperry@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
import multiprocessing
import os
import sys
import uuid

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils
import utils.credits as credits
#import utils.globals as rglobals
import utils.log
import utils.modules as modules
import utils.text as text
import utils.commandline_utils as commandline_utils
import detectors.detector_utils as detector_utils

# Plugin-specific imports
from cctbx.sgtbx import space_group_symbols


def construct_command(commandline_args, logger):
    """
    Put together the command for the plugin

    commandline_args needs to look like:

    class commandline_args(object):
        clean = True | False
        datafile = ""
        json = True | False
        method = "single" | "complete" | "average" | "weighted" | "centroid" | "median" | "ward"
        no_color = True | False
        nproc = int
        progress = True | False
        run_mode = "interactive" | "json" | "server" | "subprocess"
        test = True | False
        verbose = True | False
    """

    # The task to be carried out
    command = {
        "command": "HCMERGE",
        "process_id": uuid.uuid1().get_hex(),
        "status": 0,
    }

    work_dir = commandline_utils.check_work_dir(
        os.path.join(
            os.path.abspath(os.path.curdir),
            "hcmerge"),
        active=True,
        up=commandline_args.dir_up)

    # Work directory
    command["directories"] = {
        "work": work_dir
    }

    # Information on input
    command["input_data"] = {
        "datasets": commandline_args.datasets
    }

    # Plugin settings
    command["preferences"] = {
        "json": commandline_args.json,
        "nproc": commandline_args.nproc,
        "run_mode": commandline_args.run_mode,
        "method": commandline_args.method,
        "test": commandline_args.test,
    }
    for setting in commandline_args._get_kwargs():
        command['preferences'][setting[0]] = setting[1]

    logger.debug("Command for hcmerge plugin: %s", command)

    return command


def get_commandline():
    """Grabs the commandline"""

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Launch HCMerge plugin with filelist or pickle file"
    parser = argparse.ArgumentParser(description=commandline_description)
    parser.add_argument("-a", "--all",
                        action="store_true",
                        dest="all_clusters",
                        default=False,
                        help="make all agglomerative clusters greater than cutoff value")
    parser.add_argument("-c", "--cutoff",
                        dest="cutoff",
                        type=float,
                        default=0.95,
                        help="set a percentage cutoff for the similarity between datasets")
    parser.add_argument("-d", "--dpi",
                        dest="dpi",
                        type=int,
                        default=100,
                        help="set resolution in dpi for the dendrogram image")
    parser.add_argument("-l", "--labels",
                        action="store_true",
                        dest="labels",
                        default=False,
                        help="add file names and labels to the dendrogram")
    parser.add_argument("-m", "--method",
                        dest="method",
                        default="complete",
                        help="set alternative clustering method: single, complete (default), average, weighted, centroid, median, or ward")
    parser.add_argument("-i", "--metric",
                        dest="metric",
                        default="intensity",
                        help="set metric for determineing isomorphism: intensity, unitcell, default=intensity")
    # Number of processors to use
    parser.add_argument("--nproc",
                        action="store",
                        dest="nproc",
                        type=int,
                        default=multiprocessing.cpu_count(),
                        help="Number of processors to use. Defaults to the number of \
                             processors available")
    parser.add_argument("-o", "--output_prefix",
                        dest="prefix",
                        default="merged",
                        help="set a prefix for output files. Used in rerun as the name of the .pkl file")
    # Precheck Files for Spacegroup and is XDS_ASCII.HKL
    parser.add_argument("-p", "--precheck",
                        action="store_true",  # Automatic default of True
                        dest="precheck",
                        help="precheck for duplicate or incorrect data files, default=True")

    # Resolution
    parser.add_argument("-r", "--resolution",
                        dest="resolution",
                        type=float,
                        default=0,
                        help="set a resolution cutoff for merging data")

    # Spacegroup
    parser.add_argument("-sg", "--sg", "--spacegroup",
                        action="store",
                        dest="spacegroup",
                        default=False,
                        help="Input a spacegroup")

    # Unit cell
    parser.add_argument("-u", "--unit", "--unitcell",
                        action="store",
                        dest="unitcell",
                        default=False,
                        nargs=6,
                        type=float,
                        help="input a unit cell a b c alpha beta gamma")

    # Allow starting at a later point in the process
    parser.add_argument("--rerun",
                        dest="start_point",
                        default="start",
                        help="use pickle file and run merging again starting at: clustering, dendrogram")

    # Allow running in either no restriction (sloppy) or restricted (strict) mode.  Default is sloppy.
    parser.add_argument("--strict",
                        action="store_true",
                        dest="strict",
                        help="Have clustering run with strict parameters. Setting spacegroup or unitcell \
                        automatically forces strict mode.")

    # Allow for merging everything no matter what.  Default is force = False.
    parser.add_argument("-f", "--force",
                        dest="force",
                        action="store_true",
                        help="Force everything to be merged even if not isomorphous.")
    # Run in test mode
    parser.add_argument("-t", "--test",
                        action="store_true",
                        dest="test",
                        help="Run in test mode")

    # Verbose/Quiet are a pair of opposites
    # Recommend defaulting to verbose during development and to
    # quiet during production
    # Verbose
    # parser.add_argument("-v", "--verbose",
    #                       action="store_true",
    #                       dest="verbose",
    #                       help="More output")

    # Quiet
    parser.add_argument("-q", "--quiet",
                        action="store_false",
                        dest="verbose",
                        help="More output")

    # Messy/Clean are a pair of opposites.
    # Recommend defaulting to messy during development and to
    # clean during production
    # Messy
    parser.add_argument("--messy",
                        action="store_false",
                        dest="clean",
                        help="Keep intermediate files")

    # Clean
    parser.add_argument("--clean",
                        action="store_true",
                        default=True,
                        dest="clean",
                        help="Clean up intermediate files")

    # JSON Output
    parser.add_argument("-j", "--json",
                        dest="json",
                        action="store_true",
                        default=False,
                        help="Output JSON format string")

    parser.add_argument("--run_mode",
                        dest="run_mode",
                        default='interactive',
                        help="Specifically set the run mode: interactive, server, subprocess"
                        )

    # Positional argument
    parser.add_argument(action="store",
                        dest="datasets",
                        nargs="*",
                        help="Either a space-separated list of datasets, a file containing a list of datasets, or a pkl file")

    # Print help message if no arguments
    if len(sys.argv[1:]) == 0:
        parser.print_help()
        parser.exit()

    args = parser.parse_args()

    # Insert logic to check or modify args here
    if len(args.datasets) > 1:
        # Get absolute path in case people have relative paths
        args.datasets = [os.path.abspath(x) for x in args.datasets]
    elif len(args.datasets) == 0:
        # print 'MergeMany requires a text file with a list of files (one per line) or a list of files on the command line'
        parser.print_help()
        sys.exit(9)
    elif args.datasets[0].split('.')[1].lower() == 'pkl':
        args.datasets = args.datasets[0]
    else:
        # Read in text file with each file on a separate line
        args.datasets = open(args.datasets[0], 'rb').readlines()
        # Remove entries created from the blank lines in the file.  Compensating for returns at end of file.
        args.datasets = filter(lambda x: x != '\n', args.datasets)
        # Remove empty space on either side of the filenames
        args.datasets = [os.path.abspath(x.strip()) for x in args.datasets]

    # Regularize spacegroup
    # Check to see if the user has set a spacegroup.  If so, then change from symbol to IUCR number.
    if args.spacegroup:
        args.spacegroup = space_group_symbols(args.spacegroup).number()
        args.strict = True
    else:
        # If user has not set a spacegroup, then default to 0.
        args.spacegroup = 0

    # Unit Cell Check to set strict mode
    if args.unitcell:
        args.strict = True

    # Deal with negative integers and what happens if cpu_count() raises NotImplementedError
    if args.nproc <= 0:
        try:
            args.nproc = cpu_count()
        except:
            args.nproc = 1

    # Set the clustering method
    try:
        method_list = ['single', 'complete', 'average', 'weighted', 'centroid', 'median', 'ward']
        if [i for i in method_list if i in args.method]:
            args.method = args.method
    except:
        print 'Unrecognized method.'
        sys.exit()

    try:
        metric_list = ['intensity', 'unitcell']
        if [i for i in metric_list if i in args.metric]:
            if args.metric == 'intensity':
                args.metric = 'I' 
            if args.metric == 'unitcell':
                args.metric = 'UC'

    except:
        print("Unrecognized metric. Choose 'intensity' or 'unitcell'.")
        sys.exit()

    try:
        rerun_list = ['start', 'clustering', 'dendrogram']
        if [i for i in rerun_list if i in args.start_point]:
            args.start_point = args.start_point
    except:
        print 'Unrecognized option for rerunning HCMerge.'
        sys.exit()

    try:
        run_mode_list = ['interactive', 'server', 'subprocess']
        if [i for i in run_mode_list if i in args.run_mode]:
            args.run_mode = args.run_mode
    except:
        print 'Unrecognized run mode.'
        sys.exit()

    return args


def print_welcome_message(printer):
    """Print a welcome message to the terminal"""
    message = """
------------
RAPD Merging
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
                                  logfile_id="rapd_hcmerge",
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

    tprint = utils.log.get_terminal_printer(verbosity=terminal_log_level)

    print_welcome_message(tprint)

    logger.debug("Commandline arguments:")
    tprint(arg="\nCommandline arguments:", level=10, color="blue")
    for pair in commandline_args._get_kwargs():
        logger.debug("  arg:%s  val:%s", pair[0], pair[1])
        tprint(arg="  arg:%-20s  val:%s" %
               (pair[0], pair[1]), level=10,             color="default")

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()

    # Set working directory to go up or hcmerge rerun will break
    environmental_vars['RAPD_DIR_INCREMENT'] = "UP"

    logger.debug("" + text.info + "Environmental variables" + text.stop)
    tprint("\nEnvironmental variables", level=10, color="blue")
    for key, val in environmental_vars.iteritems():
        logger.debug("  " + key + " : " + val)
        tprint(arg="  arg:%-20s  val:%s" %
               (key, val), level=10, color="default")

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
                                 directories=["plugins.merge"],
                                 logger=logger)

    # Print plugin info
    tprint(arg="\nPlugin information", level=10, color="blue")
    tprint(arg="  Plugin type:    %s" %
           plugin.PLUGIN_TYPE, level=10,             color="default")
    tprint(arg="  Plugin subtype: %s" %
           plugin.PLUGIN_SUBTYPE, level=10,             color="default")
    tprint(arg="  Plugin version: %s" %
           plugin.VERSION, level=10, color="default")
    tprint(arg="  Plugin id:      %s" % plugin.ID, level=10, color="default")

    site = False
    # Run the plugin
    plugin.RapdPlugin(site, command, tprint, logger)


if __name__ == "__main__":

    # Execute code
    main()
