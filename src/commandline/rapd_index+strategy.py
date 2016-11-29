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
import importlib
import sys

# RAPD imports
# import utils.commandline
import utils.log
# import utils.lock
# import utils.site
import utils.text as text
import commandline_utils


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
                        nargs=1,
                        choices=["best", "mosflm"],
                        help="Type of strategy")

    # Complexity of BEST strategy
    parser.add_argument("--best_complexity",
                        action="store",
                        dest="best_complexity",
                        nargs=1,
                        choices=["min", "full"],
                        help="Complexity of BEST strategy")

    # Number of mosflm segments
    parser.add_argument("--mosflm_segments",
                        action="store",
                        dest="mosflm_segments",
                        nargs=1,
                        choices=[1, 2, 3, 4, 5],
                        help="Number of mosflm segments")

    # Rotation range for mosflm segments
    parser.add_argument("--mosflm_range",
                        action="store",
                        dest="mosflm_range",
                        nargs=1,
                        type=float,
                        help="Rotation range for mosflm segments")

    # Rotation range for mosflm segments
    parser.add_argument("--mosflm_start",
                        action="store",
                        dest="mosflm_start",
                        nargs=1,
                        type=float,
                        help="Start of allowable rotation range for mosflm segments")

    # Rotation range for mosflm segments
    parser.add_argument("--mosflm_end",
                        action="store",
                        dest="mosflm_end",
                        nargs=1,
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
            for data_file in data_files:
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

    





    # Get site - commandline wins
    site = False
    if commandline_args.site:
        site = commandline_args.site
    elif environmental_vars.has_key("RAPD_SITE"):
        site = environmental_vars["RAPD_SITE"]

    # If no site, error
    if site == False:
        print text.error+"Could not determine a site. Exiting."+text.stop
        sys.exit(9)

    # Determine the site_file
    site_file = utils.site.determine_site(site_arg=site)

    # Error out if no site_file to import
    if site_file == False:
        print text.error+"Could not find a site file. Exiting."+text.stop
        sys.exit(9)

    # Import the site settings
    # print "Importing %s" % site_file
    SITE = importlib.import_module(site_file)

	# Single process lock?
    utils.lock.file_lock(SITE.CONTROL_LOCK_FILE)

    # Set up logging
    if commandline_args.verbose:
        log_level = 10
    else:
        log_level = SITE.LOG_LEVEL
    logger = utils.log.get_logger(logfile_dir=SITE.LOGFILE_DIR,
                                  logfile_id="rapd_control",
                                  level=log_level)

    logger.debug("Commandline arguments:")
    for pair in commandline_args._get_kwargs():
        logger.debug("  arg:%s  val:%s" % pair)

    # Instantiate the model
    # MODEL = Model(SITE=SITE,
    #               overwatch_id=commandline_args.overwatch_id)

if __name__ == "__main__":

	# # Set up terminal printer
    # tprint = utils.log.get_terminal_printer(verbosity=1)

    main()
