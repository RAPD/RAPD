"""
Provides a simple launcher adapter that will launch processes in a shell
"""

"""
This file is part of RAPD

Copyright (C) 2016-2017 Cornell University
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

    def __init__(self, site, message, settings):
        """
        Initialize the adapter
        """

        # Get the logger Instance
        self.logger = logging.getLogger("RAPDLogger")
        self.logger.debug("__init__")

        self.site = site
        self.message = message
        self.settings = settings

        self.run()

    def run(self):
        """
        Orchestrate the adapter's actions
        """

        # Adjust the message to this site
        self.fix_command()

        # Put the command into a file
        command_file = launch_tools.write_command_file(self.settings["launch_dir"],
                                                       self.message["command"],
                                                       self.message)

        # Call the launch process on the command file
        self.logger.debug("rapd.launch", "-s", self.site.SITE, command_file)
        Popen(["rapd.launch", "-s", self.site.SITE, command_file])

    def fix_command(self):
        """
        Adjust the command passed in in install-specific ways
        """

        # Adjust the working directory for the launch computer
        work_dir_candidate = os.path.join(
            self.site.LAUNCHER_SETTINGS["LAUNCHER_SPECIFICATIONS"][self.site.LAUNCHER_ID]["launch_dir"],
            self.message["directories"]["work"])

        # Make sure this is an original directory
        if os.path.exists(work_dir_candidate):
            # Already exists
            for i in range(1, 1000):
                if not os.path.exists("_".join((work_dir_candidate, str(i)))):
                    work_dir_candidate = "_".join((work_dir_candidate, str(i)))
                    break
                else:
                    i += 1
        # Now make the directory
        if os.path.isdir(work_dir_candidate) == False:
            os.makedirs(work_dir_candidate)

        # Modify command
        #self.decoded_message["directories"]["work"] = work_dir_candidate
        self.message["directories"]["work"] = work_dir_candidate

if __name__ == "__main__":

    LauncherAdapter('["test1", "test2", "test3"]', {"launch_dir":"/tmp/log"})
