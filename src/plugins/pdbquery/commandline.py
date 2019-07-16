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
    """
    Put together the command for the plugin

    commandline_args needs to look like:

    class commandline_args(object):
        clean = True | False
        contaminants = True | False
        data_file = ""
        json = True | False
        no_color = True | False
        nproc = int
        pdbs = False | ["pdbid", ...]
        progress = True | False
        run_mode = "interactive" | "json" | "server" | "subprocess"
        search = True | False
        test = True | False
        verbose = True | False
    """

    # The task to be carried out
    command = {
        "command": "PDBQUERY",
        "process_id": uuid.uuid1().get_hex(),
        "status": 0,
        }

    # Work directory
    work_dir = commandline_utils.check_work_dir(
        os.path.join(
            os.path.abspath(os.path.curdir),
            "rapd_pdbquery_%s" %  ".".join(
                os.path.basename(commandline_args.data_file).split(".")[:-1])),
        active=True,
        up=commandline_args.dir_up)

    command["directories"] = {
        "work": work_dir,
        "exchange_dir": commandline_args.exchange_dir
        }

    # Information on input
    command["input_data"] = {
        "data_file": os.path.abspath(commandline_args.data_file),
        "pdbs": commandline_args.pdbs,
        "db_settings": commandline_args.db_settings
    }

    # Plugin settings
    command["preferences"] = {
        "clean": commandline_args.clean,
        "json": commandline_args.json,
        "contaminants": commandline_args.contaminants,
        "nproc": commandline_args.nproc,
        "progress": commandline_args.progress,
        "run_mode": commandline_args.run_mode,
        "search": commandline_args.search,
        "test": commandline_args.test,
        #"computer_cluster": commandline_args.computer_cluster,
        #"results_queue": commandline_args.results_queue,
    }

    return command

def get_commandline():
    """Grabs the commandline"""

    # Parse the commandline arguments
    commandline_description = "Launch pdbquery plugin"
    my_parser = argparse.ArgumentParser(description=commandline_description)

    # Run in test mode
    my_parser.add_argument("-t", "--test",
                           action="store_true",
                           dest="test",
                           help="Run in test mode")

    # Verbose
    # my_parser.add_argument("-v", "--verbose",
    #                        action="store_true",
    #                        dest="verbose",
    #                        help="More output")

    # Quiet
    my_parser.add_argument("-q", "--quiet",
                           action="store_false",
                           dest="verbose",
                           help="Run with less output")

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

    # Output progress updates?
    my_parser.add_argument("--progress",
                           action="store_true",
                           dest="progress",
                           help="Output progress updates to the terminal")

    # Multiprocessing
    my_parser.add_argument("--nproc",
                           dest="nproc",
                           type=int,
                           default=max(1, multiprocessing.cpu_count() - 1),
                           help="Number of processors to employ")

    # Run similarity search
    my_parser.add_argument("--search",
                           dest="search",
                           action="store_true",
                           help="Search for structures with similar unit cells")

    # Run contaminant screen
    my_parser.add_argument("--contaminants",
                           action="store_true",
                           dest="contaminants",
                           help="Run screen of known common contaminants")

    # Run contaminant screen
    my_parser.add_argument("--pdbs", "--pdb",
                           dest="pdbs",
                           nargs="*",
                           default=False,
                           help="PDB codes to test")

    # Positional argument
    my_parser.add_argument("--data_file",
                           dest="data_file",
                           required=True,
                           help="Name of data file to be analyzed")

    # Print help message if no arguments
    if len(sys.argv[1:])==0:
        my_parser.print_help()
        my_parser.exit()

    args = my_parser.parse_args()

    # Fixes a problem from plugin-called code
    args.exchange_dir = False
    args.db_settings = False

    # Insert logic to check or modify args here

    # Running in interactive mode if this code is being called
    if args.json:
        args.run_mode = "json"
    else:
        args.run_mode = "interactive"

    # Capitalize pdb codes
    if args.pdbs:
        tmp_pdbs = []
        for pdb in args.pdbs:
            if not len(pdb) == 4:
                raise Exception(\
                "PDB codes must be 4 characters. %s is not valid." % pdb)
            tmp_pdbs.append(pdb.upper())
        args.pdbs = tmp_pdbs

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
                                  logfile_id="rapd_pdbquery",
                                  level=log_level,
                                  console=commandline_args.test)

    # Set up terminal printer
    # Verbosity
    if commandline_args.json:
        terminal_log_level = 100
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
    if environmental_vars.get("RAPD_DIR_INCREMENT") in ("up", "UP"):
        commandline_args.dir_up = True
    else:
        commandline_args.dir_up = False

    # Construct the command
    command = construct_command(commandline_args=commandline_args)
    #print command

    # Load the plugin
    plugin = modules.load_module(seek_module="plugin",
                                 directories=["plugins.pdbquery"],
                                 logger=logger)

    # Print out plugin info
    tprint(arg="\nPlugin information", level=10, color="blue")
    tprint(arg="  Plugin type:    %s" % plugin.PLUGIN_TYPE, level=10, color="white")
    tprint(arg="  Plugin subtype: %s" % plugin.PLUGIN_SUBTYPE, level=10, color="white")
    tprint(arg="  Plugin version: %s" % plugin.VERSION, level=10, color="white")
    tprint(arg="  Plugin id:      %s" % plugin.ID, level=10, color="white")

    # Run the plugin
    plugin.RapdPlugin(command, tprint, logger)

if __name__ == "__main__":

    main()
