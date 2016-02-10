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

__created__ = "2016-02-01"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

import datetime
import logging
import os
import threading

from rapd_cluster import PerformAction

class Handler(threading.Thread):
    """
    Handles the initialization of simple merging runs in a separate thread
    """

    # Previous result(s) information
    primary_result = None
    secondary_result = None
    process_settings = None

    def __init__(self, request, database, settings, reply_settings):

        # Grab the logger
        self.logger = logging.getLogger("RAPDLogger")
        self.logger.info("SimpleMergeHandler::__init__  %s", request)

        # Initialize the thread
        threading.Thread.__init__(self)

        # Store passed-in variables
        self.request = request
        self.database = database
        self.settings = settings
        self.reply_settings = reply_settings

        # Run
        self.start()

    def run(self):
        """Body of the handler"""

        self.logger.debug("SimpleMergeHandler::run")

        # Mark that the request has been addressed
        self.database.markCloudRequest(self.request["cloud_request_id"], "working")

        # Get the settings for processing
        self.get_process_data()

        # Get the working directory and repr
        new_work_dir, new_repr = self.get_work_dir()

        # Save typing
        data_root_dir = self.primary_result["data_root_dir"]

        # Add the process to the database to display as in-process
        process_id = self.database.addNewProcess(type="merge",
                                                 rtype="reprocess",
                                                 data_root_dir=data_root_dir,
                                                 repr=new_repr)

        # Make a new result for this process
        merge_result_id, result_id = self.database.makeNewResult(rtype="merge",
                                                                 process_id=process_id,
                                                                 data_root_dir=data_root_dir)

        # Package directories into a dict for easy access by worker class
        new_dirs = {"work":new_work_dir,
                    "data_root_dir":data_root_dir}

        # Accumulate the information into the data directory
        data = {"original":self.primary_result,
                "secondary":self.secondary_result,
                "repr":new_repr,
                "process_id":process_id}

        # Add the request to self.process_settings so it can be passed on
        self.process_settings["request"] = self.request

        # Mark that the request has been addressed
        self.database.markCloudRequest(self.request["cloud_request_id"], "working")

        # Mark in the cloud_current table
        self.database.addCloudCurrent(self.request)

        # Connect to the server and autoindex the single image
        PerformAction(("SMERGE", new_dirs, data, self.process_settings, self.reply_settings),
                      self.process_settings,
                      self.settings)

    def get_process_data(self):
        """Retrieve information on the previous process from the database"""

        # Get the settings for processing
        self.process_settings = self.database.getSettings(setting_id=self.request["new_setting_id"])
        self.logger.debug("process_settings: %s", self.process_settings)

        # Get the primary and secondary results from the database
        self.primary_result = self.database.getResultById(self.request["original_id"],
                                                          self.request["original_type"])
        self.secondary_result = self.database.getResultById(self.request["additional_image"],
                                                            "integrate")
        self.logger.debug("primary_result: %s", self.primary_result)
        self.logger.debug("secondary_result: %s", self.secondary_result)


    def get_work_dir(self):
        """Calculate the new work directory for this reindexing"""

        # Construct a repr for the merged data
        new_repr = self.primary_result["repr"]+"+"+self.secondary_result["repr"]

        # Get the correct directory to run in
        # We should end up with top_level/sad/2010-05-10/XXX_1_1-180/
        # Top level
        if self.process_settings["work_dir_override"] == "False":
            if  "merge" in self.primary_result["work_dir"]:
                toplevel_dir = self.primary_result["work_dir"][:self.primary_result["work_dir"].index("merge")]
            else:
                toplevel_dir = self.primary_result["work_dir"][:self.primary_result["work_dir"].index("integrate")]
        else:
            toplevel_dir = self.process_settings["work_directory"]

        # Type level
        typelevel_dir = "merge"

        # Date level
        datelevel_dir = datetime.date.today().isoformat()

        # Lowest level
        sub_dir = new_repr

        # Join the four levels
        work_dir_candidate = os.path.join(toplevel_dir, typelevel_dir, datelevel_dir, sub_dir)

        # Make sure this is an original directory
        if os.path.exists(work_dir_candidate):
            # Have already
            for i in range(1, 10000):
                if not os.path.exists("_".join((work_dir_candidate, str(i)))):
                    work_dir_candidate = "_".join((work_dir_candidate, str(i)))
                    break
                else:
                    i += 1

        return work_dir_candidate, new_repr
