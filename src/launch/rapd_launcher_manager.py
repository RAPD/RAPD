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
import logging
import importlib
from pprint import pprint
import redis.exceptions
import time
import threading
from collections import OrderedDict


# RAPD imports
import utils.launch_tools as launch_tools
from utils.commandline import base_parser
from utils.lock import file_lock
import utils.site
import utils.log
from utils.overwatch import Registrar
from utils.text import json
#import json
from bson.objectid import ObjectId

# Timer (s) for checking which launchers are alive.
TIMER = 5

class Launcher_Manager(threading.Thread):
    """
    Listens to the 'RAPD_JOBS'list and sends jobs to proper
    launcher.
    """
    def __init__(self, site, logger=False, overwatch_id=False):
        """
        Initialize the Launcher instance

        Keyword arguments:
        site -- site object with relevant information to run
        redis -- Redis instance for communication
        logger -- logger instance (default = None)
        overwatch_id -- id for optional overwatcher instance
        """
        # If logger is passed in from main use that...
        if logger:
            self.logger = logger
        else:
            # Otherwise, get the rapd logger
            self.logger = logging.getLogger("RAPDLogger")

        # Initialize the thread
        threading.Thread.__init__(self)

        # Save passed-in variables
        self.site = site
        self.overwatch_id = overwatch_id

        self.running = True
        self.timer = 0
        self.job_list = []

        self.connect_to_redis()

        self.start()

    def run(self):
        """The core process of the Launcher instance"""

        # Set up overwatcher
        if self.overwatch_id:
            self.ow_registrar = Registrar(site=self.site,
                                          ow_type="control",
                                          ow_id=self.overwatch_id)
            self.ow_registrar.register()

        # Get the initial possible jobs lists
        full_job_list = [x.get('job_list') for x in self.site.LAUNCHER_SETTINGS["LAUNCHER_SPECIFICATIONS"]]

        try:
            # This is the server portion of the code
            while self.running:
                # Have Registrar update status
                if self.overwatch_id:
                    self.ow_registrar.update()

                # Get updated job list by checking which launchers are running
                # Reassign jobs if launcher(s) status changes
                if round(self.timer%TIMER,1) == 1.0:
                    try:
                        # Check which launchers are running
                        temp = [l for l in full_job_list if self.redis.get("OW:"+l)]

                        # Determine which launcher(s) went offline
                        offline = [line for line in self.job_list if temp.count(line) == False]
                        if len(offline) > 0:
                            # Pop waiting jobs off their job_lists and push back in RAPD_JOBS for reassignment.
                            for _l in offline:
                                while self.redis.llen(_l) != 0:
                                    self.redis.rpoplpush(_l, 'RAPD_JOBS')

                        # Determine which launcher(s) came online (Also runs at startup!)
                        online = [line for line in temp if self.job_list.count(line) == False]
                        if len(online) > 0:
                            # Pop jobs off RAPD_JOBS_WAITING and push back onto RAPD_JOBS for reassignment.
                            while self.redis.llen('RAPD_JOBS_WAITING') != 0:
                                self.redis.rpoplpush('RAPD_JOBS_WAITING', 'RAPD_JOBS')

                        # Update the self.job_list
                        self.job_list = temp

                    except redis.exceptions.ConnectionError:
                        if self.logger:
                            self.logger.exception("Remote Redis is not up. Waiting for Sentinal to switch to new host")
                        time.sleep(1)

                # Look for a new command
                # This will throw a redis.exceptions.ConnectionError if redis is unreachable
                #command = self.redis.brpop(["RAPD_JOBS",], 5)
                try:
                    while self.redis.llen("RAPD_JOBS") != 0:
                        command = self.redis.rpop("RAPD_JOBS")
                        # Handle the message
                        if command:
                            #self.push_command(json.loads(command))
                            self.push_command(json.loads(command))
                            # Only run 1 command
                            # self.running = False
                            # break
                    # sleep a little when jobs aren't coming in.
                    time.sleep(0.2)
                    self.timer += 0.2
                except redis.exceptions.ConnectionError:
                    if self.logger:
                        self.logger.exception("Remote Redis is not up. Waiting for Sentinal to switch to new host")
                    time.sleep(1)

        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        if self.logger:
            self.logger.debug('shutting down launcher manager')
        self.running = False
        if self.overwatch_id:
            self.ow_registrar.stop()
        self.redis_db.stop()

    def set_launcher(self, command=False, site_tag=False):
        """Find the correct running launcher to launch a specific job COMMAND"""
        # list of commands to look for in the 'job_types'
        # If the highest prioity launcher is 'ALL', it is chosen.
        search = ['ALL']
        if command:
            search.append(command)

        # Search through launchers
        for x in self.site.LAUNCHER_SETTINGS["LAUNCHER_SPECIFICATIONS"]:
            # Is launcher running?
            if x.get('job_list') in self.job_list:
                # check if its job type matches the command
                for j in search:
                    if j in x.get('job_types'):
                        # Check if launcher is accepting jobs for this beamline
                        if site_tag:
                            if site_tag in x.get('site_tag'):
                                return (x.get('job_list'), x.get('launch_dir'))
                        else:
                            return (x.get('job_list'), x.get('launch_dir'))

        # Return False if no running launchers are appropriate
        return (False, False)

    def push_command(self, command):
        """
        Handle an incoming command

        Keyword arguments:
        command -- command from redis
        """
        print "push_command"
        #pprint(command)

        # Split up the command
        message = command
        if self.logger:
            self.logger.debug("Command received channel:RAPD_JOBS  message: %s", message)

        # get the site_tag from the image header to determine beamline where is was collected.
        site_tag = launch_tools.get_site_tag(message)

        # get the correct running launcher and launch_dir
        launcher, launch_dir = self.set_launcher(message['command'], site_tag)

        if message['command'].startswith('INTEGRATE'):
            print 'type: %s'%message['preferences']['xdsinp']

        if launcher:
            # Update preferences to be in server run mode
            if not message.get("preferences"):
                message["preferences"] = {}
            message["preferences"]["run_mode"] = "server"

            # Pass along the Launch directory
            if not message.get("directories"):
                message["directories"] = {}
            message["directories"]["launch_dir"] = launch_dir

            # Push the job on the correct launcher job list
            self.redis.lpush(launcher, json.dumps(message))
            if self.logger:
                self.logger.debug("Command sent channel:%s  message: %s", launcher, message)
        else:
            self.redis.lpush('RAPD_JOBS_WAITING', json.dumps(message))
            if self.logger:
                self.logger.debug("Could not find a running launcher for this job. Putting job on RAPD_JOBS_WAITING list")

    def connect_to_redis(self):
        """Connect to the redis instance"""
        redis_database = importlib.import_module('database.rapd_redis_adapter')

        self.redis_db = redis_database.Database(settings=self.site.CONTROL_DATABASE_SETTINGS)
        self.redis = self.redis_db.connect_to_redis()

def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """The Launch process for handling calls for
    computation"""
    parser = argparse.ArgumentParser(parents=[base_parser],
                                     description=commandline_description,
                                     conflict_handler='resolve')

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

    LAUNCHER_MANAGER = Launcher_Manager(site=SITE,
                                        logger=logger,
                                        overwatch_id=commandline_args.overwatch_id)

    try:
        time.sleep(100)
    except KeyboardInterrupt:
        LAUNCHER_MANAGER.stop()

if __name__ == "__main__":
    main()
