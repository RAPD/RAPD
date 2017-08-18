"""
Creates a launcher instance which runs a socket server that can take incoming
commands and launches them to a rapd launch instance that is determined by the
IP address of the host and the optional passed-in tag
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
# import logging
# import logging.handlers
from pprint import pprint
import redis.exceptions
import socket
import sys
import time
import threading

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
    Connects to Redis instance, listens for jobs, and spawns new threads using defined
    launcher_adapter
    """

    adapter = None
    adapter_file = None
    database = None
    # address = None
    ip_address = None
    job_types = None
    launcher = None
    port = None
    tag = None

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

        # Connect to Redis for communications
        self.connect_to_redis()

        self.running = True

        # Start listening for commands through a thread for clean exit.
        threading.Thread(target=self.run).start()

    def run(self):
        """The core process of the Launcher instance"""

        # Set up overwatcher
        if self.overwatch_id:
            self.ow_registrar = Registrar(site=self.site,
                                          ow_type="launcher",
                                          ow_id=self.overwatch_id)
            self.ow_registrar.register({"site_id":self.site.ID})

        # This is the server portion of the code
        while self.running:
            # Have Registrar update status
            if self.overwatch_id:
                self.ow_registrar.update({"site_id":self.site.ID})

            # Look for a new command
            # This will trow a redis.exceptions.ConnectionError if redis is unreachable
            #command = self.redis.brpop(["RAPD_JOBS",], 5)
            try:
                while self.redis.llen("RAPD_JOBS") != 0:
                    command = self.redis.rpop("RAPD_JOBS")
                    # Handle the message
                    if command:
                        #self.handle_command("RAPD_JOBS", json.loads(command))
                        self.handle_command(json.loads(command))
                # sleep a little when jobs aren't coming in.
                time.sleep(0.2)
            except redis.exceptions.ConnectionError:
                self.logger.exception("Remote Redis is not up. Waiting for Sentinal to switch to new host")
                time.sleep(1)

    def stop(self):
        """Stop everything smoothly."""
        self.running = False
        if self.site.CONTROL_DATABASE_SETTINGS['REDIS_CONNECTION'] == 'pool':
            self.redis.close()

    def connect_to_redis(self):
        """Connect to the redis instance"""
        # Create a pool connection
        redis_database = importlib.import_module('database.rapd_redis_adapter')

        self.redis_database = redis_database.Database(settings=self.site.CONTROL_DATABASE_SETTINGS)
        if self.site.CONTROL_DATABASE_SETTINGS['REDIS_CONNECTION'] == 'pool':
            # For a Redis pool connection
            self.redis = self.redis_database.connect_redis_pool()
        else:
            # For a Redis sentinal connection
            self.redis = self.redis_database.connect_redis_manager_HA()

    def handle_command(self, command):
        """
        Handle an incoming command

        Keyword arguments:
        command -- command from redis
        """
        print "handle_command"
        pprint(command)

        # Split up the command
        message = command

        # Update preferences to be in server run mode
        if not message.get("preferences"):
            message["preferences"] = {}
        message["preferences"]["run_mode"] = "server"

        self.logger.debug("Command received channel:RAPD_JOBS  message: %s", message)

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
                for tag in possible_tags:
                    print "    %s" % tag
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
                                  logfile_id="rapd_launcher")

    logger.debug("Commandline arguments:")
    for pair in commandline_args._get_kwargs():
        logger.debug("  arg:%s  val:%s", pair)

    LAUNCHER = Launcher(site=SITE,
                        tag=tag,
                        logger=logger,
                        overwatch_id=commandline_args.overwatch_id)

    try:
        time.sleep(100)
    except KeyboardInterrupt:
        LAUNCHER.stop()

if __name__ == "__main__":

    main()
