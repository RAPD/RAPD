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
Provides a simple launcher adapter that will launch processes in a shell
"""

import logging
import json
from subprocess import Popen

# RAPD imports
import utils.launch_tools as launch_tools

class LauncherAdapter(object):
    """
    An adapter for launcher process.

    Will launch requested job in shell on the current machine
    """

    def __init__(self, message, settings):
        """
        Initialize the adapter
        """

        # Get the logger Instance
        self.logger = logging.getLogger("RAPDLogger")
        self.logger.debug("__init__")

        self.message = message
        self.settings = settings

        self.run()

    def run(self):
        """
        Orchestrate the adapter's actions
        """

        # Decode message
        message_decoded = json.loads(self.message)

        # Unpack message
        try:
            command, request, reply_settings = message_decoded
        except ValueError:
            self.logger.error("Unable to unpack message")
            return False

        # Put the command into a file
        command_file = launch_tools.write_command_file(self.settings["launch_dir"], command, self.message)

        # Call the launch process on the command file
        Popen(["rapd.launch", command_file], shell=True)

if __name__ == "__main__":

    LauncherAdapter('["test1", "test2", "test3"]', {"launch_dir":"/tmp/log"})
