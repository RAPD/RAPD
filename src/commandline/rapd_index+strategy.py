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

    # Pair?
    # parser.add_argument("-d",
    #                     action="store",
    #                     dest="detector",
    #                     help="Specify a detector for the analysis")

    return parser.parse_args()

def main():
    """ The main process
    Setup logging and instantiate the model"""

    # Get the commandline args
    commandline_args = get_commandline()
    tprint(commandline_args)

    if commandline_args.listsites:
        tprint(text.info + "Available sites:" + text.stop)
        commandline_utils.print_sites(left_buffer="  ")
        sys.exit()

    # if commandline_args.listdetectors:
    #     tprint(text.info + "Available detectors:" + text.stop)
    #     commandline_utils.print_detectors(left_buffer="  ")
    #     sys.exit()

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()

    tprint(environmental_vars)

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

	# Set up terminal printer
    tprint = utils.log.get_terminal_printer(verbosity=1)

    main()
