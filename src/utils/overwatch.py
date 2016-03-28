"""
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

"""
Provides tools for registration, autodiscovery, monitoring and launching
"""

# Standard imports
import importlib
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

class Registrar(object):
    """Provides microservice monitoring tools"""

    def __init__(self):
        """
        Setup the Startover
        """
        pass

    def register(self):
        """
        Register the process with the central db
        """

        # Get connection
        red = redis.Redis(connection_pool=self.redis_pool)

        # Put entry in the redis db
        red.hmset("OW:"+self.id, {"ow_type":self.ow_type,
                                  "id":self.id,
                                  "ow_id":self.ow_id,
                                  "ts":time.time()})

        # Expire the current entry in 30 seconds
        red.expire("OW:"+self.id, 30)

        # If this process has an overwatcher
        if not self.ow_id == None:
            # Put entry in the redis db
            red.hmset("OW:"+self.id+":"+self.ow_id, {"ow_type":self.ow_type,
                                                     "id":self.id,
                                                     "ow_id":self.ow_id,
                                                     "ts":time.time()})

            # Expire the current entry in 30 seconds
            red.expire("OW:"+self.id+":"+self.ow_id, 30)

    def update(self):
        """
        Update the status with the central db
        """

        print "update"

        # Get connection
        red = redis.Redis(connection_pool=self.redis_pool)

        # Put entry in the redis db
        red.hset("OW:"+self.id, "ts", time.time())

        # Expire the current entry in 30 seconds
        red.expire("OW:"+self.id, 30)

        # If this process has an overwatcher
        if not self.ow_id == None:
            # Put entry in the redis db
            red.hset("OW:"+self.id+":"+self.ow_id, "ts", time.time())

            # Expire the current entry in 30 seconds
            red.expire("OW:"+self.id+":"+self.ow_id, 30)

    def connect(self):
        """
        Connect to the central redis Instance
        """

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
        Set up the Overwatcher
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
        command.append("--overwatch")
        command.append(self.id)

        print command

        subprocess.Popen(command, env=path)


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
                pass

            # Update the overwatcher status
            try:
                self.update()
                connection_errors = 0
            except redis.exceptions.ConnectionError:
                connection_errors += 1
                if connection_errors > 12:
                    print "Too many connection errors. Exiting."
                    break


    def get_managed_id(self):
        """
        Retrieve the managed process's ow_id
        """

        # Get connection
        red = redis.Redis(connection_pool=self.redis_pool)

        # Look for keys
        keys = red.keys("OW:*:%s" % self.ow_id)

        if len(keys) == 0:
            return None
        elif len(keys) > 1:
            return None
        else:
            return keys[0].split(":")[1]


    def start_microservice(self):
        """
        Start the microservice to be managed
        """
        pass

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
                    pass
                    #print "  Overwatcher script", entry

                if entry == "-s":
                    site = "SITENEXT"

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
    """
    The main process
    Instantiate the Overwatcher
    """

    # Get the commandline args
    site, managed_file, managed_file_flags = get_commandline()

    print site
    print managed_file
    print managed_file_flags

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()

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
