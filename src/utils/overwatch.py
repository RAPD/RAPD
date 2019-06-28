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
import os
import socket
from subprocess import Popen
import sys
import time
import uuid
import signal
import redis

# RAPD imports
import utils.commandline
import utils.site
import utils.text as text
from utils.text import json
from bson.objectid import ObjectId

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

    def register_OLD(self, custom_vars={}):
        """
        Register the process with the central db

        Keyword arguments:
        custom_vars - dict containing custom elements to put in redis database
        """

        # Get connection
        red = self.redis

        hostname = socket.gethostname()
        try:
            host_ip = socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            host_ip = "unknown"

        # Create an entry
        entry = {"ow_type":self.ow_type,
                 "host_ip":host_ip,
                 "hostname":hostname,
                 "ow_id":self.ow_id,
                 "start_time":time.time(),
                 "status":"initializing",
                 "timestamp":time.time()}

        # If custom_vars have been passed, add them
        entry.update(custom_vars)

        # Check for launchers
        launcher = entry.get('job_list', False)
        #print launcher

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

    def register(self, custom_vars={}):
        """
        Register the process with the central db

        Keyword arguments:
        custom_vars - dict containing custom elements to put in redis database
        """

        # Get connection
        red = self.redis

        hostname = socket.gethostname()
        try:
            host_ip = socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            host_ip = "unknown"

        # Create an entry
        entry = {"ow_type":self.ow_type,
                 "host_ip":host_ip,
                 "hostname":hostname,
                 #"ow_id":self.ow_id,
                 "ow_id":self.uuid,
                 "start_time":time.time(),
                 "status":"initializing",
                 "timestamp":time.time()}

        # If custom_vars have been passed, add them
        entry.update(custom_vars)

        # Check for launchers
        launcher = entry.get('job_list', False)

        # Wrap potential redis down
        try:
            # Put entry in the redis db
            #red.hmset("OW:"+self.uuid, entry)
            for k, v in entry.iteritems():
                red.hset("OW:"+self.uuid, k, v)

            # Expire the current entry in N seconds
            red.expire("OW:"+self.uuid, OVERWATCH_TIMEOUT)

            # Announce by publishing
            red.publish("OW:registering", json.dumps(entry))

            # If this process has an overwatcher
            if not self.ow_id == None:
                # Put entry in the redis db
                #red.hmset("OW:"+self.uuid+":"+self.ow_id, entry)
                for k, v in entry.iteritems():
                    red.hset("OW:"+self.uuid+":"+self.ow_id, k, v)

                # Expire the current entry in N seconds
                red.expire("OW:"+self.uuid+":"+self.ow_id, OVERWATCH_TIMEOUT)

            # Used by launch_manager to see which launchers are running.
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

            # Used by launch_manager to see which launchers are running.
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
        redis_database = importlib.import_module('database.redis_adapter')

        self.redis = redis_database.Database(settings=self.site.CONTROL_DATABASE_SETTINGS)

    def stop(self):
        """
        Stop the running process cleanly
        """
        #self.redis_database.stop()
        pass

class Overwatcher(Registrar):
    """
    Provides methods for starting and restarting microservices

    Passes an additional commandline flag that is the id of this Overwatcher
    via the --overwatch_id flag
    """

    ow_type = "overwatcher"
    ow_id = None
    ow_managed_id = None
    ow_managed_type = None
    run_process = True

    def __init__(self, site, managed_file, managed_file_flags):
        """
        Initialize and run the Overwatcher

        Keyword arguments:
        site -- site definition object
        managed_file -- RAPD file to be wrapped and started
        managed_file_flags -- flags to be passed to the managed file
        """

        # print "__init__"

        # Passed-in variables
        self.site = site
        self.managed_file = managed_file
        self.managed_file_flags = managed_file_flags

        # remove and save Python command
        i = self.managed_file_flags.index('--python')
        self.managed_file_flags.remove('--python')
        self.python_command = self.managed_file_flags.pop(i)

        # Create a unique id
        self.uuid = uuid.uuid4().hex

        # Run
        self.run()

    def run(self):
        """
        Orchestrate core functioning of the Overwatcher instance
        """

        # Just printing help info
        if "--help" in self.managed_file_flags:
            self.start_managed_process(help=True)

        # An actual run
        else:
            # Connect to redis
            self.connect()

            # Register self
            self.register()

            # Start microservice with self.uuid as overwatch id
            self.start_managed_process(help=True)

            # Register to kill the managed process on overwatch exit
            atexit.register(self.kill_managed_process)

            # Start listening for information on managed service and updating
            self.listen_and_update()

    def restart_managed_process(self):
        """
        Kill and then start the managed process
        """

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

        print "kill_managed_process"
        # Small wait to all children to terminate without errors.
        time.sleep(2)

        # Set flag that we do not want to restart the process
        self.run_process = False

        # Update the entry in redis
        self.update(custom_vars={"status":"killing"})

        self.managed_process.terminate()
        # 'kill' makes queues hangs because they cannot close.
        #self.managed_process.kill()
        # os.kill(self.managed_process.pid, signal.SIGKILL)

        # Forget the managed id
        self.ow_managed_id = None

        # Update the entry in redis
        self.update(custom_vars={"status":"stopped"})

    def start_managed_process(self, help=False):
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
        # print 'command: %s'%command

        # Update the entry in redis with the command being run
        if not help:
            self.update(custom_vars={"command":" ".join(command),
                                     "status":"starting"})

        # Run the input command
        self.managed_process = Popen(command, env=path)

        # Make sure the managed process actually ran
        time.sleep(0.5)
        exit_code = self.managed_process.poll()
        if exit_code != None:
            if not help:
                print text.error+"Managed process exited on start. Exiting."+text.stop
                self.update(custom_vars={"status":"error"})
            sys.exit(9)

        # Set flag that we do want to restart the process
        self.run_process = True

        # Update the entry in redis
        self.update(custom_vars={"status":"running"})

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

                # Get the managed process type
                if self.ow_managed_type == None:
                    self.ow_managed_type = self.get_managed_type()

                # Check the managed process status if a managed process is found
                if not self.ow_managed_id == None:
                    status = self.check_managed_process()

                    # Watched process has failed
                    if status == False:
                        # If we are supposed to run the process, run
                        if self.run_process == True:
                            self.restart_managed_process()

                # Check for an instruction
                self.check_for_instruction()

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

    def check_for_instruction(self):
        """
        Check for an instruction in the redis instance
        """

        # print "check_for_instruction"

        # Get connection
        red = self.redis

        # What's the time?
        now = time.time()

        try:
            # Get the instruction
            instruction = red.hgetall("OW:%s:instruction" % self.uuid)
        # There is no entry - do nothing
        except TypeError:
            return False
        # Redis is down - do nothing
        except redis.exceptions.ConnectionError:
            return False

        # If there is an instruction, delete it as we have retrieved it
        if instruction:
            red.delete("OW:%s:instruction" % self.uuid)
            print "Have instruction:", instruction
            if instruction["command"] == "stop":
                self.kill_managed_process()
            elif instruction["command"] == "start":
                self.start_managed_process()

    def get_managed_id(self):
        """
        Retrieve the managed process's ow_id
        """

        # Get connection
        red = self.redis

        # Look for keys
        # print "Looking for OW:*:%s" % self.uuid
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
            # print "Found it!"
            managed_id = keys[0].split(":")[1]
            # Update the entry in redis with the command being run
            self.update(custom_vars={"managed_id":managed_id})
            return managed_id

    def get_managed_type(self):
        """
        Retrieve the managed process's ow_type
        """

        # Get connection
        red = self.redis

        # Make sure we have a managed_id
        if not self.ow_managed_id:
            return None

        # Look for keys
        try:
            ow_type = red.hget("OW:%s" % self.ow_managed_id, "ow_type")
        # Redis is down - no keys to be found
        except redis.exceptions.ConnectionError:
            return None

        if ow_type:
            # Update the entry in redis with the command being run
            self.update(custom_vars={"managed_type":ow_type})

        return ow_type

def get_commandline():
    """
    Get the commandline variables and handle them
    """

    commandline_description = "Overwatch wrapper"

    parser = argparse.ArgumentParser(parents=[utils.commandline.base_parser],
                                     description=commandline_description,
                                     add_help=False)
    # Help
    parser.add_argument("--help", "-h",
                        action="store_true",
                        dest="help")

    parser.add_argument("--managed_file", "-f",
                        action="store",
                        dest="managed_file",
                        help="File to be overwatched")

    parser.add_argument("--python", "-p",
                        action="store",
                        default="rapd.python",
                        dest="python",
                        help="Which python to launch managed file")

    # parser.add_argument('rest', nargs=argparse.REMAINDER)

    # parsed_args = parser.parse_args()
    parsed_args, unknownargs = parser.parse_known_args()

    if parsed_args.help:
        parser.print_help()

    return parsed_args, unknownargs

def main():
    """Called when overwatch is run from the commandline"""

    # Get the commandline args
    parsed_args, unknownargs = get_commandline()

    # Make sure there is a managed_process in parsed_args
    if parsed_args.managed_file == None:
        print text.error+"Need a file to manage. Exiting.\n"+text.stop
        sys.exit(9)

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()
    # print environmental_vars

    if parsed_args.help:
        print "\n"
        SITE = None
    else:
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
        # print "  arg:%s  val:%s" % (arg, val)
        if arg != "managed_file":
            if val == True:
                parsed_args_list.append("--%s" % arg)
                continue
            if val == False:
                continue
            if val != None:
                parsed_args_list.append("--%s" % arg)
                parsed_args_list.append(str(val))

    # Add the args not understood by overwatch argparser
    parsed_args_list.extend(unknownargs)

    # Instantiate the Overwatcher
    OW = Overwatcher(site=SITE,
                     managed_file=parsed_args.managed_file,
                     managed_file_flags=parsed_args_list)

if __name__ == "__main__":

    main()
