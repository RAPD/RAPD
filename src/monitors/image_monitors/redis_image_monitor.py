"""
Monitor for new data collection images to be submitted to a redis instance
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
__created__ = "2016-01-28"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import logging
import redis
import threading
import time
import importlib

# RAPD imports
from utils.overwatch import Registrar
# from utils import pysent

# Constants
POLLING_REST = 0.1      # Time to rest between checks for new image

class Monitor(threading.Thread):
    """Monitor for new data collection images to be submitted to a redis instance"""

    # Used for stopping/starting the loop
    running = True

    # The connection to the Redis database
    redis = None

    # Storage for where to look for information
    tags = []
    image_lists = []

    # Overwatch
    ow_registrar = None

    def __init__(self,
                 site,
                 notify=None,
                 overwatch_id=None):
        """
        Initialize the monitor

        Keyword arguments:
        site -- site description
        notify - Function called when image is captured
        overwatch_id -- id for optional overwather wrapper
        """

        # Get the logger
        self.logger = logging.getLogger("RAPDLogger")

        # Initialize the thread
        threading.Thread.__init__(self)

        # Passed-in variables
        self.site = site
        self.notify = notify
        self.overwatch_id = overwatch_id

        # Figure out tag(s)
        self.get_tags()

        # Start the thread
        self.daemon = True
        self.start()

    def get_tags(self):
        """Transform site.ID into tag[s] for image monitor"""

        # A string is input - one tag
        if isinstance(self.site.ID, str):
            self.tags = [self.site.ID.upper()]

        # Tuple or list
        elif isinstance(self.site.ID, tuple) or isinstance(self.site.ID, list):
            for site_id in self.site.ID:
                self.tags.append(site_id.upper())

        # Figure out where we are going to look
        for tag in self.tags:
            self.image_lists.append(("images_collected:"+tag, tag))

    def stop(self):
        """Stop the process of polling the redis instance"""

        self.logger.debug("Stopping")

        self.running = False
        self.redis_database.stop()

    def connect_to_redis(self):
        """Connect to the redis instance"""

        # Using a redis cluster setup
        # if settings["REDIS_CLUSTER"]:
        #     self.logger.debug(settings)
        #     self.redis = pysent.RedisManager(sentinel_host=settings["SENTINEL_HOST"],
        #                                      sentinel_port=settings["SENTINEL_PORT"],
        #                                      master_name=settings["REDIS_MASTER_NAME"])
        # # Using a standard redis server setup
        # else:

        # Create a pool connection
        """
        pool = redis.ConnectionPool(host=self.site.IMAGE_MONITOR_REDIS_HOST,
                                    port=self.site.IMAGE_MONITOR_REDIS_PORT,
                                    db=self.site.IMAGE_MONITOR_REDIS_DB)
        
        # The connection
        self.redis = redis.Redis(connection_pool=pool)
        """
        # Create a pool connection
        redis_database = importlib.import_module('database.rapd_redis_adapter')
        
        self.redis_database = redis_database.Database(settings=self.site.IMAGE_MONITOR_SETTINGS)
        if self.site.IMAGE_MONITOR_SETTINGS['REDIS_CONNECTION'] == 'pool':
            # For a Redis pool connection
            self.redis = self.redis_database.connect_redis_pool()
        else:
            # For a Redis sentinal connection
            self.redis = self.redis_database.connect_redis_manager_HA()

    def run(self):
        """Orchestrate the monitoring for new images in redis db"""

        self.logger.debug("Running")

        # Connect to Redis
        self.connect_to_redis()

        # Create Overwatch Registrar instance
        if self.overwatch_id:
            self.ow_registrar = Registrar(site=self.site,
                                          ow_type="control",
                                          ow_id=self.overwatch_id)
            # Register
            self.ow_registrar.register()

        # Determine interval for overwatch update
        ow_round_interval = 50 # int((5 * len(self.image_lists)) / POLLING_REST)

        while self.running:

            # ~5 seconds between overwatch updates
            for __ in range(ow_round_interval):

                for tag in self.tags:

                    # Try to pop the oldest image off the list
                    new_image = self.redis.rpop("images_collected:%s" % tag)
                    #new_image = self.redis.rpop("images_collected_%s" % tag)

                    # Have a new_image
                    if new_image:
                        self.logger.debug("New image %s - %s", tag, new_image)

                        # Notify core thread that an image has been collected
                        self.notify({"message_type":"NEWIMAGE",
                                     "fullname":new_image,
                                     "site_tag":tag})

                    # Slow it down a little
                    time.sleep(POLLING_REST)

            # Have Registrar update status
            if self.overwatch_id:
                self.ow_registrar.update()
