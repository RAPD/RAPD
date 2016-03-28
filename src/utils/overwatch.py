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
        red.hmset("OW:"+self.id, {"type":self.ow_type,
                                  "id":self.id,
                                  "ow_id":self.ow_id,
                                  "ts":time.time()})

        # Expire the current entry in 30 seconds
        red.expire("OW:"+self.id, 30)

    def update(self):
        """
        Update the status with the central db
        """

        # Get connection
        red = redis.Redis(connection_pool=self.redis_pool)

        # Put entry in the redis db
        red.hmset("OW:"+self.id, {"type":self.ow_type,
                                  "id":self.id,
                                  "ow_id":self.ow_id,
                                  "ts":time.time()})

        # Expire the current entry in 30 seconds
        red.expire("OW:"+self.id, 30)

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

    def __init__(self, site):
        """
        Set up the Overwatcher
        """

        # Passed-in variables
        self.site = site

        # Create a unique id
        self.id = uuid.uuid4()

    def run(self):
        """
        Orchestrate core functioning of the Overwatcher instance
        """

        # Connect to redis
        self.connect()

        # Register self
        self.register()

        # Start microservice with self.id as overwatch id

        # Start listening for information from

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
    print SITE

    #
    # # Have a GATHERER file
    # if hasattr(SITE, "GATHERER"):
    #
    #     # Run it
    #     subprocess.call("$RAPD_HOME/bin/rapd.python $RAPD_HOME/src/sites/gatherers/"+SITE.GATHERER+" -vs %s" % SITE.ID, shell=True)



if __name__ == "__main__":

    main()
