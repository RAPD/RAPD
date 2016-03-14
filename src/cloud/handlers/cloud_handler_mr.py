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

__created__ = "2016-01-29"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

import datetime
import logging
import os
import paramiko
import threading

# RAPD imports
from control_server import LaunchAction

# This is a rapd cloud handler
CLOUD_HANDLER = True

# This handler's request type
REQUEST_TYPE = "mr"

# A unique UUID for this handler (uuid.uuid1().hex)
ID = "58f2f0a6d98e11e5b9dcc82a1400d5bc"

class Handler(threading.Thread):
    """
    Handles the initialization of MR runs in a separate thread
    """

    # Previous result(s) information
    original_result = None
    process_settings = None

    def __init__(self, request, database, settings, reply_settings):

        self.logger = logging.getLogger("RAPDLogger")
        self.logger.info("MrHandler::__init__  %s", str(request))

        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.request = request
        self.database = database
        self.settings = settings
        self.reply_settings = reply_settings

        self.start()

    def run(self):
        self.logger.debug("MrHandler::run")

        # Mark that the request has been addressed
        self.database.markCloudRequest(self.request["cloud_request_id"], "working")

        # Get the settings for processing
        self.get_process_data()

        # Get the pdb info from the UI
        new_pdb = self.transfer_pdb_from_ui()
        if new_pdb:

            # A code has been used for MR
            if new_pdb == "option1":
                self.request["pdb"] = None
                self.request["pdb_code"] = self.request["option1"]

            # A PDB file has been uploaded by the user for MR
            else:
                self.request["pdb"] = new_pdb

            # Save some typing
            data_root_dir = self.original_result["data_root_dir"]

            #get the wavelength
            self.request["wavelength"] = self.original_result["wavelength"]

            # Get the working directory and repr
            new_work_dir, new_repr = self.get_work_dir()

            # Add the process to the database to display as in-process
            process_id = self.database.addNewProcess(type="mr",
                                                     rtype="original",
                                                     data_root_dir=data_root_dir,
                                                     repr=new_repr)

            # Add the process id entry to the data dicts
            self.process_settings["process_id"] = process_id

            # Now package directories into a dict for easy access by worker class
            my_dirs = {"work":new_work_dir,
                       "data_root_dir":data_root_dir}

            # Accumulate the information into the data directory
            data = {"original":self.original_result,
                    "repr":new_repr}

            # Add the request to self.process_settings so it can be passed on
            self.process_settings["request"] = self.request

            # Mark that the request has been addressed
            self.database.markCloudRequest(self.request["cloud_request_id"], "working")

            # Mark in the cloud_current table
            self.database.addCloudCurrent(self.request)

            # Connect to the server and autoindex the single image
            LaunchAction(("MR", my_dirs, data, self.process_settings, self.reply_settings),
                          self.process_settings,
                          self.settings)

        # MR without PDB == impossible
        else:
            raise Exception("No PDB for MR run")

    def get_process_data(self):
        """Retrieve information on the previous process from the database"""

        # Get the settings for processing
        self.process_settings = self.database.getSettings(setting_id=self.request["new_setting_id"])
        self.logger.debug("process_settings: %s", self.process_settings)

        # Get te original result from the database
        self.original_result = self.database.getResultById(self.request["original_id"],
                                                           self.request["original_type"])
        self.logger.debug("original_result: %s", self.original_result)


    def transfer_pdb_from_ui(self):
        """
        Transfer the pdb from the UI Server to the local host
        """

        self.logger.debug("MrHander.TransferFromUi")

        # Set up simpler versions of the host parameters
        host = self.settings["UI_HOST"]
        port = self.settings["UI_PORT"]
        username = self.settings["UI_USER"]
        password = self.settings["UI_PASSWORD"]

        # No PDB to transfer ?
        if self.request["pdbs_id"] == 0:
            return "option1"
        else:
            pdb_dict = self.database.getPdbById(pdbs_id=self.request["pdbs_id"])

            if pdb_dict:
                # Create the log file
                paramiko.util.log_to_file("/tmp/paramiko.log")

                # Create the Transport instance
                transport = paramiko.Transport((host, port))

                # Connect with username and password
                transport.connect(username=username, password=password)

                # Establish sftp client
                sftp = paramiko.SFTPClient.from_transport(transport)

                # The source and target
                source = os.path.join(self.settings["ui_upload_dir"], pdb_dict["pdb_file"])
                target = os.path.join(self.settings["upload_dir"], str(pdb_dict["pdbs_id"])+".pdb")

                # Transfer
                sftp.get(source, target)

                # Close up transport
                sftp.close()
                transport.close()

                # Store the location for future use
                self.database.updatePdbLocation(pdbs_id=pdb_dict["pdbs_id"],
                                                location=target)

                return target
            else:
                return False
    def get_work_dir(self):
        """Create a working directory and repr for the process"""

        #construct a repr for the merged data
        new_repr = self.original_result["repr"]

        # Get the correct directory to run in
        # We should end up with top_level/sad/2010-05-10/XXX_1_1-180/

        # Top level
        if self.process_settings["work_dir_override"] == "False":
            if "merge" in self.original_result["work_dir"]:
                toplevel_dir = self.original_result["work_dir"][:self.original_result["work_dir"].index("merge")]
            else:
                toplevel_dir = self.original_result["work_dir"][:self.original_result["work_dir"].index("integrate")]
        else:
            toplevel_dir = self.process_settings["work_directory"]

        # Type level
        typelevel_dir = "mr"

        # Date level
        datelevel_dir = datetime.date.today().isoformat()

        # Lowest level
        sub_dir = new_repr

        # Join the four levels
        work_dir_candidate = os.path.join(toplevel_dir, typelevel_dir, datelevel_dir, sub_dir)

        # Make sure this is an original directory
        if os.path.exists(work_dir_candidate):
            # Directory already exists
            for i in range(1, 10000):
                if not os.path.exists("_".join((work_dir_candidate, str(i)))):
                    work_dir_candidate = "_".join((work_dir_candidate, str(i)))
                    break
                else:
                    i += 1

        return work_dir_candidate, new_repr
