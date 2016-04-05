"""
Monitor for new data collection images to be submitted to a redis instance
"""

__license__ = """
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

# Standard imports
import logging
import threading
import time

import redis

# RAPD imports
from utils.overwatch import Registrar
from utils import pysent

# Constants
POLLING_REST = 0.1      # Time to rest between checks for new image

class Monitor(threading.Thread):
    """Monitor for new data collection images to be submitted to a redis instance"""

    # Used for stopping/starting the loop
    Go = True

    # The connection to the Redis database
    redis = None

    def __init__(self,
                 site,
                #  tag=None,
                #  image_monitor_settings=None,
                 notify=None,
                 overwatch_id=None):
        """
        Initialize the monitor

        Keyword arguments:
        tag -- Expected tag for images to be captured (default "necat_e")
        redis_settings -- Dict with appropriate redis settings
        notify - Function called when image is captured
        overwatch_id -- id for optional overwather wrapper
        """

        # Get the logger
        self.logger = logging.getLogger("RAPDLogger")

        # Initialize the thread
        threading.Thread.__init__(self)

        # Passed-in variables
        # self.tag = tag.lower()
        # self.redis_settings = image_monitor_settings
        self.site=site
        self.notify = notify
        self.overwatch_id=overwatch_id

        # Tag comes from site id
        self.tag = self.site.ID.lower()

        # Start the thread
        self.daemon = True
        self.start()

    def stop(self):
        """Stop the process of polling the redis instance"""

        self.logger.debug('Stopping')

        self.Go = False

    def connect_to_redis(self):
        """Connect to the redis instance"""

        # Make it easier to call
        settings = self.site.IMAGE_MONITOR_SETTINGS

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
        """Orchestrate the monitoring for new images in redis db"""

        self.logger.debug("Running")

        # Create Registrar instance
        self.ow_registrar = Registrar(site=self.site,
                                      ow_type="control",
                                      ow_id=self.overwatch_id)
        # Register
        self.ow_registrar.register({"site_id":self.site.ID})

        # Connect to Redis
        self.connect_to_redis()

        self.logger.debug("  Monitoring list images_collected:"+self.tag)

        image_list = "images_collected:"+self.tag
        while self.Go:

            # 50 rounds between updating overwatch system
            for __ in range(50):

                # Try to pop the oldest image off the list
                new_image = self.redis.rpop(image_list)
                if new_image:
                    # Notify core thread that an image has been collected
                    self.notify(("NEWIMAGE", new_image))
                    self.logger.debug('New image %s', new_image)

                # Slow it down a little
                time.sleep(POLLING_REST)

            # Have Registrar update status
            self.ow_registrar.update({"site_id":self.site.ID})
