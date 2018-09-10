"""
Monitors CONSOLE Redis instance for new directories to watch &
watches directories using pyinotify for new images.
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2012-2018, Cornell University
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

__created__ = "2012-02-07"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

import argparse
import atexit
import importlib
import logging
import logging.handlers
import os
import pyinotify
import socket
import sys
import threading
import time

# RAPD imports
from database.redis_adapter import Database
import utils.commandline as ucommandline
import utils.lock as ulock
import utils.log as ulog
from utils.overwatch import Registrar
import utils.site as usite
import utils.text as text

MASK = pyinotify.ALL_EVENTS
NUMBER_WATCHED = 20

# Pyinotify eventhandler


class EventHandler(pyinotify.ProcessEvent):
    """
    Process pyinotify events
    """

    def __init__(self, redis_rapd=None, redis_remote=None, logger=None):
        """
        Initialize the event handler with connections
        """

        self.redis_rapd = redis_rapd
        self.redis_remote = redis_remote
        self.logger = logger

    def process_IN_MOVED_TO(self, event):
        """
        This is the final step for a file being created
        """
        self.logger.debug("%s has been moved" % event.pathname)

        if event.pathname.endswith('.cbf'):
            # RAPD1
            self.redis_rapd.lpush("images_collected_C", event.pathname)
            self.redis_rapd.publish("image_collected_C", event.pathname)
            # RAPD2
            self.redis_rapd.lpush("images_collected:NECAT_C", event.pathname)
            self.redis_rapd.publish("image_collected:NECAT_C", event.pathname)
            # REMOTE
            self.redis_remote.publish("filecreate:C", event.pathname)

    def process_IN_DELETE_SELF(self, event):
        """
        A watched directory is deleted
        """
        self.logger.debug("%s has been deleted" % event.pathname)

    def process_default(self, event):
        """
        Eventually, this method is called for all other types of events.
        This method can be useful when an action fits all events.
        """
        pass
        #logger.debug("%s" % str(event))


class DirectoryHandler(threading.Thread):
    """
    Handles a new directory to add
    """

    def __init__(self, current_dir, watch_manager, logger):

        logger.debug("DirectoryHandler.__init__ %s" % current_dir)

        # Store variables
        self.current_dir = current_dir
        self.watch_manager = watch_manager
        self.logger = logger

        # Initialize thread
        threading.Thread.__init__(self)

        # GO!
        self.start()

    def run(self):

        def checkForDir(in_dir):
            """
            Check for directory existence on filesystem
            """
            self.logger.debug("Checking for %s existence" % in_dir)
            counter = 0
            while (counter < 120):
                if os.path.isdir(in_dir):
                    self.logger.debug("%s exists" % in_dir)
                    return True
                else:
                    self.logger.debug("%s does not exist" % in_dir)
                    time.sleep(0.5)
                    counter += 1
            return False

        # def trim_dirs(wdd):
        #     """
        #     Keep the watched directories reasonable in number
        #     """
        #     while len(dirs) > NUMBER_WATCHED:
        #         remove_dir = self.watched_dirs.pop(3)
        #         self.logger.debug("Removing %s from watched directories" % remove_dir)
        #         if remove_dir:
        #             self.watch_manager.rm_watch(wdd[remove_dir], rec=True)
        #         else:
        #             self.logger.debug('Not removing watch %s is an empty watch descriptor' % str(wdd))

        # Make sure we are not already watching this directory
        watch_descriptor = self.watch_manager.get_path(self.current_dir)
        if watch_descriptor:
            self.watch_manager.rm_watch(watch_descriptor)

        count = 0
        while (count < 5):
            if (checkForDir(self.current_dir)):
                try:
                    wdd = self.watch_manager.add_watch(
                        self.current_dir, MASK, rec=True, auto_add=True, quiet=False)
                    self.logger.debug(
                        "DirectoryHandler.run %s watch added" % self.current_dir)
                    # Minimize the number of dirs being watched
                    # trim_dirs(wdd=wdd)
                    # Break out of the loop
                    break
                except pyinotify.WatchManagerError, err:
                    self.logger.exception(err, err.wmd)
                    count = count + 1
                    time.sleep(1)
            else:
                count += 1
                self.logger.debug("ERROR!! %s will not be watched" % self.current_dir)


class Gatherer(object):
    """
    Watches the beamline and signals images and runs over redis
    """
    # For keeping track of file change times
    run_time = 0
    image_time = 0

    # Host computer detail
    ip_address = None

    def __init__(self, site, overwatch_id=None):
        """
        Setup and start the Gatherer
        """

        # Get the logger Instance
        self.logger = logging.getLogger("RAPDLogger")

        # Passed-in variables
        self.site = site
        self.overwatch_id = overwatch_id

        self.logger.info("Gatherer.__init__")

        # Get our bearings
        self.set_host()

        # Connect to redis
        self.connect()

        # Running conditions
        self.go = True

        # Now run
        self.run()

    def run(self):
        """
        The while loop for watching the files
        """
        self.logger.info("Gatherer.run")

        # Set up overwatcher
        self.ow_registrar = Registrar(site=self.site,
                                      ow_type="gatherer",
                                      ow_id=self.overwatch_id)
        self.ow_registrar.register({"site_id": self.site.ID})

        # A RUN & IMAGES EXAMPLE
        # Some logging
        self.logger.debug("  Will publish new images on filecreate:C")
        self.logger.debug("  Will publish new images on image_collected:C")
        self.logger.debug("  Will push new images onto images_collected:C")
        self.logger.debug(
            "  Will publish new images on image_collected:%s" % self.tag)
        self.logger.debug(
            "  Will push new images onto images_collected:%s" % self.tag)

        # Set up the WatchManager
        watch_manager = pyinotify.WatchManager()

        # Set up the notifier for files being made
        notifier = pyinotify.ThreadedNotifier(watch_manager, EventHandler(redis_rapd=self.redis_rapd,
                                                                          redis_remote=self.redis_remote,
                                                                          logger=self.logger))
        notifier.start()

        # Try exiting the pyinotify gracefully
        # def exit_gracefully():
        #     """
        #     Exit pyinotify properly when program exits
        #     """
        #     self.logger.debug("Attempting to gracefully shut down")
        #     watch_manager.rm_watch(wdd.values())
        #     notifier.stop()
        # atexit.register(exit_gracefully)

        # Start by adding the current dir in the beamline redis db
        DATA_DIR = "ADX_SUBDIR_SV"  # "datadir_%s" % self.tag

        # Listen for new directory
        current_dir = ""
        time.sleep(0.5)
        counter = 0
        try:
            while True:
                print counter
                newdir = self.redis_beamline.get(DATA_DIR)
                if (newdir != current_dir):
                    # have = False
                    current_dir = newdir
                    self.logger.debug("New directory to watch %s'" % newdir)
                    DirectoryHandler(current_dir=newdir,
                                     watch_manager=watch_manager,
                                     logger=self.logger)
                time.sleep(1)
                # Update overwatcher every 5 seconds
                if counter % 5 == 0:
                    self.ow_registrar.update({"site_id": self.site.ID})
                    counter = 0
                else:
                    counter += 1

        # Exited by keyboard
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """
        Stop the loop
        """
        self.logger.debug("Gatherer.stop")

        self.go = False

    def set_host(self):
        """
        Use os.uname to set files to watch
        """
        self.logger.debug("Gatherer.set_host")

        # Figure out which host we are on
        self.ip_address = socket.gethostbyaddr(socket.gethostname())[-1][0]
        self.logger.debug("IP Address: %s" % self.ip_address)

        # Now grab the file locations, beamline from settings
        if self.site.GATHERERS.has_key(self.ip_address):
            self.tag = self.site.GATHERERS[self.ip_address]
            # Make sure we enforce uppercase for tag
            self.tag = self.tag.upper()
        else:
            print "ERROR - no settings for this host"
            self.tag = "test"

    def connect(self):
        """
        Connect to redis host
        """

        self.logger.debug("Gatherer.connect")

        # Connect to RAPD Redis
        self.redis_rapd = Database(
            settings=self.site.CONTROL_DATABASE_SETTINGS)

        # NECAT uses Redis to communicate with the beamline
        # Connect to beamline Redis to monitor if run is launched
        self.redis_beamline = Database(
            settings=self.site.SITE_ADAPTER_SETTINGS[self.tag])

        # NECAT uses Redis to communicate with the remote system
        # Connect to remote system Redis to monitor if run is launched
        self.redis_remote = Database(
            settings=self.site.REMOTE_ADAPTER_SETTINGS)


def get_commandline():
    """
    Get the commandline variables and handle them
    """

    # Parse the commandline arguments
    commandline_description = "Data gatherer"
    parser = argparse.ArgumentParser(parents=[ucommandline.base_parser],
                                     description=commandline_description)

    return parser.parse_args()


def main():
    """ 
    The main process 
    Setup logging and instantiate the gatherer 
    """

    # Get the commandline args
    commandline_args = get_commandline()

    # Get the environmental variables
    environmental_vars = usite.get_environmental_variables()
    site = commandline_args.site

    # If no commandline site, look to environmental args
    if site == None:
        site = environmental_vars["RAPD_SITE"]

    # Determine the site
    site_file = usite.determine_site(site_arg=site)

    # Handle no site file
    if site_file == False:
        print text.error+"Could not determine a site file. Exiting."+text.stop
        sys.exit(9)

    # Import the site settings
    SITE = importlib.import_module(site_file)

    # Single process lock?
    ulock.file_lock(SITE.GATHERER_LOCK_FILE)

    # Set up logging
    if commandline_args.verbose:
        log_level = 10
    else:
        log_level = SITE.LOG_LEVEL
    logger = ulog.get_logger(logfile_dir="/tmp",
                             logfile_id="rapd_gatherer",
                             level=log_level
                             )
    logger.debug("Commandline arguments:")
    for pair in commandline_args._get_kwargs():
        logger.debug("  arg:%s  val:%s" % pair)

    # Instantiate the Gatherer
    GATHERER = Gatherer(site=SITE,
                        overwatch_id=commandline_args.overwatch_id)


if __name__ == "__main__":

    # Execute code
    main()
