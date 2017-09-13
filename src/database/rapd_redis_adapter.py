"""
This is an adapter for RAPD to connect to the results database, when it is a
REDIS instance
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2009-2017, Cornell University
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
__created__ = "2016-05-31"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

"""
#To run a MongoDB instance in docker:
#sudo docker run --name mongodb -p 27017:27017 -d mongo:3.4
"""

# Standard imports
import datetime
import json
import logging
import os
import threading

from bson.objectid import ObjectId
import redis
from redis.sentinel import Sentinel

CONNECTION_ATTEMPTS = 30

class Database(object):
    """
    Provides connection to REDIS for Model.
    """

    client = None

    def __init__(self, settings):

        """
        Initialize the adapter

        Keyword arguments
        host --
        port --
        user --
        password --
        settings --
        """

        # Get the logger
        self.logger = logging.getLogger("RAPDLogger")

        # Store passed in variables
        # Using the settings "shorthand"

        # Used for a Redis connection pool
        self.redis_host = settings.get('REDIS_HOST', False)
        self.redis_port = settings.get('REDIS_PORT', False)
        self.redis_db = settings.get('REDIS_DB', False)

        # Used for a more reliable sentinal connection.
        self.sentinal_hosts = settings.get('REDIS_SENTINEL_HOSTS', False)
        self.sentinal_name = settings.get('REDIS_MASTER_NAME', False)

        if settings.get('REDIS_CONNECTION', False) == 'pool':
            self.pool = True
        else:
            self.pool = False
        
        # A lock for troublesome fast-acting data entry
        #self.LOCK = threading.Lock()
    def connect_to_redis(self):
        if self.pool:
            return self.connect_redis_pool()
        else:
            return self.connect_redis_manager_HA()

    def connect_redis_pool(self):
        # Create a pool connection
        pool = redis.ConnectionPool(host=self.redis_host,
                                    port=self.redis_port,
                                    db=self.redis_db)
        # Save the pool for a clean exit.
        self.pool = redis.Redis(connection_pool=pool)
        # The return the connection
        return self.pool
    
    def connect_redis_manager_HA(self):
        return (Sentinel(self.sentinal_hosts).master_for(self.sentinal_name))
    
    def stop(self):
        if self.pool:
            self.pool.close()
