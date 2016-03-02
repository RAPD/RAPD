"""
This file is part of RAPD

Copyright (C) 2016, Cornell University
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

__created__ = "2016-03-02"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

"""
An echo rapd_agent
"""

import logging
import multiprocessing

# This is an active rapd agent
RAPD_AGENT = True

# This handler's request type
AGENT_TYPE = "echo"

# A unique UUID for this handler (uuid.uuid1().hex)
ID = "4eb96075e0a911e590d2c82a1400d5bc"

class RapdAgent(multiprocessing.Process):
    """
    An action class which only echos the input data back
    """

    # This is where I have chosen to place my results
    results = False

    def __init__(self, command, request, reply_settings):
        """
        Initialize the TestCase process

        input   is whatever is passed in
        pipe    is the communication back to the calling process
        """

        # Get the logger Instance
        self.logger = logging.getLogger("RAPDLogger")
        self.logger.debug("__init__")

        self.command = command
        self.request = request
        self.reply_settings = reply_settings

        self.logger.debug(command)

        # Initialize the process
        multiprocessing.Process.__init__(self, name=AGENT_TYPE)

        # Starts the new process
        self.start()

    def run(self):
        """
        Orchestrates the agent's duties
        """

        self.preprocess()
        self.process()
        self.postprocess()

    def preprocess(self):
        """
        Things to do before the main process runs
        1. Change to the correct directory
        2. Print out the reference for labelit
        """
        self.logger.debug("preprocess")


    def process(self):
        """
        The main process
        1. Construct the labelit command
        2. Run labelit, grabbing the outout
        3. Parse the labelit output
        """
        self.logger.debug("process")

        # Put the gathered data into a dict for return
        self.results = [self.command, self.request, self.reply_settings]
        self.results.append("rapd_agent_echo")

    def postprocess(self):
        """
        Things to do after the main process runs
        1. Return the data throught the pipe
        """
        self.logger.debug("postprocess")

        self.logger.debug(self.results)
