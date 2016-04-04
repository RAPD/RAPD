"""
Provides tools for registration, autodiscovery, monitoring and launching of RAPD
processes
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2016 Cornell University
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

__created__ = "2016-03-18"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import importlib
import json
import os
import subprocess
import sys
import time
import uuid

import redis

# RAPD imports
import utils.commandline
import utils.site
import utils.text as text

# Time in seconds for a process to be considered dead
OVERWATCH_TIMEOUT = 30

class Registrar(object):
    """Provides microservice monitoring tools"""

    def __init__(self, site=None, ow_type="unknown", ow_id=None):
        """
        Initialize the Registrar

        Keyword arguments:
        site -- site definition object
        ow_type -- type of process to be registered
        ow_id -- id for overwatcher that started the process to be registered
        """

        # Passed-in vars
        self.site = site
        self.ow_type = ow_type
        self.ow_id = ow_id

        # Create a unique id
        self.id = uuid.uuid4().hex

        # Connect to redis
        self.connect()

    def run(self):
        """
        Provides a generic registration and ongoing update of the instantiating
        process. Mainly for a test or example
        """

        # Register
        self.register()

        # Update every 5 seconds
        while True:
            time.sleep(5)
            self.update()

    def register(self, custom_vars={}):
        """
        Register the process with the central db

        Keyword arguments:
        custom_vars - dict containing custom elements to put in redis database
        """

        # Get connection
        red = redis.Redis(connection_pool=self.redis_pool)

        # Create an entry
        entry = {"ow_type":self.ow_type,
                 "id":self.id,
                 "ow_id":self.ow_id,
                 "timestamp":time.time()}

        # If custom_vars have been passed, add them
        entry.update(custom_vars)

        # Wrap potential redis down
        try:
            # Put entry in the redis db
            red.hmset("OW:"+self.id, entry)

            # Expire the current entry in N seconds
            red.expire("OW:"+self.id, OVERWATCH_TIMEOUT)

            # Announce by publishing
            red.publish("OW:registering", json.dumps(entry))

            # If this process has an overwatcher
            if not self.ow_id == None:
                # Put entry in the redis db
                red.hmset("OW:"+self.id+":"+self.ow_id, entry)

                # Expire the current entry in N seconds
                red.expire("OW:"+self.id+":"+self.ow_id, OVERWATCH_TIMEOUT)

        # Redis is down
        except redis.exceptions.ConnectionError:

            print "Redis appears to be down"

    def update(self, custom_vars={}):
        """
        Update the status with the central db

        Keyword arguments:
        custom_vars -- dict containing custom elements to put in redis database
        """

        # Get connection
        red = redis.Redis(connection_pool=self.redis_pool)

        # Create entry
        entry = {"ow_type":self.ow_type,
                 "id":self.id,
                 "ow_id":self.ow_id,
                 "timestamp":time.time()}

        # If custom_vars have been passed, add them
        entry.update(custom_vars)

        # Wrap potential redis down
        try:
            # Update timestamp
            red.hset("OW:"+self.id, "timestamp", time.time())

            # Update any custom_vars
            for k, v in custom_vars.iteritems():
                red.hset("OW:"+self.id, k, v)

            # Expire the current entry in N seconds
            red.expire("OW:"+self.id, OVERWATCH_TIMEOUT)

            # Announce by publishing
            red.publish("OW:updating", json.dumps(entry))

            # If this process has an overwatcher
            if not self.ow_id == None:
                # Put entry in the redis db
                red.hset("OW:"+self.id+":"+self.ow_id, "timestamp", time.time())

                # Update any custom_vars
                for k, v in custom_vars.iteritems():
                    red.hset("OW:"+self.id+":"+self.ow_id, k, v)

                # Expire the current entry in N seconds
                red.expire("OW:"+self.id+":"+self.ow_id, OVERWATCH_TIMEOUT)

        # Redis is down
        except redis.exceptions.ConnectionError:

            print "Redis appears to be down"

    def connect(self):
        """Connect to the central redis Instance"""

        self.redis_pool = redis.ConnectionPool(host=self.site.CONTROL_REDIS_HOST)

class Overwatcher(Registrar):
    """
    Provides methods for starting and restarting microservices

    Passes an additional commandline flag that is the id of this Overwatcher
    via the --overwatch flag
    """

    ow_type = "overwatcher"
    ow_id = None
    ow_managed_id = None

    def __init__(self, site, managed_file, managed_file_flags):
        """
        Initialize and run the Overwatcher

        Keyword arguments:
        site -- site definition object
        managed_file -- RAPD file to be wrapped and started
        managed_file_flags -- flags to be passed to the managed file
        """

        # Passed-in variables
        self.site = site
        self.managed_file = managed_file
        self.managed_file_flags = managed_file_flags

        # Create a unique id
        self.id = uuid.uuid4().hex

        # Run
        self.run()

    def run(self):
        """
        Orchestrate core functioning of the Overwatcher instance
        """

        # Connect to redis
        self.connect()

        # Register self
        self.register()

        # Start microservice with self.id as overwatch id
        self.start_managed_process()

        # Start listening for information on managed service and updating
        self.listen_and_update()

    def restart_managed_process(self):
        """
        Kill and then start the managed process
        """

        # Forget the previous id
        self.ow_managed_id = None

        # Kill
        self.managed_process.kill()

        # Wait
        time.sleep(2)

        # Start
        self.start_managed_process()

    def start_managed_process(self):
        """
        Start the managed process with the passed in flags and the current
        environment
        """

        # The environmental_vars
        path = os.environ.copy()

        # Put together the command
        command = self.managed_file_flags[:]
        command.insert(0, self.managed_file)
        command.insert(0, "rapd.python")
        command.append("--overwatch")
        command.append(self.id)

        # Run the input command
        self.managed_process = subprocess.Popen(command, env=path)

    def listen_and_update(self):
        """
        Listen for information on the managed process and maintain updates on
        self
        """

        connection_errors = 0

        while True:
            time.sleep(5)

            # Get the managed process ow_id if unknown
            if self.ow_managed_id == None:
                self.ow_managed_id = self.get_managed_id()

            # Check the managed process status if a managed process is found
            if not self.ow_managed_id == None:
                status = self.check_managed_process()

                # Watched process has failed
                if status == False:
                    self.restart_managed_process()

            # Update the overwatcher status
            try:
                self.update()
                connection_errors = 0
            # Redis is down
            except redis.exceptions.ConnectionError:
                connection_errors += 1
                if connection_errors > 12:
                    print "Too many connection errors. Exiting."
                    break


    def check_managed_process(self):
        """
        Check the managed process's status
        """

        # Get connection
        red = redis.Redis(connection_pool=self.redis_pool)

        # What's the time?
        now = time.time()

        try:
            managed_process_timestamp = float(red.hget("OW:%s" % self.ow_managed_id, "timestamp"))
        # There is no entry for the managed process - it has TTLed
        except TypeError:
            return False
        # Redis is down - default to not doing anything
        except redis.exceptions.ConnectionError:
            return True

        # Calculate time ellapsed since last update of status
        ellapsed = now - managed_process_timestamp

        # If too long, return False
        if ellapsed > OVERWATCH_TIMEOUT:
            return False
        else:
            return True

    def get_managed_id(self):
        """
        Retrieve the managed process's ow_id
        """

        # Get connection
        red = redis.Redis(connection_pool=self.redis_pool)

        # Look for keys
        print "Looking for OW:*:%s" % self.id
        try:
            keys = red.keys("OW:*:%s" % self.id)
        # Redis is down - no keys to be found
        except redis.exceptions.ConnectionError:
            return None

        if len(keys) == 0:
            return None
        elif len(keys) > 1:
            return None
        else:
            return keys[0].split(":")[1]




def get_commandline():
    """
    Get the commandline variables and handle them

    This is a manual handling of the commandline, no tthe typical RAPD style
    The commandline MUST BE
    >... [../]overwatch.py -s site managed_file managed_file_flags
    """

    managed_file = False
    site = False
    managed_file_flags = []

    # Go through the command line
    for entry in sys.argv:

        # No managed file yet
        if not managed_file:

            # site == False
            if not site:

                # The overwatch script
                if entry.endswith("overwatch.py"):
                    continue
                    #print "  Overwatcher script", entry

                if entry == "-s":
                    site = "SITENEXT"
                    continue

                # No site specification, straight to managed file
                if entry.endswith(".py"):
                    managed_file = entry

            # site is the current entry
            elif site == "SITENEXT":
                site = entry

            # managed_file is entry
            else:
                managed_file = entry

        # Have the managed file, rest is for it
        else:
            managed_file_flags.append(entry)

    print "  site:", site
    print "  managed_file:", managed_file
    print "  managed_file_flags:", managed_file_flags

    return site, managed_file, managed_file_flags

def main():
    """Called when overwatch is run from the commandline"""

    # Get the commandline args
    site, managed_file, managed_file_flags = get_commandline()

    print site
    print managed_file
    print managed_file_flags

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()

    if site == False:
        if environmental_vars["RAPD_SITE"]:
            site = environmental_vars["RAPD_SITE"]

    # Determine the site
    site_file = utils.site.determine_site(site_arg=site)
    if site_file == False:
        print text.error+"Could not determine a site file. Exiting."+text.stop
        sys.exit(9)

    # Import the site settings
    SITE = importlib.import_module(site_file)

    # Instantiate the Overwatcher
    OW = Overwatcher(site=SITE,
                     managed_file=managed_file,
                     managed_file_flags=managed_file_flags)


if __name__ == "__main__":

    main()
