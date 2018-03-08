"""
Provides a simple launcher adapter that will launch processes in a shell
"""

"""
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

import logging
# import json
import os
from subprocess import Popen

# RAPD imports
import utils.launch_tools as launch_tools
from utils.modules import load_module

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
        # Check if command is ECHO
        if self.message['command'] == 'ECHO':
            # Load the simple_echo module
            echo = load_module(seek_module='launch.launcher_adapters.echo_simple')
            # send message to simple_echo
            echo.LauncherAdapter(self.site, self.message, self.settings)
        else:
            # Adjust the message to this site
            #self.fix_command()
            self.message = launch_tools.fix_command(self.message)
    
            # Put the command into a file
            command_file = launch_tools.write_command_file(self.settings["launch_dir"],
                                                           self.message["command"],
                                                           self.message)
    
            # Set the site tag from input
            site_tag = launch_tools.get_site_tag(self.message).split('_')[0]
    
            # Call the launch process on the command file
            self.logger.debug("rapd.launch -s %s %s", site_tag, command_file)
            Popen(["rapd.launch", "-s",site_tag, command_file])

    def fix_command_OLD(self):
        """
        Adjust the command passed in in install-specific ways
        """

        # Adjust the working directory for the launch computer
        work_dir_candidate = os.path.join(
            self.message["directories"]["launch_dir"],
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
