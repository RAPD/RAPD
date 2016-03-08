"""
This file is part of RAPD

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

__created__ = "2009-07-10"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

# Standard imports
import argparse
import importlib
import json
import logging
import logging.handlers

# RAPD imports
import utils.commandline
import utils.log
from utils.modules import load_module
import utils.sites

class Launch(object):
    """
    Launches json-formatted radp command files using the command-appropriate
    rapd agent
    """

    agent = None

    def __init__(self, site, command_file, logger):
        """Initialize the Launch"""

        # Get the logger Instance
        self.logger = logger #logging.getLogger("RAPDLogger")
        self.logger.debug("__init__")

        # Save passed-in variables
        self.site = site
        self.command_file = command_file

        self.logger.debug("%s", self.site)

        self.run()

    def run(self):
        """Orchsetrate the Launch process"""

        # Load and decode json command file
        command, dirs, data, send_address, reply_address = self.load_command()

        self.logger.debug("command: %s", command)
        self.logger.debug("dirs: %s", dirs)
        self.logger.debug("data: %s", data)
        self.logger.debug("send_address: %s", send_address)
        self.logger.debug("reply_address: %s", reply_address)

        # Load the agent for this command
        self.load_agent(command)

        # Run the agent
        self.agent.RapdAgent(self.site, command, data, reply_address)

    def load_command(self):
        """Load and parse the command file"""

        # Load the file
        message = open(self.command_file, "r").read()

        # Decode json command file
        return json.loads(message)

    def load_agent(self, command):
        """Load the agent file for this command"""

        # Agent we are looking for
        seek_module = "rapd_agent_%s" % command.lower()

        self.agent = load_module(seek_module=seek_module,
                                 directories=self.site.RAPD_AGENT_DIRECTORIES)




def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """The Launch process for handling calls for
    computation"""
    parser = argparse.ArgumentParser(parents=[utils.commandline.base_parser],
                                     description=commandline_description)

    # Passing command files is one way to use
    parser.add_argument("command_files",
                        nargs="*",
                        default=False,
                        help="Command files to execute")

    return parser.parse_args()

def main():
    """Run the main process"""

    # Get the commandline args
    commandline_args = get_commandline()
    print commandline_args

    # Determine the site
    site_file = utils.sites.determine_site(site_arg=commandline_args.site)

    # Import the site settings
    SITE = importlib.import_module(site_file)

    # Set up logging
    if commandline_args.verbose:
        log_level = 10
    else:
        log_level = SITE.LOG_LEVEL

    logger = utils.log.get_logger(logfile_dir=SITE.LOGFILE_DIR,
                                  logfile_id="rapd_launch_"+SITE.ID,
                                  level=log_level)

    logger.debug("Commandline arguments:")
    for pair in commandline_args._get_kwargs():
        logger.debug("  arg:%s  val:%s" % pair)

    # Run command file[s]
    if commandline_args.command_files:
        for command_file in commandline_args.command_files:
            Launch(SITE, command_file, logger)
    else:
        raise Exception("Not sure what to do!")

if __name__ == '__main__':

    main()
