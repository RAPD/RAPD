"""
Manager which sorts out jobs and send to appropriate launchers
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2016-2017 Cornell University
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
import json
# import logging
# import logging.handlers
from pprint import pprint
import redis.exceptions
import sys
import time
import threading

# RAPD imports
from utils.commandline import base_parser
from utils.lock import file_lock
import utils.site
import utils.log

# Timer (s) for sending jobs to make sure launchers are alive.
ALIVE_TIMER = 5

class Launcher_monitor(object):
    """
    Monitors which launchers are running.
    """
    def __init__(self, site, tag="", logger=None, overwatch_id=False):
        """
        Initialize the Launcher instance

        Keyword arguments:
        site -- site object with relevant information to run
        tag -- optional string describing launcher. Defined in site.LAUNCHER_REGISTER
        logger -- logger instance (default = None)
        overwatch_id -- id for optional overwatcher instance
        """
        threading.Thread.__init__ (self)
        # Get the logger Instance
        self.logger = logger

        # Save passed-in variables
        self.site = site
        self.tag = tag
        self.overwatch_id = overwatch_id
        
        self.running = True
        self.timer = 0
        
        self.start()
    
    def run(self):
        
        # Get the initial possible jobs lists
        jlist = get_job_list()
        # Now check if they are running
        
        
        while self.running:
            if round(self.timer%self.hb_int,1) == 1.0:
                #print self.timer
                for job in self.jobs.keys():
                    self.check_job(job)
            time.sleep(0.2)
            self.timer += 0.2
        
        
    def stop(self):
        self.running = False
    
    def get_job_list():
        """Get all possible launcher job lists"""
        jlist = []
        for l in self.site.LAUNCHER_SETTINGS["LAUNCHER_SPECIFICATIONS"].keys():
            if self.site.LAUNCHER_SETTINGS["LAUNCHER_SPECIFICATIONS"][l].get('job_list') not in jlist:
                jlist.append(self.site.LAUNCHER_SETTINGS["LAUNCHER_SPECIFICATIONS"][l].get('job_list'))
        return jlist


class Lancher_manager(object):
    """
    Listens to the 'RAPD_JOBS'list and sends jobs to proper
    launcher. 
    """
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

                        # Only run 1 command
                        # self.running = False
                        # break
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
        #self.adapter(self.site, message, self.specifications)
def connect_to_redis(self):
    """Connect to the redis instance"""
    redis_database = importlib.import_module('database.rapd_redis_adapter')

    self.redis_database = redis_database.Database(settings=self.site.CONTROL_DATABASE_SETTINGS)
    self.redis = self.redis_database.connect_to_redis()

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
    """
    parser.add_argument("-t", "--tag",
                        action="store",
                        dest="tag",
                        default="",
                        help="Specify a tag for the Launcher")
    """
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
    """
    # Determine the tag - commandline wins
    if commandline_args.tag:
        tag = commandline_args.tag
    elif environmental_vars.has_key("RAPD_LAUNCHER_TAG"):
        tag = environmental_vars["RAPD_LAUNCHER_TAG"]
    else:
        tag = ""
    """
    # Get th possible Launcher tags
    jlist = get_job_list(SITE)
    
    # Single process lock?
    file_lock(SITE.LAUNCHER_MANAGER_LOCK_FILE)

    # Set up logging level
    if commandline_args.verbose:
        log_level = 10
    else:
        log_level = SITE.LOG_LEVEL

    # Instantiate the logger
    logger = utils.log.get_logger(logfile_dir=SITE.LOGFILE_DIR,
                                  logfile_id="rapd_launcher_manager")

    logger.debug("Commandline arguments:")
    for pair in commandline_args._get_kwargs():
        logger.debug("  arg:%s  val:%s" % pair)
    """
    LAUNCHER_MANAGER = Launcher_Manager(site=SITE,
                        tag=tag,
                        logger=logger,
                        overwatch_id=commandline_args.overwatch_id)
    LAUNCHER_MANAGER.start()
    
    

    try:
        time.sleep(100)
    except KeyboardInterrupt:
        LAUNCHER.stop()
    """

if __name__ == "__main__":

    main()