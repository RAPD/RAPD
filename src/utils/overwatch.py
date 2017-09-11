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
import argparse
import atexit
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
        self.uuid = uuid.uuid4().hex

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
        #red = redis.Redis(connection_pool=self.redis_pool)
        red = self.redis

        # Create an entry
        entry = {"ow_type":self.ow_type,
                 "id":self.uuid,
                 "ow_id":self.ow_id,
                 "timestamp":time.time()}

        # If custom_vars have been passed, add them
        entry.update(custom_vars)

        # Check for launchers
        launcher = entry.get('job_list', False)

        # Wrap potential redis down
        try:
            # Put entry in the redis db
            red.hmset("OW:"+self.uuid, entry)

            # Expire the current entry in N seconds
            red.expire("OW:"+self.uuid, OVERWATCH_TIMEOUT)

            # Announce by publishing
            red.publish("OW:registering", json.dumps(entry))

            # If this process has an overwatcher
            if not self.ow_id == None:
                # Put entry in the redis db
                red.hmset("OW:"+self.uuid+":"+self.ow_id, entry)

                # Expire the current entry in N seconds
                red.expire("OW:"+self.uuid+":"+self.ow_id, OVERWATCH_TIMEOUT)
            
            # Used to monitor which launchers are running.
            if launcher:
                # Put entry in the redis db
                red.set("OW:"+launcher, 1)
                
                # Expire the current entry in N seconds
                red.expire("OW:"+launcher, OVERWATCH_TIMEOUT)

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
        #red = redis.Redis(connection_pool=self.redis_pool)
        red = self.redis

        # Create entry
        entry = {"ow_type":self.ow_type,
                 "id":self.uuid,
                 "ow_id":self.ow_id,
                 "timestamp":time.time()}

        # If custom_vars have been passed, add them
        entry.update(custom_vars)

        # Check for launchers
        launcher = entry.get('job_list', False)

        # Wrap potential redis down
        try:
            # Update timestamp
            red.hset("OW:"+self.uuid, "timestamp", time.time())

            # Update any custom_vars
            for k, v in custom_vars.iteritems():
                red.hset("OW:"+self.uuid, k, v)

            # Expire the current entry in N seconds
            red.expire("OW:"+self.uuid, OVERWATCH_TIMEOUT)

            # Announce by publishing
            red.publish("OW:updating", json.dumps(entry))

            # If this process has an overwatcher
            if not self.ow_id == None:
                # Put entry in the redis db
                red.hset("OW:"+self.uuid+":"+self.ow_id, "timestamp", time.time())

                # Update any custom_vars
                for k, v in custom_vars.iteritems():
                    red.hset("OW:"+self.uuid+":"+self.ow_id, k, v)

                # Expire the current entry in N seconds
                red.expire("OW:"+self.uuid+":"+self.ow_id, OVERWATCH_TIMEOUT)
            
            # Used to monitor which launchers are running.
            if launcher:
                # Put entry in the redis db
                red.set("OW:"+launcher, 1)
                
                # Expire the current entry in N seconds
                red.expire("OW:"+launcher, OVERWATCH_TIMEOUT)

        # Redis is down
        except redis.exceptions.ConnectionError:

            print "Redis appears to be down"

    def connect(self):
        """Connect to the central redis Instance"""
        redis_database = importlib.import_module('database.rapd_redis_adapter')

        self.redis_database = redis_database.Database(settings=self.site.CONTROL_DATABASE_SETTINGS)
        self.redis = self.redis_database.connect_to_redis()

    def stop(self):
        """Stop the running process cleanly"""
        self.redis_database.stop()

class Overwatcher(Registrar):
    """
    Provides methods for starting and restarting microservices

    Passes an additional commandline flag that is the id of this Overwatcher
    via the --overwatch_id flag
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

        # remove and save Python command
        i = self.managed_file_flags.index('--python')
        self.managed_file_flags.remove('--python')
        self.python_command = self.managed_file_flags.pop(i)

        print site
        print managed_file
        print managed_file_flags

        # Create a unique id
        self.uuid = uuid.uuid4().hex

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

        # Start microservice with self.uuid as overwatch id
        self.start_managed_process()

        # Register to kill the managed process on overwatch exit
        atexit.register(self.kill_managed_process)

        # Start listening for information on managed service and updating
        self.listen_and_update()

    def restart_managed_process(self):
        """
        Kill and then start the managed process
        """

        # Forget the previous id
        self.ow_managed_id = None

        # Kill
        self.kill_managed_process()

        # Wait
        time.sleep(2)

        # Start
        self.start_managed_process()

    def kill_managed_process(self):
        """
        Kill the managed process
        """

        self.managed_process.kill()

    def start_managed_process(self):
        """
        Start the managed process with the passed in flags and the current
        environment. If the process exits immediately, the overwatcher will exit
        """
        # The environmental_vars
        path = os.environ.copy()

        # Put together the command
        command = self.managed_file_flags[:]
        command.insert(0, self.managed_file)
        command.insert(0, self.python_command)
        command.append("--overwatch_id")
        command.append(self.uuid)
        print 'command: %s'%command

        # Run the input command
        self.managed_process = subprocess.Popen(command, env=path)

        # Make sure the managed process actually ran
        time.sleep(0.5)
        exit_code = self.managed_process.poll()
        if exit_code != None:
            print text.error+"Managed process exited on start. Exiting."+text.stop
            sys.exit(9)

    def listen_and_update(self):
        """
        Listen for information on the managed process and maintain updates on
        self
        """

        connection_errors = 0
        try:
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
        except KeyboardInterrupt:
            pass

    def check_managed_process(self):
        """
        Check the managed process's status
        """

        # Get connection
        #red = redis.Redis(connection_pool=self.redis_pool)
        red = self.redis

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
        #red = redis.Redis(connection_pool=self.redis_pool)
        red = self.redis

        # Look for keys
        print "Looking for OW:*:%s" % self.uuid
        try:
            keys = red.keys("OW:*:%s" % self.uuid)
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
    """

    commandline_description = "Overwatch wrapper"

    parser = argparse.ArgumentParser(parents=[utils.commandline.base_parser],
                                     description=commandline_description)

    parser.add_argument("--managed_file", "-f",
                        action="store",
                        dest="managed_file",
                        help="File to be overwatched")
    parser.add_argument("--python", "-p",
                        action="store",
                        default="rapd.python",
                        dest="python",
                        help="Which python to launch managed file")
    parsed_args = parser.parse_args()

    return parsed_args

def main():
    """Called when overwatch is run from the commandline"""

    # Get the commandline args
    parsed_args = get_commandline()

    # Make sure there is a managed_process in parsed_args
    if parsed_args.managed_file == None:
        print text.error+"Need a file to manage. Exiting.\n"+text.stop
        sys.exit(9)

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()
    print environmental_vars

    # Environmental var for site if no commandline
    site = parsed_args.site
    if site == None:
        if environmental_vars.has_key("RAPD_SITE"):
            site = environmental_vars["RAPD_SITE"]

    # Determine the site
    site_file = utils.site.determine_site(site_arg=site)
    if site_file == False:
        print text.error+"Could not determine a site file. Exiting."+text.stop
        sys.exit(9)

    # Import the site settings
    print "Importing %s" % site_file
    SITE = importlib.import_module(site_file)

    # Create a list from the parsed_args
    parsed_args_list = []
    for arg, val in parsed_args._get_kwargs():
        print "  arg:%s  val:%s" % (arg, val)
        if arg != "managed_file":
            if val == True:
                parsed_args_list.append("--%s" % arg)
                continue
            if val == False:
                continue
            if val != None:
                parsed_args_list.append("--%s" % arg)
                parsed_args_list.append(str(val))

    # Instantiate the Overwatcher
    OW = Overwatcher(site=SITE,
                     managed_file=parsed_args.managed_file,
                     managed_file_flags=parsed_args_list)


if __name__ == "__main__":

    main()
