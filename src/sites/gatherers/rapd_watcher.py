"""
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

import os
#import redis
import pysent
import time
import logging, logging.handlers
import pyinotify
from threading import Timer
import atexit
import threading

# Set up redis connection
#redPool = redis.ConnectionPool(host='164.54.212.169')
#red = redis.Redis(connection_pool=redPool)
red = pysent.RedisManager(sentinel_host="remote.nec.aps.anl.gov",
                          sentinel_port=26379,
                          master_name="remote_master")

#set up logging
LOG_FILENAME = '/tmp/runwatcher.log'
# Set up a specific logger with our desired output level
logger = logging.getLogger('RAPDLogger')
logger.setLevel(logging.DEBUG)

# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler(
          LOG_FILENAME, maxBytes=1000000, backupCount=5)
#add a formatter
formatter = logging.Formatter("%(asctime)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.debug("Logger started")



# Check for directory existence
def checkForDir(in_dir):
    logger.debug("Checking for %s existence" % in_dir)
    counter = 0
    while (counter < 120):
        if (os.path.isdir(in_dir)):
            return True
        else:
            logger.debug("%s does not exist" % in_dir)
            time.sleep(0.5)
            counter += 1
    return False

# Publish to Raj
def publish(pathname):
    red.publish('filecreate:C',pathname)

# Set up pyinotify
class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CREATE(self, event):
        logger.debug("%s has been created" % event.pathname)
        if (event.pathname.endswith('.cbf')):
            #red.lpush("images_collected_C",event.pathname)
            logger.debug("Image %s has been created" % event.pathname)
            #time.sleep(1)
            #red.publish('filecreate',event.pathname)

    def process_IN_MOVED_TO(self, event):
        #logger.debug("%s has been moved" % event.pathname)
        if (event.pathname.endswith('.cbf')):
            try:
                red.lpush("images_collected_C",event.pathname)
            except:
                logger.debug("ERROR: %s has not been sent to RAPD!!" % event.pathname)
            logger.debug("Image %s has been moved" % event.pathname)
            #red.publish('filecreate',event.pathname)
            t = Timer(1.0,publish,[event.pathname])
            t.start()
    def process_default(self, event):
        """Eventually, this method is called for all others types of events.
        This method can be useful when an action fits all events.
        """
        pass
        #logger.debug("%s" % str(event))


class DirectoryHandler(threading.Thread):
    """Handles a new directory to add
    """
    def __init__(self,current_dir,logger):

        logger.debug("DirectoryHandler.__init__ %s" % current_dir)

        self.current_dir = current_dir
        self.logger = logger

        threading.Thread.__init__(self)

        self.start()

    def run(self):

        have = False

        # Make sure we are not already watching this directory
        for wdd in dirs:
            if (wdd.has_key(self.current_dir)):
                have = True
                break

        if (not have):
            count = 0
            while (count < 5):
                if (checkForDir(self.current_dir)):
                    try:
                        wdd = wm.add_watch(self.current_dir, mask, rec=True, auto_add=True, quiet=False)
                        add_watch_descriptor(wdd,self.current_dir)
                        self.logger.debug("DirectoryHandler.run %s watch added" % self.current_dir)
                        # Minimize the number of dirs being watched
                        trim_dirs()
                        # Break out of the loop
                        break
                    except pyinotify.WatchManagerError, err:
                        logger.exception(err, err.wmd)
                        count = count + 1
                        time.sleep(1)
                else:
                    count += 1
                    logger.debug('ERROR!! %s will not be watched' % start_dir)
        else:
            logger.debug("Already watching %s" % current_dir)
        # time.sleep(0.5)


dirs = []
wm = pyinotify.WatchManager()  # Watch Manager
mask = pyinotify.ALL_EVENTS
#mask = pyinotify.IN_MOVED_TO | pyinotify.IN_CREATE  #pyinotify.IN_CREATE|pyinotify.IN_MOVED_TO  #CREATE  # watched events
notifier = pyinotify.ThreadedNotifier(wm, EventHandler())
notifier.start()

def exit_gracefully():
    logger.debug('Attempting to gracefully shut down')
    wm.rm_watch(wdd.values())
    notifier.stop()

atexit.register(exit_gracefully)

def add_watch_descriptor(wd,directory):
    if (wd):
        dirs.append(wd)
    else:
        logger.debug("Error adding watch for directory" % directory)

def trim_dirs():
    while len(dirs) > 20:
        remove_dir = dirs.pop(2)
        logger.debug('Removing %s from watched directories' % remove_dir)
        if remove_dir:
            wm.rm_watch(wdd[remove_dir], rec=True)
        else:
            logger.debug('Not removing watch %s is an empty watch descriptor' % str(wdd))
#for testing
#wdd = wm.add_watch('/tmp', mask, rec=True, auto_add=True)
#dirs.append(wdd)

#hardcode the analysis directory to watch - not appending dirs as it will not go away
try:
    DirectoryHandler('/gpfs5/users/necat/phi_raster_snap/in',logger)
except pyinotify.WatchManagerError, err:
    logger.exception(err, err.wmd)


try:
    DirectoryHandler('/gpfs5/users/necat/phi_dfa_1/in',logger)
except pyinotify.WatchManagerError, err:
        logger.exception(err, err.wmd)

try:
    DirectoryHandler('/gpfs5/users/necat/phi_dfa_scan_data',logger)
except pyinotify.WatchManagerError, err:
        logger.exception(err, err.wmd)

try:
    DirectoryHandler('/gpfs5/users/necat/phi_ova_scan_data',logger)
except pyinotify.WatchManagerError, err:
        logger.exception(err, err.wmd)

try:
    DirectoryHandler('/gpfs5/users/necat/phi_rastersnap_scan_data',logger)
except pyinotify.WatchManagerError, err:
        logger.exception(err, err.wmd)



#start by adding the current dir in the redis db
current_dir = ''
start_dir = red.get("datadir_C")
if (start_dir):
    logger.debug("Call to watch  %s from Redis memory store" % start_dir)
    current_dir = start_dir
    DirectoryHandler(current_dir,logger)
    """
    if (checkForDir(start_dir)):
        try:
            wdd = wm.add_watch(start_dir, mask, rec=True, auto_add=True, quiet=False)
            add_watch_descriptor(wdd,start_dir)
        except pyinotify.WatchManagerError, err:
            logger.exception(err, err.wmd)
    else:
        logger.debug('ERROR!! %s will not be watched' % start_dir)
    """

# Listen for new directory
current_dir = ''
time.sleep(0.5)
while True:
    try:
        #for payload in pubsub.listen():
        newdir = red.get('datadir_C')
        if (newdir):
          if (newdir != current_dir):
            have = False
            current_dir = newdir
            logger.debug('New directory to watch %s' % newdir)

            DirectoryHandler(newdir,logger)
        time.sleep(1)





    except:
        logger.exception('Error in main loop')
        #grab another redis connection - hoping this is the problem!
        red = redis.Redis(connection_pool=redPool)
