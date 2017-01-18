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

__created__ = "2016-03-08"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

"""
Provides a simple launcher adapter that will launch processes via qsub

This is the stock version used at NE-CAT
"""

import logging
import json
import os
from subprocess import Popen

# RAPD imports
import utils.launch_tools as launch_tools

class LauncherAdapter(object):
    """
    An adapter for launcher process.

    Will launch requested job via qsub on current machine
    """

    def __init__(self, site_id, message, settings):
        """
        Initialize the adapter
        """

        # Get the logger Instance
        self.logger = logging.getLogger("RAPDLogger")
        self.logger.debug("__init__")

        self.site_id = site_id
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
            command, dirs, data, send_address, reply_address = message_decoded
        except ValueError:
            self.logger.error("Unable to unpack message")
            return False

        # Put the command into a file
        command_file = launch_tools.write_command_file(self.settings["launch_dir"], command, self.message)
        command_file_path = os.path.abspath(command_file)

        # Generate a label for qsub job
        qsub_label = os.path.basename(command_file).replace(".rapd", "")

        # Determine the qsub queue
        def determine_qsub_queue(command):
            """Determine the queue to use"""
            if command == "AUTO":
                cl_queue = "-q index.q -pe smp 4"
            elif command == "INTE":
                cl_queue = "-q phase2.q"
            else:
                cl_queue = "-q phase1.q"
            return cl_queue
        qsub_queue = determine_qsub_queue(command)

        # Call the launch process on the command file
        # qsub_command = "qsub -cwd -V -b y -N %s %s rapd.python %s %s" %
        #       (qsub_label, qsub_queue, command_file_path, command_file)
        qsub_command = "qsub -cwd -V -b y -N %s %s rapd.launch %s" % (
            qsub_label, qsub_queue, command_file)

        # Launch it
        self.logger.debug(qsub_command)
        p = Popen(qsub_command, shell=True)
        sts = os.waitpid(p.pid, 0)[1]
        # qsub -d (working_dir) -V -N (job name) (for indexing add '-l nodes=1:ppn=4') command_script
