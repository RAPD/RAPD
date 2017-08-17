"""
Orchestrates the launch process by wrapping a launch plugin
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2009-2017, Cornell University
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
import os
import sys

# RAPD imports
import utils.commandline
import utils.log
from utils.modules import load_module
import utils.site

class Launch(object):
    """
    Launches json-formatted RAPD command files using the command-appropriate
    rapd plugin
    """

    command = None
    plugin = None
    new_logger = None

    def __init__(self, site, command_file):
        """
        Initialize the Launch
        """

        # Save passed-in variables
        self.site = site
        self.command_file = command_file

        self.run()

    def run(self):
        """
        Orchsetrate the Launch process
        """

        # Start the logger
        self.init_logger()

        # Load and decode json command file
        self.command = self.load_command()

        # Put the site object into the command
        self.command["site"] = self.site

        self.new_logger.debug("command: %s", self.command.get("command", None))

        # Load the plugin for this command
        self.load_plugin(self.command.get("command"))

        # Run the plugin
        plugin = self.plugin.RapdPlugin(site=self.site,
                                        command=self.command,
                                        tprint=False,
                                        logger=self.new_logger)

        plugin.start()

    def load_command(self):
        """
        Load and parse the command file
        """

        # Load the file
        message = open(self.command_file, "r").read()

        # Decode json command file
        return json.loads(message)

    def load_plugin(self, command):
        """
        Load the plugin file for this command

        Keyword arguments
        command -- the command to be run (index+strategy for example)
        """
        # plugin directories we are looking for
        directories = []
        for directory in self.site.RAPD_PLUGIN_DIRECTORIES:
            directories.append(directory+".%s" % self.command.get("command").lower())

        # Load the plugin from directories defined in site file
        self.plugin = load_module(seek_module="plugin",
                                  directories=directories,
                                  logger=self.new_logger)

    def init_logger(self):
        """
        Start the logger for this launched process
        """

        # Derive definitions for log file
        # = os.path.dirname(self.command_file)
        logfile_dir = self.site.LOGFILE_DIR
        logfile_id = os.path.basename(self.command_file).replace(".rapd", "")

        # Instantiate a logger at verbose level
        self.new_logger = utils.log.get_logger(logfile_dir=logfile_dir,
                                           logfile_id=logfile_id,
                                           #level=10)
                                           )



def get_commandline():
    """
    Get the commandline variables and handle them
    """

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
    """
    Run the main process
    """

    # Get the commandline args
    commandline_args = get_commandline()

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()

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
    SITE = importlib.import_module(site_file)

    """
    # Set up logging
    if commandline_args.verbose:
        log_level = 10
    else:
        log_level = SITE.LOG_LEVEL

    run_logger = utils.log.get_logger(logfile_dir=SITE.LOGFILE_DIR,
                                  logfile_id="rapd_launch",
                                  level=log_level)

    run_logger.debug("Commandline arguments:")
    for pair in commandline_args._get_kwargs():
        run_logger.debug("  arg:%s  val:%s", pair[0], pair[1])
    """
    # Run command file[s]
    if commandline_args.command_files:
        for command_file in commandline_args.command_files:
            #run_logger.info("Launching %s", command_file)
            Launch(SITE, command_file)
    else:
        raise Exception("Not sure what to do!")

if __name__ == "__main__":

    main()
