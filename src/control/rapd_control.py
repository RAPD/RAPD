"""
File for launching the controller process for a RAPD site install
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2009-2018, Cornell University
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

__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

# Standard imports
import argparse
import importlib
import sys
import time

# RAPD imports
import utils.commandline
import utils.log
from utils.lock import lock_file, close_lock_file
import utils.site
import utils.text as text
from control.model import Model

def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """The core rapd process for coordination of a
    site install"""
    parser = argparse.ArgumentParser(parents=[utils.commandline.base_parser],
                                     description=commandline_description)

    parser.add_argument("--clean_start",
                        action="store_true",
                        dest="clean_start",
                        help="Wipe input queues clean before starting")

    # Run without monitoring the beamline
    parser.add_argument("--no_monitor",
                        action="store_false",
                        dest="monitor",
                        help="Don't monitor the beamline")

    return parser.parse_args()

def main():
    """ The main process
    Setup logging and instantiate the model"""

    # Get the commandline args
    commandline_args = get_commandline()

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()

    # Get site - commandline wins
    site = False
    if commandline_args.site:
        site = commandline_args.site
    elif "RAPD_SITE" in environmental_vars:
        site = environmental_vars["RAPD_SITE"]

    # If no site, error
    if site == False:
        print(text.error+"Could not determine a site. Exiting."+text.stop)
        sys.exit(9)

    # Determine the site_file
    site_file = utils.site.determine_site(site_arg=site)

    # Error out if no site_file to import
    if site_file == False:
        print(text.error+"Could not find a site file. Exiting."+text.stop)
        sys.exit(9)

    # Import the site settings
    # print "Importing %s" % site_file
    SITE = importlib.import_module(site_file)

    # Single process lock?
    if lock_file(SITE.CONTROL_LOCK_FILE):
        print('another instance of rapd.control is running... exiting now')
        sys.exit(9)

    # Set up logging
    if commandline_args.verbose:
        log_level = 10
    else:
        log_level = SITE.LOG_LEVEL
    logger = utils.log.get_logger(logfile_dir=SITE.LOGFILE_DIR,
                                  logfile_id="rapd_control",
                                  #level=log_level
                                 )

    logger.debug("Commandline arguments:")
    settings = {}
    for pair in commandline_args._get_kwargs():
        logger.debug("  arg:%s  val:%s" % pair)
        #settings[arg] = val
        settings[pair[0]] = pair[1]

    # Instantiate the model
    MODEL = Model(SITE=SITE,
                  settings=settings,
                  overwatch_id=commandline_args.overwatch_id)

    try:
      while 1:
        time.sleep(100)
    except KeyboardInterrupt:
        # Close everything cleanly
        MODEL.stop()
        # c;lose the file lock
        close_lock_file()


if __name__ == "__main__":

	# Set up terminal printer
    tprint = utils.log.get_terminal_printer(verbosity=1)

    main()
