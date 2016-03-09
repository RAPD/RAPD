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

        self.logger.debug("site: %s", self.site)

        self.run()

    def run(self):
        """
        Orchestrate the adapter's actions
        """

        # Decode message
        message_decoded = json.loads(self.message)

        # Unpack message
        try:
            command, data, reply_address = message_decoded
        except ValueError:
            self.logger.error("Unable to unpack message")
            return False

        # Get the launcher directory - in launcher specification
        qsub_dir = self.site.LAUNCHER_SETTINGS["LAUNCHER_SPECIFICATIONS"][self.site.LAUNCHER_ID]["launch_dir"]

        # Put the message into a rapd-readable file
        command_file = launch_tools.write_command_file(qsub_dir, command, self.message)

        # The command has to come in the form of a script on the SERCAT install
        command_line = "rapd.launch -vs %s %s" % (self.site.ID, command_file)
        command_script = launch_tools.write_command_script(command_file.replace(".rapd", ".sh"), command_line)

        # Set the path for qsub
        qsub_path = "PATH=/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/etc:\
/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/bin:\
/home/schuerjp/Programs/best:\
/home/schuerjp/Programs/RAPD/bin:\
/home/schuerjp/Programs/RAPD/share/phenix-1.10.1-2155/build/bin:\
/home/schuerjp/Programs/raddose-20-05-09-distribute-noexec/bin:\
/usr/local/bin:/bin:/usr/bin"

        # Parse a label for qsub job from the command_file name
        qsub_label = os.path.basename(command_file).replace(".rapd", "")

        # Determine the processor specs
        def determine_qsub_proc(command):
            """Determine the queue to use"""
            if command == "AUTO":
                qsub_proc = "nodes=1:ppn=4"
            else:
                qsub_proc = "nodes=1:ppn=1"
            return qsub_proc
        qsub_proc = determine_qsub_proc(command)

        # Call the launch process on the command file
        # qsub_command = "qsub -cwd -V -b y -N %s %s rapd.python %s %s" %
        #       (qsub_label, qsub_queue, command_file_path, command_file)
        qsub_command = "qsub -d %s -v %s -N %s -l %s %s" % (
            qsub_dir, qsub_path, qsub_label, qsub_proc, command_script)

        # Launch it
        self.logger.debug(qsub_command)
        p = Popen(qsub_command, shell=True)
        sts = os.waitpid(p.pid, 0)[1]
