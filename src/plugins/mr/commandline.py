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
import importlib

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
        data_file = ""
        struct_file = ""
        json = True | False
        no_color = True | False
        nproc = int
        progress = True | False
        run_mode = "interactive" | "json" | "server" | "subprocess"
        test = True | False
        verbose = True | False
    """

    # The task to be carried out
    command = {
        "command": "MR",
        "process_id": uuid.uuid1().get_hex(),
        "status": 0,
        }

    # Work directory
    work_dir = commandline_utils.check_work_dir(
        os.path.join(
            os.path.abspath(os.path.curdir),
            "rapd_mr_%s" %  ".".join(
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
        "struct_file": os.path.abspath(commandline_args.struct_file),
        #"db_settings": commandline_args.db_settings
    }

    # Plugin settings
    command["preferences"] = {
        "clean": commandline_args.clean,
        "json": commandline_args.json,
        "nproc": commandline_args.nproc,
        "progress": commandline_args.progress,
        "run_mode": commandline_args.run_mode,
        "test": commandline_args.test,
        "adf": commandline_args.adf,
    }

    return command

def get_commandline():
    """Grabs the commandline"""

    # Parse the commandline arguments
    commandline_description = "Launch mr plugin"
    parser = argparse.ArgumentParser(description=commandline_description)
    
    # Parse the commandline arguments
    #commandline_description = """Launch an MR on input model and data"""
    #parser = argparse.ArgumentParser(parents=[commandline_utils.dp_parser],
    #                                 description=commandline_description)

    # Run in test mode
    parser.add_argument("-t", "--test",
                           action="store_true",
                           dest="test",
                           help="Run in test mode")

    # Verbose
    parser.add_argument("-v", "--verbose",
                            action="store_true",
                            dest="verbose",
                            help="More output")

    # Quiet
    parser.add_argument("-q", "--quiet",
                           action="store_false",
                           dest="verbose",
                           help="Run with less output")
    # The site
    parser.add_argument("-s", "--site",
                       action="store",
                       dest="site",
                       help="Define the site (ie. NECAT)")

    # Clean
    parser.add_argument("--clean",
                           action="store_true",
                           dest="clean",
                           help="Remove intermediate files")

    # Color
    parser.add_argument("--color",
                           action="store_false",
                           dest="no_color",
                           default=False,
                           help="Color the terminal output")

    # No color
    parser.add_argument("--nocolor",
                           action="store_true",
                           dest="no_color",
                           help="Do not color the terminal output")

    # JSON Output
    parser.add_argument("-j", "--json",
                           action="store_true",
                           dest="json",
                           help="Output JSON format string")

    # Output progress updates?
    parser.add_argument("--progress",
                           action="store_true",
                           dest="progress",
                           help="Output progress updates to the terminal")
    
    # Set filehandle for progress output
    parser.add_argument("--progress-fd",
                           action="store",
                           dest="progress_fd",
                           default=False,
                           help="Output progress updates to a file descriptor. No need to also use --progress, unless you want JSON on the terminal too.")

    # Multiprocessing
    parser.add_argument("--nproc",
                           dest="nproc",
                           type=int,
                           default=max(1, multiprocessing.cpu_count() - 1),
                           help="Number of processors to employ")
    
    # Calculate ADF map on solutions
    parser.add_argument("--adf",
                           action="store_true",
                           dest="adf",
                           help="Calculate Anomalous Difference Fourier map on solution")

    # Run specific structure file
    parser.add_argument("--struct_file", "--pdb", "--cif",
                           dest="struct_file",
                           required=True,
                           help="PDB/mmCIF file path or a PDB code.")

    # Positional argument
    parser.add_argument("--data_file", "--mtz",
                           dest="data_file",
                           required=True,
                           help="Name of data file to be analyzed")

    # Print help message if no arguments
    if len(sys.argv[1:])==0:
        parser.print_help()
        parser.exit()

    args = parser.parse_args()

    # Fixes a problem from plugin-called code
    args.exchange_dir = False
    args.db_settings = False

    # Insert logic to check or modify args here

    # Running in interactive mode if this code is being called
    if args.json:
        args.run_mode = "json"
    else:
        args.run_mode = "interactive"
        # Show progress in interactive version
        args.progress = True

    return args

def print_welcome_message(printer):
    """Print a welcome message to the terminal"""
    message = """
------------
RAPD MR
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
                                  logfile_id="rapd_mr",
                                  level=log_level,
                                  #console=commandline_args.test
                                  console=False)
    
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

    # Get site - commandline wins over the environmental variable
    site = False
    site_module = False
    if commandline_args.site:
        site = commandline_args.site
    elif environmental_vars.has_key("RAPD_SITE"):
        site = environmental_vars["RAPD_SITE"]

    # If someone specifies the site or found in env.
    if site and not site_module:
        site_file = utils.site.determine_site(site_arg=site)
        site_module = importlib.import_module(site_file)

    # Construct the command
    command = construct_command(commandline_args=commandline_args)

    # Load the plugin
    plugin = modules.load_module(seek_module="plugin",
                                 directories=["plugins.mr"],
                                 logger=logger)

    # Print out plugin info
    tprint(arg="\nPlugin information", level=10, color="blue")
    tprint(arg="  Plugin type:    %s" % plugin.PLUGIN_TYPE, level=10, color="white")
    tprint(arg="  Plugin subtype: %s" % plugin.PLUGIN_SUBTYPE, level=10, color="white")
    tprint(arg="  Plugin version: %s" % plugin.VERSION, level=10, color="white")
    tprint(arg="  Plugin id:      %s" % plugin.ID, level=10, color="white")

    # Run the plugin
    # Instantiate the plugin
    plugin_instance = plugin.RapdPlugin(command=command,
                                        site=site_module,
                                        tprint=tprint,
                                        logger=logger)
    plugin_instance.start()

if __name__ == "__main__":

    main()
