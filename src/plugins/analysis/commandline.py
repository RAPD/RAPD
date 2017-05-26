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
import multiprocessing
import os
import sys
import uuid

# RAPD imports
import utils.log
import utils.modules as modules
import utils.text as text
import utils.commandline_utils as commandline_utils

def construct_command(commandline_args):
    """Put together the command for the plugin"""

    # The task to be carried out
    command = {
        "command": "ANALYSIS",
        "process_id": uuid.uuid1().get_hex(),
        }

    # Working directory
    work_dir = commandline_utils.check_work_dir(
        os.path.join(
            os.path.abspath(os.path.curdir),
            "rapd_analysis_%s" % ".".join(
                os.path.basename(commandline_args.datafile).split(".")[:-1])),
        active=True,
        up=commandline_args.dir_up)

    command["directories"] = {
        "work": work_dir
    }

    # Information on input
    command["input_data"] = {
        "datafile": os.path.abspath(commandline_args.datafile)
    }

    # Plugin settings
    command["preferences"] = {
        "clean": commandline_args.clean,
        "dir_up": commandline_args.dir_up,
        "nproc": commandline_args.nproc,
        "pdbquery": commandline_args.pdbquery,
        "json": commandline_args.json,
        "show_plots": commandline_args.show_plots,
        "progress": commandline_args.progress,
        "run_mode": commandline_args.run_mode,
        "sample_type": commandline_args.sample_type,
        "test": commandline_args.test,
    }

    return command

def get_commandline():
    """Grabs the commandline"""

    # print "get_commandline"

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

    # Multiprocessing
    my_parser.add_argument("--nproc",
                           dest="nproc",
                           type=int,
                           default=max(1, multiprocessing.cpu_count() - 1),
                           help="Number of processors to employ")

    # Verbose
    # my_parser.add_argument("-v", "--verbose",
    #                        action="store_true",
    #                        dest="verbose",
    #                        help="More output")

    # Quiet
    my_parser.add_argument("-q", "--quiet",
                           action="store_false",
                           dest="verbose",
                           help="Reduce output")

    # Messy
    # my_parser.add_argument("--messy",
    #                        action="store_false",
    #                        dest="clean",
    #                        help="Keep intermediate files")

    # Clean
    my_parser.add_argument("--clean",
                           action="store_true",
                           dest="clean",
                           help="Remove intermediate files")

    # Color
    # my_parser.add_argument("--color",
    #                        action="store_false",
    #                        dest="no_color",
    #                        help="Color the terminal output")

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

    # Hide plots?
    my_parser.add_argument("--noplot",
                           action="store_false",
                           dest="show_plots",
                           help="No plotting")

    # Output progress updates?
    my_parser.add_argument("--progress",
                           action="store_true",
                           dest="progress",
                           help="Output progress updates to the terminal")

    # Positional argument
    my_parser.add_argument(action="store",
                           dest="datafile",
                           nargs="?",
                           default=False,
                           help="Name of file to be analyzed")

    # Sample type
    my_parser.add_argument("--sample_type",
                           action="store",
                           dest="sample_type",
                           # nargs=1,
                           default="default",
                           choices=["default", "protein", "ribosome"],
                           help="Type of sample")

    # Verbose
    my_parser.add_argument("--pdbquery",
                           action="store_true",
                           dest="pdbquery",
                           help="Run pdbquery as part of analysis")

    # Quiet
    # my_parser.add_argument("--nopdbquery",
    #                        action="store_false",
    #                        dest="pdbquery",
    #                        help="Don't run pdbquery as part of analysis")

    # Print help message if no arguments
    if len(sys.argv[1:]) == 0:
        my_parser.print_help()
        my_parser.exit()

    args = my_parser.parse_args()

    # Insert logic to check or modify args here
    # Running in interactive mode if this code is being called
    if args.json:
        args.run_mode = "json"
    else:
        args.run_mode = "interactive"

    return args

def print_welcome_message(printer):
    """Print a welcome message to the terminal"""
    message = """
-------------
RAPD Analysis
-------------"""
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
                                      logfile_id="rapd_analysis",
                                      level=log_level,
                                      console=commandline_args.test)

    # Set up terminal printer
    # JSON only
    if commandline_args.json:
        terminal_log_level = 100
    # Verbosity
    elif commandline_args.verbose:
        terminal_log_level = 10
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
        tprint(arg="  arg:%-20s  val:%s" % (pair[0], pair[1]), level=10, color="white")

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()
    logger.debug("" + text.info + "Environmental variables" + text.stop)
    tprint("\nEnvironmental variables", level=10, color="blue")
    for key, val in environmental_vars.iteritems():
        logger.debug("  " + key + " : " + val)
        tprint(arg="  arg:%-20s  val:%s" % (key, val), level=10, color="white")

    # Should working directory go up or down?
    if environmental_vars.get("RAPD_DIR_INCREMENT") == "up":
        commandline_args.dir_up = True
    else:
        commandline_args.dir_up = False

    command = construct_command(commandline_args=commandline_args)

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
