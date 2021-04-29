"""
Monitor for new run descriptions submitted to a redis instance
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2016-2021 Cornell University
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

__created__ = "2021-04-28"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import importlib
import logging
from pprint import pprint
from threading import Thread
import time


# RAPD imports
from utils.overwatch import Registrar
from utils.text import json
from bson.objectid import ObjectId

# Constants

class Monitor(Thread):
    """Monitor for new request to be submitted to a redis instance"""

    # For stopping/starting
    running = True

    # Connection to the Redis database
    redis = None

    # Connection to database
    database = None

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
        notify - Function that can be called when request is received
        overwatch_id -- id for optional overwather wrapper
        """

        self.logger = logging.getLogger("RAPDLogger")

        # Initialize the thread
        Thread.__init__(self)

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
        """Transform site.ID into tag[s] for request monitor"""

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
        #self.redis_database.stop()

    def connect_to_redis(self):
        """Connect to the redis instance"""
        redis_database = importlib.import_module('database.redis_adapter')
        self.redis = redis_database.Database(settings=self.site.REQUEST_MONITOR_SETTINGS)

    def connect_to_database(self):
        """Set up database connection"""

        # Import the database adapter as database module
        # global database
        database = importlib.import_module('database.%s_adapter' % self.site.CONTROL_DATABASE)

        # Shorten it a little
        site = self.site

        # Instantiate the database connection
        if site.CONTROL_DATABASE_SETTINGS.get('DATABASE_STRING', False):
            self.database = database.Database(string=site.CONTROL_DATABASE_SETTINGS['DATABASE_STRING'])
        else:
            self.database = database.Database(host=site.CONTROL_DATABASE_SETTINGS['DATABASE_HOST'],
                                              #port=site.DATABASE_SETTINGS['DB_PORT'],
                                              user=site.CONTROL_DATABASE_SETTINGS['DATABASE_USER'],
                                              password=site.CONTROL_DATABASE_SETTINGS['DATABASE_PASSWORD'])
        #self.database = database.Database(string=site.CONTROL_DATABASE_SETTINGS['DATABASE_STRING'])
    
    def run(self):
        self.logger.debug("Running")

        # Connect to Redis
        self.connect_to_redis()

        # Connect to database
        self.connect_to_database()

        # Create Overwatch Registrar instance
        if self.overwatch_id:
            self.ow_registrar = Registrar(site=self.site,
                                          ow_type="control",
                                          ow_id=self.overwatch_id)
            # Register
            self.ow_registrar.register()

        # Determine interval for overwatch update
        ow_round_interval = 10

        self.logger.debug("Finished registering %d", ow_round_interval)

        while self.running:

            # ~5 seconds between overwatch updates
            for __ in range(ow_round_interval):

                request = self.redis.brpop(["RAPD2_REQUESTS",], 5)
                if request:
                    self.handle_request(request[1])

            # Have Registrar update status
            if self.overwatch_id:
                self.ow_registrar.update()

    def handle_request(self, request):
        """Handle requests received"""

        self.logger.debug("handle_request")      

        # Decode the request
        request = json.loads(request)

        # Send request to instantiating thread
        if self.notify:
            self.notify(request)

        # Handle understood requests here
        if request.get("request_type", None) == "DATA_PRODUCED":
            self.handle_data_produced_request(request)

        else:
            raise Exception("Unknown request type: %s", request.get("request_type", None))

    def handle_data_produced_request(self, request):
        """Handle a request for data produced"""

        self.logger.debug("handle_data_produced_request") 

        # Query for the data
        entry, content = self.database.retrieve_file(
            result_id=request.get("result_id"),
            description=request.get("description"),
            hash=request.get("hash"),
            )

        # Put reply together
        reply_data = entry["metadata"]
        reply_data["filename"] = entry["filename"]
        
        reply = json.dumps(reply_data) + "://:" + content

        # Send reply
        key = "RAPD2_DATA_REPLY_"+request.get("request_id")
        self.redis.set(key, reply)

        # Expire this key in 5 minutes
        self.redis.expire(key, 300)



if __name__ == "__main__":

    # Create an object to spoof site
    import types
    site = types.ModuleType('site', 'The site module')
    site.ID = "TEST"
    site.REQUEST_MONITOR_SETTINGS = {
        "REDIS_CONNECTION":     "direct",
        "REDIS_MASTER_NAME" :   None,
        "REDIS_HOST":           "127.0.0.1",
        "REDIS_PORT":           6379,
        "REDIS_DB":             0
    }
    site.CONTROL_DATABASE = "mongodb"
    site.CONTROL_DATABASE_SETTINGS = {"DATABASE_STRING": "mongodb://127.0.0.1:27017/rapd"}

    M = Monitor(site=site)