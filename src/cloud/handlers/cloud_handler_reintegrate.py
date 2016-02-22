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

import logging
import os
import threading

# This is a rapd cloud handler
CLOUD_HANDLER = True

# This handler's request type
REQUEST_TYPE = "reintegration"

# A unique UUID for this handler (uuid.uuid1().hex)
ID = "d3a84d9ed98e11e5b92fc82a1400d5bc"

class Handler(threading.Thread):
    """
    Handles the initialization of re-integrations in a separate thread.
    """

    # Previous result(s) information
    original_result = None
    process_settings = None

    def __init__(self, request, database, settings, reply_settings):
        """
        Initialize the handler.

        request - a dict containing information on the request
        database - an instance of rapd_database.Database
        settings - dict from rapd_site describing settings for this rapd setup
        reply_settings - a tuple of ip address and port for the controller server to reply to
        """

        # Grab the logger
        self.logger = logging.getLogger("RAPDLogger")
        self.logger.info("IntegrationHandler::__init__  %s", str(request))

        # Initialize the thread
        threading.Thread.__init__(self)

        # Store passed-in variables
        self.request = request
        self.database = database
        self.settings = settings
        self.reply_settings = reply_settings

        # Start the new thread
        self.start()

    def run(self):
        """
        The new thread is now running
        """

        self.logger.debug("IntegrationHandler::run")

        # Mark that the request has been addressed
        self.database.markCloudRequest(self.request["cloud_request_id"], "working")

        # Get the settings for processing
        self.get_process_data()

        # Get working directory and repr
        new_work_dir, new_repr = self.get_work_dir()

        # Save some typing
        data_root_dir = self.original_result["data_root_dir"]

        # Tweak request
        self.request["work_dir"] = new_work_dir

        # XDS
        if self.request["request_type"] == "start-fastin":
            request_type = "XDS"
        # xia2
        elif self.request["request_type"] == "start-xiaint":
            request_type = "XIA2"

        # Re-key the spacegroup request
        self.request["spacegroup"] = int(self.request.get("option1", 0))

        # Wavelength
        self.request["wavelength"] = self.database.getWavelengthFromRunId(
            run_id=self.original_result["run_id"])

        # Add the process to the database to display as in-process
        process_id = self.database.addNewProcess(type=request_type,
                                                 rtype="reprocess",
                                                 data_root_dir=data_root_dir,
                                                 repr=new_repr)

        # Create a result for this process as well
        integrate_result_id, result_id = self.database.makeNewResult(rtype="integrate",
                                                                     process_id=process_id,
                                                                     data_root_dir=data_root_dir)

        # Add the process id entry to the data dicts
        self.process_settings["process_id"] = process_id

        # Now package directories into a dict for easy access by worker class
        my_dirs = {"work":new_work_dir,
                   "data_root_dir":data_root_dir}

        #accumulate the information into the data directory
        data = {"original":self.original_result,
                "repr":new_repr}

        # Add the request to self.process_settings so it can be passed on
        self.process_settings["request"] = self.request

        #mark that the request has been addressed
        self.database.markCloudRequest(self.request["cloud_request_id"], "working")

        #mark in the cloud_current table
        self.database.addCloudCurrent(self.request)

        #connect to the server and send request
        PerformAction((my_request_type, my_dirs, data, self.process_settings, self.reply_settings),
                      self.process_settings,
                      self.settings,self.logger)

    def get_work_dir(self):
        """Calculate and check a new work directory and repr"""

        #construct a repr for the reprocessed data
        new_repr = "_".join(self.original_result["repr"].split("_")[:-1])+"_"+str(self.request["frame_start"])+"-"+str(self.request["frame_finish"])

        # Get the correct directory to run in
        # We should end up with original["work_dir"]/reprocess_#
        work_dir_candidate = os.path.join(self.original_result["work_dir"], "reproc")
        # work_dir = "_".join((my_work_dir_candidate, str(1)))
        #make sure this is an original directory
        for i in range(1, 10000):
            if not os.path.exists("_".join((work_dir_candidate, str(i)))):
                work_dir_candidate = "_".join((work_dir_candidate, str(i)))
                new_repr += "_%d" % i
                self.logger.debug("%s will be used for this image", work_dir_candidate)
                break


        return work_dir_candidate, new_repr

    def get_process_data(self):
        """Retrieve information on the previous process from the database"""

        # Get the settings for processing
        self.process_settings = self.database.getSettings(setting_id=self.request["new_setting_id"])
        self.logger.debug("process_settings: %s", self.process_settings)

        # Get te original result from the database
        self.original_result = self.database.getResultById(self.request["original_id"],
                                                           "integrate")
        self.logger.debug("original_result: %s", self.original_result)
