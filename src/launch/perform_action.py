"""
This file is part of RAPD

Copyright (C) 2009-2016, Cornell University
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

"""
Method for connecting and sending command to Launcher instance
"""

import socket
import threading
import json
import time
import logging
import logging.handlers

BUFFER_SIZE = 8192

class PerformAction(threading.Thread):
    """
    Manages the dispatch of jobs to the cluster process
    NB that the cluster can be on the localhost or a remote host
    """
    def __init__(self, command, settings):
        """Initialize the class

        Keyword arguments:
        command --
        settings -- Right now only needs to be a dict with the entry LAUNCHER_ADDRESS
        """
        self.logger = logging.getLogger("RAPDLogger")
        self.logger.debug("PerformAction::__init__  command:%s", command)

        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variable
        self.command = command
        self.settings = settings

        # Start the thread
        self.start()

    def run(self):
        """Start the thread"""

        self.logger.debug("PerformAction::run")

        attempts = 0

        while attempts < 10:
            attempts += 1
            self.logger.debug("Launcher connection attempt %d", attempts)

            # Connect to the cluster process
            _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                _socket.connect(self.settings["LAUNCHER_ADDRESS"])
                break
            except socket.error:
                self.logger.exception("Failed to initialize socket to cluster")
                time.sleep(1)
        else:
            raise RuntimeError("Failed to initialize socket to cluster after %d attempts", attempts)

        # Put the command in rapd server-speak
        message = json.dumps(self.command)
        message = "<rapd_start>" + message + "<rapd_end>"
        message_length = len(message)

        # Send the message
        total_sent = 0
        while total_sent < message_length:
            sent = _socket.send(message[total_sent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            total_sent += sent

        self.logger.debug("Message sent to cluster total_sent:%d", total_sent)

        # Close connection to cluster
        _socket.close()

        self.logger.debug("Connection to cluster closed")

if __name__ == '__main__':

    print "perform_action.py"
