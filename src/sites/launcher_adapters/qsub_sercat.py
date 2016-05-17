"""
Provides a simple launcher adapter that will launch processes via qsub
"""

__license__ = """
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

# Standard imports
import logging
import json
import os
from subprocess import Popen

# RAPD imports
import utils.launch_tools as launch_tools

class LauncherAdapter(object):
    """
    An adapter for launcher process.

    Will launch requested job via qsub on current machine.

    NB - this adapter is highly specific to SERCAT install.
    """

    def __init__(self, site, message, settings):
        """
        Initialize the adapter

        Keyword arguments
        site -- imported site definition module
        message -- command from the control process, encoded as JSON
        settings --
        """

        # Get the logger Instance
        self.logger = logging.getLogger("RAPDLogger")
        self.logger.debug("__init__")

        self.site = site
        self.message = message
        self.settings = settings

        # Decode message
        self.decoded_message = json.loads(self.message)

        self.run()

    def run(self):
        """
        Orchestrate the adapter's actions
        """

        # Adjust the message to this site
        self.fix_command()

        # Get the launcher directory - in launcher specification
        qsub_dir = self.site.LAUNCHER_SETTINGS["LAUNCHER_SPECIFICATIONS"][self.site.LAUNCHER_ID]["launch_dir"]+"/command_files"

        # Put the message into a rapd-readable file
        command_file = launch_tools.write_command_file(qsub_dir, self.decoded_message["command"], json.dumps(self.decoded_message))

        # The command has to come in the form of a script on the SERCAT install
        site_tag = self.site.LAUNCHER_SETTINGS["LAUNCHER_SPECIFICATIONS"][self.site.LAUNCHER_ID]["site_tag"]
        command_line = "rapd.launch -vs %s %s" % (site_tag, command_file)
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
            if command.startswith("index"):
                qsub_proc = "nodes=1:ppn=4"
            else:
                qsub_proc = "nodes=1:ppn=1"
            return qsub_proc
        qsub_proc = determine_qsub_proc(self.decoded_message["command"])

        # Call the launch process on the command file
        # qsub_command = "qsub -cwd -V -b y -N %s %s rapd.python %s %s" %
        #       (qsub_label, qsub_queue, command_file_path, command_file)
        # qsub_command = "qsub -d %s -v %s -N %s -l %s %s" % (
        #     qsub_dir, qsub_path, qsub_label, qsub_proc, command_script)
        qsub_command = "qsub -d %s -v %s -N %s -l %s %s" % (
            qsub_dir, qsub_path, qsub_label, qsub_proc, command_script)

        # Launch it
        print "!!!!!!!!!!!!!"
        print qsub_command
        self.logger.debug(qsub_command)
        p = Popen(qsub_command, shell=True)
        sts = os.waitpid(p.pid, 0)[1]

    def fix_command(self):
        """
        Adjust the command passed in in install-specific ways
        """

        # Adjust the working directory for the launch computer
        self.decoded_message["directories"]["work"] = os.path.join(self.site.LAUNCHER_SETTINGS["LAUNCHER_SPECIFICATIONS"][self.site.LAUNCHER_ID]["launch_dir"],
                                                                   self.decoded_message["directories"]["work"])

        # Filesystem is NOT shared
        # For header_1 & header_2
        for header_iter in ("1", "2"):
            header_key = "header%s" % header_iter
            if header_key in self.decoded_message:
                # Values that need changed
                for value_key in ("fullname", "directory"):
                    # Store originals
                    self.decoded_message[header_key][value_key+"_orig"] = self.decoded_message[header_key][value_key]

                    # Change
                    for prepended_string in ("/raw", "/archive"):
                        if self.decoded_message[header_key][value_key].startswith(prepended_string):
                            self.decoded_message[header_key][value_key] = self.decoded_message[header_key][value_key].replace(prepended_string, "/panfs/panfs0.localdomain"+prepended_string)
