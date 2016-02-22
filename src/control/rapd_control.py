"""
RAPD - Automated data analysis for macromolecular crystallography

Copyright (C) 2009-2016, Cornell University
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

"""
rapd.py is the core process for RAPD.
"""

import argparse
import fcntl
import importlib
import os

import utils.commandline
import utils.log
import utils.site_tools
from control.rapd_model import Model

file_handle = None

"""
	# Assure we are running as a singleton
	file_path = '/tmp/lock/rapd_freeagent_distl.lock'

	if not os.path.exists(os.path.dirname(file_path)):
			os.makedirs((os.path.dirname(file_path)))

	if file_is_locked(file_path):
			print 'another instance is running exiting now'
			sys.exit(0)
	else:
			print 'no other instance is running'
"""


def file_is_locked(file_path):
    """Method to make sure only one instance is running on this machine"""
    global file_handle

	# Create the directory for file_path if it does not exist
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))

    file_handle = open(file_path, "w")
    try:
        fcntl.lockf(file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return False
    except IOError:
        return True

def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """The core rapd process for coordination of a
    site install"""
    parser = argparse.ArgumentParser(parents=[utils.commandline.base_parser],
                                     description=commandline_description)

    return parser.parse_args()

def main(site_in=None):
    """ The main process
    Setup logging and instantiate the model"""

    # Get the commandline args
    commandline_args = get_commandline()

    # Determine the site
    site_file = utils.site_tools.determine_site(site_arg=commandline_args.site)

    # Import the site settings
    SITE = importlib.import_module(site_file)

	# Single process lock?
    if SITE.LOCK_FILE:
        if file_is_locked(SITE.LOCK_FILE):
            raise Exception("%s is already locked, unable to run" % SITE.LOCK_FILE)

    # Set up logging
    if commandline_args.verbose:
        log_level = 10
    else:
        log_level = SITE.LOG_LEVEL
    logger = utils.log.get_logger(logfile_dir=SITE.LOGFILE_DIR,
                                  logfile_id="rapd_core_"+SITE.ID,
                                  level=log_level)

    logger.debug("Commandline arguments:")
    for pair in commandline_args._get_kwargs():
        logger.debug("  arg:%s  val:%s" % pair)

    # Instantiate the model
    MODEL = Model(SITE=SITE)


if __name__ == "__main__":

	# Set up terminal printer
    tprint = utils.log.get_terminal_printer(verbosity=1)

    main()
