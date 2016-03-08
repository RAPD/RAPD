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
import logging
import logging.handlers
import socket
import time

# RAPD imports
import utils.commandline
from utils.lock import file_lock
import utils.log
from utils.modules import load_module
import utils.sites

# from rapd_database import Database

BUFFER_SIZE = 8192
database = None

class Launcher(object):
    """
    Runs a socket server and spawns new threads when connections are received
    """

    database = None
    adapter = None
    address = None
    ip_address = None
    tag = None
    port = None
    job_types = None
    adapter_file = None

    def __init__(self, site, tag=""):
        """
        The main server thread
        """

        # Get the logger Instance
        self.logger = logging.getLogger("RAPDLogger")
        self.logger.debug("__init__")

        # Save passed-in variables
        self.site = site
        self.tag = tag

        # Retrieve settings for this Launcher
        self.get_settings()

        # Load the adapter
        self.load_adapter()

        # Set up connection to the control database
        self.connect_to_database()

        # Start listening for commands
        self.run()

    def run(self):
        """
        The core process of the Launcher instance
        """

        # Create socket to listen for commands
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.bind(("", self.specifications["port"]))

        # This is the server portion of the code
        while(1):
            try:
                s.listen(5)
                # print 'MODE', self.mode
                conn, addr = s.accept()
                # tmp = Handler(conn=conn,
                #               addr=addr,
                #               db=self.DATABASE,
                #               mode = self.mode,
                #               logger=self.logger)

                # Read the message from the socket
                message = ""
                while not (message.endswith('<rapd_end>')):
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
                print "5 seconds up"

        # If we exit...
        s.close()

    def handle_message(self, message):
        """
        Handle an incoming message
        """

        self.logger.debug("Message received: %s", message)

        # Strip the message of its delivery tags
        message = message.rstrip().replace("<rapd_start>","").replace("<rapd_end>","")

        # Use the adapter to launch
        self.adapter(self.site.ID, message, self.specifications)

    def get_settings(self):
        """
        Get the settings for this Launcher based on ip address and tag
        """

        # Save typing
        launchers = self.site.LAUNCHER_SETTINGS["LAUNCHER_REGISTER"]

        # Get IP Address
        self.ip_address = utils.sites.get_ip_address()

        for launcher in launchers:
            if launcher[0] == self.ip_address and launcher[1] == self.tag:
                self.launcher = launcher
                break

        # No address
        if self.launcher == None:
            raise Exception("No definition for launcher in site file")
        else:
            # Unpack address
            self.ip_address, self.tag, self.launcher_id = self.launcher
            self.specifications = self.site.LAUNCHER_SETTINGS["LAUNCHER_SPECIFICATIONS"][self.launcher_id]

    def load_adapter(self):
        """Find and load the adapter"""

        # Import the database adapter as database module
        self.adapter = load_module(
            seek_module=self.specifications["adapter"],
            directories=self.site.LAUNCHER_SETTINGS["RAPD_LAUNCHER_ADAPTER_DIRECTORIES"]).LauncherAdapter

        self.logger.debug(self.adapter)

    def connect_to_database(self):
        """Set up database connection"""

        # Shorten it a little
        site = self.site

        # Import the database adapter as database module
        global database
        database = importlib.import_module('database.rapd_%s_adapter' % site.CONTROL_DATABASE)

        # Instantiate the database connection
        self.database = database.Database(settings=site.CONTROL_DATABASE_SETTINGS)





def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """The Launch process for handling calls for
    computation"""
    parser = argparse.ArgumentParser(parents=[utils.commandline.base_parser],
                                     description=commandline_description)

    # Add the possibility to tag the Launcher
    # This will make it possible to run multiple Launcher configurations
    # on one machine
    parser.add_argument("--tag",
                        action="store",
                        dest="tag",
                        default="",
                        help="Specify a tag for the Launcher")

    return parser.parse_args()

def main():
    """Run the main process"""

    # Get the commandline args
    commandline_args = get_commandline()

    # Determine the site
    site_file = utils.sites.determine_site(site_arg=commandline_args.site)

    # Import the site settings
    SITE = importlib.import_module(site_file)

    # Single process lock?
    file_lock(SITE.LAUNCHER_LOCK_FILE)

    # Set up logging
    if commandline_args.verbose:
        log_level = 10
    else:
        log_level = SITE.LOG_LEVEL
    logger = utils.log.get_logger(logfile_dir=SITE.LOGFILE_DIR,
                                  logfile_id="rapd_launcher_"+SITE.ID,
                                  level=log_level)

    logger.debug("Commandline arguments:")
    for pair in commandline_args._get_kwargs():
        logger.debug("  arg:%s  val:%s" % pair)

    LAUNCHER = Launcher(site=SITE,
                        tag=commandline_args.tag)

if __name__ == "__main__":

    main()
