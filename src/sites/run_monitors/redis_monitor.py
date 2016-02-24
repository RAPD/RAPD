"""
This file is part of RAPD

Copyright (C) 2016, Cornell University
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

import logging
import threading
import time
import redis

# RAPD imports
import pysent

class RedisMonitor(threading.Thread):
    """Monitor for new data collection images to be submitted to a redis instance"""

    # For stopping/starting
    Go = True

    # Connection to the Redis database
    redis = None

    def __init__(self, tag="necat_e", run_monitor_settings=None, notify=None, reconnect=None):
        """Initialize the object

        Keyword arguments:
        tag -- Expected tag for images to be captured (default "necat_e")
        redis_settings -- Dict with appropriate redis settings
        notify - Function called when image is captured
        reconnect --
        """

        self.logger = logging.getLogger("RAPDLogger")
        self.logger.debug("Starting")

        # Initialize the thread
        threading.Thread.__init__(self)

        # Passed-in variables
        self.tag = tag
        self.redis_settings = run_monitor_settings
        self.notify = notify
        self.reconnect = reconnect

        # Start the thread
        self.daemon = True
        self.start()

    def stop(self):
        """Stop the process of polling the redis instance"""

        self.logger.debug('Stopping')

        self.Go = False

    def connect_to_redis(self):
        """Connect to the redis instance"""

        # Make it easier to call var
        settings = self.redis_settings

        # Using a redis cluster setup
        if settings["REDIS_CLUSTER"]:
            self.logger.debug(settings)
            self.redis = pysent.RedisManager(sentinel_host=settings["SENTINEL_HOST"],
                                             sentinel_port=settings["SENTINEL_PORT"],
                                             master_name=settings["REDIS_MASTER_NAME"])
        # Using a standard redis server setup
        else:
            self.redis = redis.Redis(settings["REDIS_HOST"])

    def run(self):
        self.logger.debug('Running')

        # Connect to Redis
        self.connect_to_redis()

        image_list = "images_collected_"+self.tag
        while self.Go:
            # Try to pop the oldest image off the list
            new_image = self.redis.rpop(image_list)
            if new_image:
                # Notify core thread that an image has been collected
                self.notify(("NEWIMAGE", new_image))
                self.logger.debug('New image %s', new_image)

            # Slow it down a little
            time.sleep(0.1)
