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

__created__ = "2016-01-31"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

import datetime
import logging
import os
import threading

from rapd_launch import PerformAction

class Handler(threading.Thread):
    """
    Handles the initialization of SAD runs in a separate thread.
    """

    original_result = None
    process_settings = None

    def __init__(self, request, database, settings, reply_settings):
        """
        Initialize SadHandler.

        Keyword arguments:
        request - a dict contining a variety of information that comes from the request
        database - an instance of rapd_database.Database
        settings -
        reply_settings - a tuple of the ip address and port for the controller server
        """

        self.logger = logging.getLogger("RAPDLogger")
        self.logger.info("SadHandler::__init__  %s", str(request))

        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.request = request
        self.database = database
        self.settings = settings
        self.reply_settings = reply_settings
        self.start()

    def run(self):
        self.logger.debug("SadHandler::run")

        # Read the original results and settings into instance-level variables
        self.get_process_data()

        #mark that the request has been addressed
        self.database.markCloudRequest(self.request["cloud_request_id"], "working")

        # Get the working directory and repr
        new_work_dir, new_repr = self.get_work_dir()

        # data root dir
        data_root_dir = self.original_result["data_root_dir"]

        #get the wavelength
        self.request["wavelength"] = self.original_result["wavelength"]

        # Add the process to the database to display as in-process
        process_id = self.database.addNewProcess(type="sad",
                                                 rtype="original",
                                                 data_root_dir=data_root_dir,
                                                 repr=new_repr)

        # Add the process id entry to the data dicts
        self.process_settings["process_id"] = process_id

        # Now package directories into a dict for easy access by worker class
        new_dirs = {"work":new_work_dir,
                    "data_root_dir":data_root_dir}

        #accumulate the information into the data directory
        data = {"original":self.original_result,
                "repr":new_repr}

        # Add the request to self.process_settings so it can be passed on
        self.process_settings["request"] = self.request

        # Mark that the request has been addressed
        self.database.markCloudRequest(self.request["cloud_request_id"], "working")

        # Mark in the cloud_current table
        self.database.addCloudCurrent(self.request)

        # Connect to the server and autoindex the single image
        PerformAction(("SAD", new_dirs, data, self.process_settings, self.reply_settings),
                      self.process_settings,
                      self.settings)

    def get_process_data(self):
        """Retrieve information on the previous process from the database"""

        # The original result
        self.original_result = self.database.getResultById(self.request["original_id"],
                                                           self.request["original_type"])
        # Get the settings
        self.process_settings = self.database.getSettings(
            setting_id=self.original_result["settings_id"])

    def get_work_dir(self):
        """Returns the work directory and repr for """

        # Get the correct directory to run in
        # We should end up with top_level/sad/2010-05-10/XXX_1_1-180/

        # No override
        if self.process_settings["work_dir_override"] == "False":
            # Use the original result as the basis for the new directory
            # Should either be a merge or an integration
            # Merge
            if "merge" in self.original_result["work_dir"]:
                toplevel_dir = self.original_result["work_dir"][:self.original_result["work_dir"].index("merge")]
            # Integration
            else:
                toplevel_dir = self.original_result["work_dir"][:self.original_result["work_dir"].index("integrate")]
        # Use the override directory
        else:
            toplevel_dir = self.process_settings["work_directory"]

        # Type level
        typelevel_dir = "sad"

        # Date level
        datelevel_dir = datetime.date.today().isoformat()

        # Lowest level
        sub_dir = self.original_result["repr"]
        new_repr = self.original_result["repr"]

        # Join the four levels
        work_dir_candidate = os.path.join(toplevel_dir, typelevel_dir, datelevel_dir, sub_dir)

        #make sure this is an original directory
        if os.path.exists(work_dir_candidate):
            # Directory already exists
            self.logger.debug("%s has already been used, will add qualifier", work_dir_candidate)
            for i in range(1, 10000):
                if not os.path.exists("_".join((work_dir_candidate, str(i)))):
                    work_dir_candidate = "_".join((work_dir_candidate, str(i)))
                    self.logger.debug("%s will be used for this image", work_dir_candidate)
                    break
                else:
                    i += 1

        return work_dir_candidate, new_repr
