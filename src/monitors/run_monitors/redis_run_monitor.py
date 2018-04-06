"""
Monitor for new run descriptions submitted to a redis instance
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2016-2018 Cornell University
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
import sys
import threading
import time

#import redis
import importlib

# RAPD imports
from utils.overwatch import Registrar
from utils.text import json
from bson.objectid import ObjectId

# Constants
POLLING_REST = 1      # Time to rest between checks for new run data

class Monitor(threading.Thread):
    """Monitor for new data collection run to be submitted to a redis instance"""

    # For stopping/starting
    running = True

    # Connection to the Redis database
    redis = None

    # Storage for where to look for information
    tags = []
    run_lists = []

    # Overwatch
    ow_registrar = None

    def __init__(self,
                 site,
                 notify=None,
                 overwatch_id=None):
        """
        Initialize the RedisMonitor

        Keyword arguments:
        site -- site description
        notify - Function called when image is captured
        overwatch_id -- id for optional overwather wrapper
        """

        self.logger = logging.getLogger("RAPDLogger")

        # Initialize the thread
        threading.Thread.__init__(self)

        # Passed-in variables
        self.site = site
        self.notify = notify
        self.overwatch_id = overwatch_id

        # Figure out the site
        self.get_tags()

        # Start the thread
        # self.daemon = True
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
        for site_tag in self.tags:
            self.run_lists.append(("runs_data:"+site_tag, site_tag))

        self.logger.debug("run_lists: %s", str(self.run_lists))

    def stop(self):
        """Stop the process of polling the redis instance"""

        self.logger.debug("Stopping")

        self.running = False
        self.redis_database.stop()

    def connect_to_redis(self):
        """Connect to the redis instance"""
        redis_database = importlib.import_module('database.redis_adapter')

        self.redis_database = redis_database.Database(settings=self.site.RUN_MONITOR_SETTINGS)
        self.redis = self.redis_database.connect_to_redis()

    def run(self):
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
        # ow_round_interval = max(int((5 * len(self.run_lists)) / POLLING_REST), int(5/POLLING_REST))
        ow_round_interval = 10

        self.logger.debug("Finished registering %d", ow_round_interval)

        while self.running:

            # ~5 seconds between overwatch updates
            for __ in range(ow_round_interval):

                for run_list, site_tag in self.run_lists:

                    self.logger.debug("Querying %s %s", run_list, site_tag)
                    sys.exit()
                    # Try to pop the oldest image off the list
                    raw_run_data = self.redis.rpop(run_list)

                    # Have new run data
                    if raw_run_data != None:
                        # Parse into python object
                        run_data = json.loads(raw_run_data)

                        # Notify core thread that an image has been collected
                        self.notify({"message_type":"NEWRUN",
                                     "run_data":run_data,
                                     "site_tag":site_tag})

                        self.logger.debug("New run data %s", raw_run_data)

                    # Slow it down a little
                    time.sleep(POLLING_REST)
                time.sleep(POLLING_REST)

            # Have Registrar update status
            if self.overwatch_id:
                self.ow_registrar.update()
