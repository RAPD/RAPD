"""
Creates a launcher instance which runs a socket server that can take incoming
commands and launches them to a rapd launch instance that is determined by the
IP address of the host and the optional passed-in tag
"""

__license__ = """
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
# import logging
# import logging.handlers
import socket
import sys
import time

# RAPD imports
from utils.commandline import base_parser
from utils.lock import file_lock
import utils.log
from utils.modules import load_module
from utils.overwatch import Registrar
import utils.site
import utils.text as text

BUFFER_SIZE = 8192

class Launcher(object):
    """
    Runs a socket server and spawns new threads using defined launcher_adapter
    when connections are received
    """

    database = None
    adapter = None
    # address = None
    ip_address = None
    tag = None
    port = None
    job_types = None
    adapter_file = None
    launcher = None

    def __init__(self, site, tag="", logger=None, overwatch_id=False):
        """
        Initialize the Launcher instance

        Keyword arguments:
        site -- site object with relevant information to run
        tag -- optional string describing launcher. Defined in site.LAUNCHER_REGISTER
        logger -- logger instance (default = None)
        overwatch_id -- id for optional overwatcher instance
        """

        # Get the logger Instance
        self.logger = logger

        # Save passed-in variables
        self.site = site
        self.tag = tag
        self.overwatch_id = overwatch_id

        # Retrieve settings for this Launcher
        self.get_settings()

        # Load the adapter
        self.load_adapter()

        # Start listening for commands
        self.run()

    def run(self):
        """The core process of the Launcher instance"""

        # Set up overwatcher
        if self.overwatch_id:
            self.ow_registrar = Registrar(site=self.site,
                                          ow_type="launcher",
                                          ow_id=self.overwatch_id)
            self.ow_registrar.register({"site_id":self.site.ID})

        # Create socket to listen for commands
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.settimeout(5)
        _socket.bind(("", self.specifications["port"]))

        # This is the server portion of the code
        while 1:
            try:
                # Have Registrar update status
                if self.overwatch_id:
                    self.ow_registrar.update({"site_id":self.site.ID})

                # Listen for connections
                _socket.listen(5)
                conn, address = _socket.accept()

                # Read the message from the socket
                message = ""
                while not message.endswith("<rapd_end>"):
                    try:
                        data = conn.recv(BUFFER_SIZE)
                        message += data
                    except:
                        pass
                    time.sleep(0.01)

                # Close the connection
                conn.close()

                # Handle the message
                self.handle_message(message)

            except socket.timeout:
                pass
                # print "5 seconds up"

        # If we exit...
        _socket.close()

    def handle_message(self, message):
        """
        Handle an incoming message

        Keyword arguments:
        message -- raw message from socket
        """

        self.logger.debug("Message received: %s", message)

        # Strip the message of its delivery tags
        message = message.rstrip().replace("<rapd_start>", "").replace("<rapd_end>", "")

        # Use the adapter to launch
        self.adapter(self.site, message, self.specifications)

    def get_settings(self):
        """
        Get the settings for this Launcher based on ip address and tag
        """

        # Save typing
        launchers = self.site.LAUNCHER_SETTINGS["LAUNCHER_REGISTER"]

        # Get IP Address
        self.ip_address = utils.site.get_ip_address()
        self.logger.debug("Found ip address to be %s", self.ip_address)

        # Look for the launcher matching this ip_address and the input tag
        possible_tags = []
        for launcher in launchers:
            if launcher[0] == self.ip_address and launcher[1] == self.tag:
                self.launcher = launcher
                break
            elif launcher[0] == self.ip_address:
                possible_tags.append(launcher[1])

        # No launcher adapter
        if self.launcher is None:

            # No launchers for this IP address
            if len(possible_tags) == 0:
                print "  There are no launcher adapters registered for this ip address"
            # IP Address in launchers, but not the input tag
            else:
                print text.error + "There is a launcher adapter registered for thi\
s IP address (%s), but not for the input tag (%s)" % (self.ip_address, self.tag)
                print "  Available tags for this IP address:"
                for t in possible_tags:
                    print "    %s" % t
                print text.stop

            # Exit in error state
            sys.exit(9)
        else:
            # Unpack address
            self.ip_address, self.tag, self.launcher_id = self.launcher
            self.specifications = self.site.LAUNCHER_SETTINGS["LAUNCHER_SPECIFICATIONS"][self.launcher_id]
            # Tag launcher in self.site
            self.site.LAUNCHER_ID = self.launcher_id

    def load_adapter(self):
        """Find and load the adapter"""

        # Import the database adapter as database module
        self.adapter = load_module(
            seek_module=self.specifications["adapter"],
            directories=self.site.LAUNCHER_SETTINGS["RAPD_LAUNCHER_ADAPTER_DIRECTORIES"]).LauncherAdapter

        self.logger.debug(self.adapter)

    # def connect_to_database(self):
    #     """Set up database connection"""
    #
    #     # Import the database adapter as database module
    #     database = importlib.import_module('database.rapd_%s_adapter' % self.site.CONTROL_DATABASE)
    #
    #     # Instantiate the database connection
    #     self.database = database.Database(settings=self.site.CONTROL_DATABASE_SETTINGS)




def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """The Launch process for handling calls for
    computation"""
    parser = argparse.ArgumentParser(parents=[base_parser],
                                     description=commandline_description)

    # Add the possibility to tag the Launcher
    # This will make it possible to run multiple Launcher configurations
    # on one machine
    parser.add_argument("--tag", "-t",
                        action="store",
                        dest="tag",
                        default="",
                        help="Specify a tag for the Launcher")

    return parser.parse_args()

def main():
    """Run the main process"""

    # Get the commandline args
    commandline_args = get_commandline()

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()

    # Get site - commandline wins
    if commandline_args.site:
        site = commandline_args.site
    elif environmental_vars["RAPD_SITE"]:
        site = environmental_vars["RAPD_SITE"]

    # Determine the site_file
    site_file = utils.site.determine_site(site_arg=site)

    # Import the site settings
    SITE = importlib.import_module(site_file)

    # Determine the tag - commandline wins
    if commandline_args.tag:
        tag = commandline_args.tag
    elif environmental_vars.has_key("RAPD_LAUNCHER_TAG"):
        tag = environmental_vars["RAPD_LAUNCHER_TAG"]
    else:
        tag = ""

    # Single process lock?
    file_lock(SITE.LAUNCHER_LOCK_FILE)

    # Set up logging level
    if commandline_args.verbose:
        log_level = 10
    else:
        log_level = SITE.LOG_LEVEL

    # Instantiate the logger
    logger = utils.log.get_logger(logfile_dir=SITE.LOGFILE_DIR,
                                  logfile_id="rapd_launcher",
                                  level=log_level)

    logger.debug("Commandline arguments:")
    for pair in commandline_args._get_kwargs():
        logger.debug("  arg:%s  val:%s" % pair)

    LAUNCHER = Launcher(site=SITE,
                        tag=tag,
                        logger=logger,
                        overwatch_id=commandline_args.overwatch_id)

if __name__ == "__main__":

    main()
