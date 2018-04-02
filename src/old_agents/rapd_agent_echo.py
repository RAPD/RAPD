"""
An echo RAPD agent
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2016-2018 Cornell University
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

# This is an active rapd agent
RAPD_AGENT = True
AGENT_TYPE = "ECHO"
AGENT_SUBTYPE = "CORE"
AGENT_VERSION = "2.0"
# A unique UUID for this handler (uuid.uuid1().hex)
AGENT_ID = "4eb96075e0a911e590d2c82a1400d5bc"

# Standard imports
import logging
import multiprocessing

# RAPD imports
from utils.communicate import rapd_send

class RapdAgent(multiprocessing.Process):
    """
    An action class which only echos the input data back
    """

    # Address for communications to go to
    reply_settings = None

    # This is where I have chosen to place my results
    results = False

    def __init__(self, site, command):
        """
        Initialize the echo process

        Keyword arguments
        site -- full site settings
        command -- dict of data necessary for this agent
        """

        # Get the logger Instance
        self.logger = logging.getLogger("RAPDLogger")
        self.logger.debug("__init__")

        self.site = site
        self.command = command

        self.logger.debug("%s", self.site)

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

        # Get the reply_settings
        self.reply_settings = self.command["return_address"]

        # Put the gathered data into a dict for return
        self.results = self.command

        # Add the agent information
        self.results["process"]["origin"] = "AGENT"
        self.results["process"]["agent_id"] = AGENT_ID
        self.results["process"]["agent_type"] = AGENT_TYPE
        self.results["process"]["agent_subtype"] = AGENT_SUBTYPE
        self.results["process"]["agent_version"] = AGENT_VERSION

    def process(self):
        """
        The main process
        1. Construct the labelit command
        2. Run labelit, grabbing the outout
        3. Parse the labelit output
        """
        self.logger.debug("process")

        # Spoof that this agent has a real results
        self.results["results"] = True

    def postprocess(self):
        """
        Things to do after the main process runs
        1. Return the data throught the pipe
        """
        self.logger.debug("postprocess")

        self.logger.debug(self.results)

        # Send back the data as an echo
        rapd_send(self.reply_settings, self.results)
