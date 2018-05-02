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

import atexit
import logging, logging.handlers
import os
import pyinotify
import threading
from threading import Timer
import time

# RAPD imports
from database.redis_adapter import Database as RedisDB

# Set up redis connection
HOSTS = (("164.54.212.170", 26379),
         ("164.54.212.172", 26379),
         ("164.54.212.169", 26379),
         ("164.54.212.165", 26379),
         ("164.54.212.166", 26379)
        )
MASTER_NAME = "remote_master"

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
        self.ow_registrar.register({"site_id":self.site.ID})

        # A RUN ONLY EXAMPLE
        # Some logging
        self.logger.debug("  Will publish new datasets on run_data:%s" % self.tag)
        self.logger.debug("  Will push new datasets onto runs_data:%s" % self.tag)

        try:
            counter = 0
            while self.go:

                # NECAT uses a beamline Redis database to communicate
                #----------------------------------------------------

                # Check if the run info changed in beamline Redis DB.
                current_run_raw = self.redis_beamline.get("RUN_INFO_SV")

                # New run information
                if current_run_raw not in (None, ""):
                    # Blank out the Redis entry
                    self.redis_beamline.set("RUN_INFO_SV", "")
                    # Handle the run information
                    self.handle_run(run_raw=current_run_raw)

                # Have Registrar update status
                if counter % 5 == 0:
                    self.ow_registrar.update({"site_id":self.site.ID})
                    counter = 0

                # Increment counter
                counter += 1

                # Pause
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

        # A RUN & IMAGES EXAMPLE
        # Some logging
        self.logger.debug("  Will publish new images on filecreate:%s" % self.tag)
        self.logger.debug("  Will push new images onto images_collected:%s" % self.tag)
        self.logger.debug("  Will publish new datasets on run_data:%s" % self.tag)
        self.logger.debug("  Will push new datasets onto runs_data:%s" % self.tag)

            while self.go:

                # 5 rounds of checking
                for ___ in range(5):
                    # An example of file-based signalling
                    # Check if the run info has changed on the disk
                    if self.check_for_run_info():
                        run_data = self.get_run_data()
                        if run_data:
                        # Handle the run information
                        self.handle_run(run_raw=current_run_raw)

                        # 20 image checks
                        for __ in range(20):
                            # Check if the image file has changed
                            if self.check_for_image_collected():
                                image_name = self.get_image_data()
                                if image_name:
                                    self.handle_image(image_name)
                                break
                            else:
                                time.sleep(0.05)
    def stop(self):
        """
        Stop the loop
        """
        self.logger.debug("Gatherer.stop")

        self.go = False
        self.redis_database.stop()
        self.bl_database.stop()

    def set_host(self):
        """
        Use os.uname to set files to watch
        """
        self.logger.debug("Gatherer.set_host")

        # Figure out which host we are on
        self.ip_address = socket.gethostbyaddr(socket.gethostname())[-1][0]
        self.logger.debug("IP Address:",self.ip_address)

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
        self.redis_rapd = RedisDB(settings=self.site.CONTROL_DATABASE_SETTINGS)

        # NECAT uses Redis to communicate with the beamline
        # Connect to beamline Redis to monitor if run is launched
        # self.redis_beamline = RedisDB(settings=self.site.SITE_ADAPTER_SETTINGS[self.tag])

        # NECAT uses Redis to communicate with the remote system
        # Connect to remote system Redis to monitor if run is launched
        # self.redis_beamline = RedisDB(settings=self.site.REMOTE_ADAPTER_SETTINGS)

    handle_run(self, run_raw):
        """
        Handle the raw run information
        """

        # Run information is encoded in JSON format
        run_data = json.loads(current_run_raw)

        # Determine if the run should be ignored

        # If you need to manipulate the run information or add to it, here's the place

        # Put into exchangable format
        run_data_json = json.dumps(run_data)

        # Publish to Redis
        self.redis.publish("run_data:%s" % self.tag, run_data_json)

        # Push onto redis list in case no one is currently listening
        self.redis.lpush("runs_data:%s" % self.tag, run_data_json)

    handle_image(self, image_name):
        """
        Handle a new image
        """

        self.logger.debug("image_collected:%s %s",
                          self.tag,
                          image_name)

        # Publish to Redis
        red.publish("image_collected:%s" % self.tag, image_name)

        # Push onto redis list in case no one is currently listening
        red.lpush("images_collected:%s" % self.tag, image_name)

    # Used for file-based image example
    def check_for_image_collected(self):
        """
        Returns True if image information file has new timestamp, False if not
        """

        tries = 0
        while tries < 5:
            try:
                statinfo = os.stat(self.image_data_file)
                break
            except:
                if tries == 4:
                    return False
                time.sleep(0.01)
                tries += 1

        # The modification time has not changed
        if self.image_time == statinfo.st_mtime:
            return False
        # The file has changed
        else:
            self.image_time = statinfo.st_mtime
            return True

def get_commandline():
    """
    Get the commandline variables and handle them
    """

    # Parse the commandline arguments
    commandline_description = "Data gatherer"
    parser = argparse.ArgumentParser(parents=[utils.commandline.base_parser],
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
    environmental_vars = utils.site.get_environmental_variables() 
    site = commandline_args.site 

    # If no commandline site, look to environmental args 
    if site == None: 
        if environmental_vars["RAPD_SITE"]: 
            site = environmental_vars["RAPD_SITE"] 

    # Determine the site 
    site_file = utils.site.determine_site(site_arg=site) 

    # Handle no site file 
    if site_file == False: 
        print text.error+"Could not determine a site file. Exiting."+text.stop
        sys.exit(9) 

    # Import the site settings 
    SITE = importlib.import_module(site_file) 

    # Single process lock? 
    utils.lock.file_lock(SITE.GATHERER_LOCK_FILE) 

    # Set up logging 
    if commandline_args.verbose: 
        log_level = 10 
    else: 
        log_level = SITE.LOG_LEVEL 
    logger = utils.log.get_logger(logfile_dir=SITE.LOGFILE_DIR, 
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


###############################################################################
###############################################################################


# Connect to sentinel
sentinel = Sentinel(HOSTS)

# Connect to master 
red = sentinel.master_for(MASTER_NAME)

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
def publish(pathname, tries=10):
    error_count = 0
    while error_count < tries:
        try:
            red.publish("filecreate:C", pathname)
            break
        except redis.exceptions.ConnectionError:
            logger.error("Connection error in publish")
            error_count += 1
            time.sleep(1)

# Set up pyinotify
class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CREATE(self, event):
        logger.debug("%s has been created" % event.pathname)
        if (event.pathname.endswith('.cbf')):
            logger.debug("Image %s has been created" % event.pathname)

    def process_IN_MOVED_TO(self, event):
        #logger.debug("%s has been moved" % event.pathname)
        if (event.pathname.endswith('.cbf')):
            # LPUSH onto redis for RAPD
            error_count = 0
            while error_count < 10:
                try:
                    red.lpush("images_collected_C", event.pathname)
                    # RAPD2
                    red.lpush("images_collected:NECAT_C", event.pathname)
                    break
                except redis.ConnectionError:
                    logger.error("%s has not been sent to RAPD!!" % event.pathname)
                    error_count += 1
                    time.sleep(1)

            logger.debug("Image %s has been moved" % event.pathname)
            t = Timer(1.0, publish, [event.pathname])
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
    print "add_watch_descriptor",wd,directory
    if (wd):
        dirs.append(wd)
    else: 
        print "Not adding"
        #logger.debug("Error adding watch for directory" % directory)

def trim_dirs():
    while len(dirs) > 20:
        remove_dir = dirs.pop(2)
        logger.debug('Removing %s from watched directories' % remove_dir)
        if remove_dir:
            wm.rm_watch(wdd[remove_dir], rec=True)
        else:
            logger.debug('Not removing watch %s is an empty watch descriptor' % str(wdd))

# Start by adding the current dir in the redis db
start_dir = False
error_count = 0
while error_count < 10:
    try:
        start_dir = red.get("datadir_C")
        break
    except redis.ConnectionError:
        print "Connection Error in get %d" % counter
        error_count += 1
        time.sleep(1)

current_dir = ''
if (start_dir):
    logger.debug("Call to watch  %s from Redis memory store" % start_dir)
    current_dir = start_dir
    DirectoryHandler(current_dir, logger)

# Listen for new directory
current_dir = ''
time.sleep(0.5)
while True:
    newdir = False
    error_count = 0
    while error_count < 10:
        try:
            newdir = red.get("datadir_C")
            break
        except redis.ConnectionError:
            logger.error("Connection Error in get %d" % counter)
            error_count += 1
            time.sleep(1)
    if newdir:
        if (newdir != current_dir):
            have = False
            current_dir = newdir
            logger.debug('New directory to watch %s' % newdir)
            DirectoryHandler(newdir, logger)
    time.sleep(1)
