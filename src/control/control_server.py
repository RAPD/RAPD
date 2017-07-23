"""
Provides tools for interface between the control process and launched processes
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
__created__ = "2009-07-10"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

# Standard imports
import json
import logging
#import redis
import importlib
import socket
import threading
import time

BUFFER_SIZE = 8192

class ControllerServer(threading.Thread):
    """
    Runs the socket server and spawns new threads when connections are received
    """

    Go = True

    def __init__(self, receiver, site):
        """
        The main server thread
        """
        # Get the logger
        self.logger = logging.getLogger("RAPDLogger")

        # Initialize the thred
        threading.Thread.__init__(self)

        # Store passed-in variables
        self.receiver = receiver
        self.site = site

        # Connect to redis
        self.connect_to_redis()

        # Start it up
        # self.daemon = True
        self.start()

    def run(self):


        # This is the "server"
        while self.Go:

            channel, message = self.redis.brpop(["RAPD_RESULTS"])

            print channel, message

            self.receiver(json.loads(message))

    def stop(self):
        self.logger.debug("Received signal to stop")
        self.Go = False
        self.redis_database.close()

    def connect_to_redis(self):
        """Connect to the redis instance"""

        # Create a pool connection
        """
        pool = redis.ConnectionPool(host=self.site.CONTROL_SETTINGS['REDIS_HOST'],
                                    port=self.site.CONTROL_SETTINGS['REDIS_PORT'],
                                    db=self.site.CONTROL_SETTINGS['REDIS_DB'])
        """
        # The connection
        #self.redis = redis.Redis(connection_pool=pool)
        
        redis_database = importlib.import_module('database.rapd_redis_adapter')
        
        self.redis_database = redis_database.Database(settings=self.site.CONTROL_DATABASE_SETTINGS)
        """
        # For a Redis pool connection
        self.redis = self.redis_database.connect_redis()
        """
        # For a Redis sentinal connection
        self.redis = self.redis_database.connect_redis_manager_HA()

# class ControllerHandler(threading.Thread):
#     """
#     Handles the data that is received from the cluster via incoming client socket
#     """
#     def __init__(self, conn, addr, receiver, logger=None):
#         """Initialize the handler"""
#
#         # Initialize the thread
#         threading.Thread.__init__(self)
#
#         # Store the connection variable
#         self.conn = conn
#         self.addr = addr
#         self.receiver = receiver
#         self.logger = logger
#
#         # Start the thread
#         self.start()
#
#     def run(self):
#         """Main process of the handler"""
#
#         if self.logger:
#             self.logger.debug("run!")
#
#         #Receive the output back from the cluster
#         message = ""
#         while not message.endswith("<rapd_end>"):
#             data = self.conn.recv(BUFFER_SIZE)
#             message += data
#             time.sleep(0.001)
#         self.conn.close()
#
#         # Strip off the start and end markers
#         stripped = message.rstrip().replace("<rapd_start>", "").replace("<rapd_end>", "")
#
#         # Load the JSON
#         decoded_received = json.loads(stripped)
#
#         # Feedback
#         if self.logger:
#             self.logger.debug(decoded_received)
#
#         # Assign the command
#         self.receiver(decoded_received)

class LaunchAction(threading.Thread):
    """
    Manages the dispatch of jobs to the cluster process
    NB that the cluster can be on the localhost or a remote host
    """
    def __init__(self, command, launcher_address, settings):
        """Initialize the class

        Keyword arguments:
        command -- Dict containing everything needed by launcher and downstream
        launcher_address -- tuple of IP, PORT for a launcher instance
        settings -- Not currently used
        """
        self.logger = logging.getLogger("RAPDLogger")
        self.logger.debug("LaunchAction::__init__  command:%s", command)

        # Initialize the thread
        threading.Thread.__init__(self)

        # Store passed-in variable
        self.command = command
        self.launcher_address = launcher_address
        self.settings = settings    # Not used yet

        # Start the thread
        self.start()

    def run(self):
        """Start the thread"""

        self.logger.debug("Attempting to send launch action to %s:%s",
                          self.launcher_address[0],
                          self.launcher_address[1])

        # Put the command in rapd server-speak
        message = json.dumps(self.command)
        message = "<rapd_start>" + message + "<rapd_end>"
        MSGLEN = len(message)

        # Connect to launcher instance
        attempts = 0
        while attempts < 10:
            attempts += 1
            self.logger.debug("Launcher connection attempt %d", attempts)

            # Connect to the cluster process
            _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                _socket.connect(self.launcher_address)
                break
            except socket.error:
                self.logger.exception("Failed to initialize socket to launcher")
                time.sleep(1)
        else:
            raise RuntimeError("Failed to initialize socket to launcher after %d attempts", attempts)

        # Send the message
        total_sent = 0
        while total_sent < MSGLEN:
            sent = _socket.send(message[total_sent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            total_sent += sent

        self.logger.debug("Message sent to launcher total_sent:%d", total_sent)

        # Close connection to cluster
        _socket.close()

        self.logger.debug("Connection to cluster closed")
