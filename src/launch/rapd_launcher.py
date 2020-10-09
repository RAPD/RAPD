"""
Creates a launcher instance which runs a socket server that can take incoming
commands and launches them to a rapd launch instance that is determined by the
IP address of the host and the optional passed-in tag
"""
#from old_agents.rapd_agent_anom import inp

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
__created__ = "2009-07-10"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

# Standard imports
import argparse
import importlib
from pprint import pprint
import redis.exceptions
import sys
import time

# RAPD imports
from utils.commandline import base_parser
from utils.lock import lock_file, close_lock_file
import utils.log
from utils.modules import load_module
from utils.overwatch import Registrar
import utils.site
import utils.text as text
from utils.text import json
from utils.processes import mp_pool, total_nproc
from bson.objectid import ObjectId
from threading import Thread

import multiprocessing
from multiprocessing.util import Finalize

BUFFER_SIZE = 8192

class Launcher(object):
    """
    Connects to Redis instance, listens for jobs, and spawns new threads using defined
    launcher_adapter
    """

    adapter = None
    ip_address = None
    launcher = None
    tag = None
    pool = None

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

        # Check if additional params in self.launcher
        self.check_settings()
        
        # Load the adapter
        self.load_adapter()

        # Connect to Redis for communications
        self.connect_to_redis()

        # For loop in self.run
        self.running = True

        self.run()

    def run(self):
        """The core process of the Launcher instance"""

        # Set up overwatcher
        if self.overwatch_id:
            self.ow_registrar = Registrar(site=self.site,
                                          ow_type="launcher",
                                          ow_id=self.overwatch_id)
            self.ow_registrar.register({"site_id":json.dumps(self.launcher.get('site_tag')),
                                        "job_list":self.job_list})

        try:
            timer = 0
            # This is the server portion of the code
            while self.running:
                # Have Registrar update status every second
                if round(timer%1,1) in (0.0,1.0):
                    if self.overwatch_id:
                        #self.ow_registrar.update({"site_id":self.site.ID,
                        self.ow_registrar.update({"site_id":json.dumps(self.launcher.get('site_tag')),
                                                  "job_list":self.job_list})
                        #self.ow_registrar.update({"job_list":self.job_list})

                # Look for a new command
                # This will throw a redis.exceptions.ConnectionError if redis is unreachable
                #command = self.redis.brpop(["RAPD_JOBS",], 5)
                try:
                    while self.redis.llen(self.job_list) != 0:
                        command = self.redis.rpop(self.job_list)
                        # Handle the message
                        if command:
                            self.handle_command(json.loads(command))

                            # Only run 1 command
                            # self.running = False
                            # break
                    # sleep a little when jobs aren't coming in.
                    time.sleep(0.2)
                    timer += 0.2
                except redis.exceptions.ConnectionError:
                    if self.logger:
                        self.logger.exception("Remote Redis is not up. Waiting for Sentinal to switch to new host")
                    time.sleep(1)

        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop everything smoothly."""
        self.running = False
        # Close the file lock handle
        close_lock_file()
        # Try to close the pool. Python bugs gives errors!
        if self.pool:
            self.pool.close()
            self.pool.join()
        # Tell overwatch it is closing
        if self.overwatch_id:
            self.ow_registrar.stop()

    def connect_to_redis(self):
        """Connect to the redis instance"""
        redis_database = importlib.import_module('database.redis_adapter')

        self.redis = redis_database.Database(settings=self.site.CONTROL_DATABASE_SETTINGS, 
                                             logger=self.logger)

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
        if self.logger:
            self.logger.debug("Command received channel:%s  message: %s", self.job_list, message)

        # Use the adapter to launch
        #self.adapter(self.site, message, self.launcher)
        # If running thru a shell limit the number of running processes
        if self.pool:
            self.pool.apply_async(self.adapter(self.site, message, self.launcher))
        else:
            self.adapter(self.site, message, self.launcher)

    def get_settings(self):
        """
        Get the settings for this Launcher based on ip address and tag
        """

        # Get IP Address
        self.ip_address = utils.site.get_ip_address()
        #print self.ip_address
        if self.logger:
            self.logger.debug("Found ip address to be %s", self.ip_address)

        # Save typing
        launchers = self.site.LAUNCHER_SETTINGS["LAUNCHER_SPECIFICATIONS"]

        # Look for the launcher matching this ip_address and the input tag
        possible_tags = []
        for launcher in launchers:
            #print launcher
            if launcher.get('ip_address') == self.ip_address and launcher.get('tag') == self.tag:
                self.launcher = launcher
                break
            elif launcher.get('ip_address') == self.ip_address:
                possible_tags.append(launcher.get('tag'))

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
            # Get the job_list to watch for this launcher
            self.job_list = self.launcher.get('job_list')

    def check_settings(self):
        """Check if additional params in self.launcher need setup."""
        # Check if a multiprocessing.Pool needs to be setup for launcher adapter.
        if self.tag == 'shell':
            if self.launcher.get('pool_size', False):
                try:
                    size = int(self.launcher.get('pool_size'))
                except ValueError:
                    size = total_nproc()-1
            else:
                size = total_nproc()-1
            # Make sure its an integer
            self.pool = mp_pool(size)

    def load_adapter(self):
        """Find and load the adapter"""

        # Import the database adapter as database module
        
        self.adapter = load_module(
            seek_module=self.launcher["adapter"],
            directories=self.site.LAUNCHER_SETTINGS["RAPD_LAUNCHER_ADAPTER_DIRECTORIES"]).LauncherAdapter

        if self.logger:
            self.logger.debug(self.adapter)

def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """The Launch process for handling calls for
    computation"""
    parser = argparse.ArgumentParser(parents=[base_parser],
                                     description=commandline_description,
                                     conflict_handler='resolve')

    # Add the possibility to tag the Launcher
    # This will make it possible to run multiple Launcher configurations
    # on one machine
    parser.add_argument("-t", "--tag",
                        action="store",
                        dest="tag",
                        default="",
                        help="Specify a tag for the Launcher. Found in sites.LAUNCHER_SPECIFICATIONS")

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
    #import glob
    #print glob.glob('/tmp/rapd2/lock/*')
    # Single process lock?
    if lock_file(SITE.LAUNCHER_LOCK_FILE):
        print 'another instance of rapd.launcher is running... exiting now'
        sys.exit(9)

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
        logger.debug("  arg:%s  val:%s" % pair)

    LAUNCHER = Launcher(site=SITE,
                        tag=tag,
                        logger=logger,
                        overwatch_id=commandline_args.overwatch_id)

if __name__ == "__main__":

    main()
