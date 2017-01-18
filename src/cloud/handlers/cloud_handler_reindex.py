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

__created__ = "2016-01-29"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

import datetime
import logging
import os
import threading

# RAPD imports
from control_server import LaunchAction

# This is a rapd cloud handler
CLOUD_HANDLER = True

# This handler's request type
REQUEST_TYPE = "reindex"

# A unique UUID for this handler (uuid.uuid1().hex)
ID = "fc774d3ad98e11e5b08ac82a1400d5bc"

class Handler(threading.Thread):
    """
    Handles the initialization of reprocessing runs in a separate thread
    """

    # single, pair, or new_pair
    index_type = None

    # The data on the image(s)
    image1 = None
    image2 = None

    # Previous result(s) information
    original_result = None
    process_settings = None

    def __init__(self, request, database, settings, reply_settings):
        """Initialize the handler for reindexing frames"""

        # Grab the logger
        self.logger = logging.getLogger("RAPDLogger")
        self.logger.info("ReprocessHandler::__init__  %s", request)

        # Initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.request = request
        self.database = database
        self.settings = settings
        self.reply_settings = reply_settings

        # Kick it off
        self.start()

    def run(self):
        """Main process og the handler"""

        #mark that the request has been addressed
        self.database.markCloudRequest(self.request["cloud_request_id"], "working")

        # Get the settings for processing
        self.get_process_data()

        # Get the images data
        self.get_image_data()

        # Get the working directory and repr
        new_work_dir, new_repr = self.get_work_dir()

        # Save some typing
        data_root_dir = self.original_result["data_root_dir"]

        # Header beam position settings will be overridden sometimes
        # Not overridden
        if self.process_settings["x_beam"] == "0":
            # Source the beam center from the calculated one from image1
            # This gives better indexing results
            if self.image1["calc_beam_center_x"] > 0.0:
                self.process_settings["x_beam"] = self.image1["calc_beam_center_x"]
                self.process_settings["y_beam"] = self.image1["calc_beam_center_y"]

        process_type = {"single" : "single",
                        "pair" : "pair",
                        "new_pair" : "pair"}

        # Add the process to the database to display as in-process
        process_id = self.database.addNewProcess(type=process_type[self.index_type],
                                                 rtype="reprocess",
                                                 data_root_dir=data_root_dir,
                                                 repr=new_repr)

        # Add the ID entry to the data dict
        self.image1.update({"ID" : os.path.basename(new_work_dir),
                            "process_id" : process_id,
                            "repr" : new_repr})
        if self.image2:
            self.image2.update({"ID" : os.path.basename(new_work_dir),
                                "process_id" : process_id,
                                "repr" : new_repr})

        # Now package directories into a dict for easy access by worker class
        new_dirs = {"work" : new_work_dir,
                    "data_root_dir" : self.original_result["data_root_dir"]}


        # Add the request to self.process_settings so it can be passed on
        self.process_settings["request"] = self.request

        # Mark that the request has been addressed
        self.database.markCloudRequest(self.request["cloud_request_id"], "working")

        #mark in the cloud_current table
        self.database.addCloudCurrent(self.request)

        # Connect to the server and autoindex the single image
        # Pair
        if "pair" in self.index_type:
            LaunchAction(command=("AUTOINDEX-PAIR",
                                   new_dirs,
                                   self.image1,
                                   self.image2,
                                   self.process_settings,
                                   self.reply_settings),
                          settings=self.settings)
        # Single
        else:
            LaunchAction(("AUTOINDEX",
                           new_dirs,
                           self.image1,
                           self.process_settings,
                           self.reply_settings),
                          self.settings)

    def get_process_data(self):
        """Retrieve information on the previous process from the database"""

        # Get the settings for processing
        self.process_settings = self.database.getSettings(setting_id=self.request["new_setting_id"])
        self.logger.debug("process_settings: %s", self.process_settings)

        # Get te original result from the database
        self.original_result = self.database.getResultById(self.request["original_id"],
                                                           self.request["original_type"])
        self.logger.debug("original_result: %s", self.original_result)

    def get_image_data(self):
        """Retrieve image data for the image(s) in the autoindexing"""

        # Coming from an indexing of a single image
        if self.request["original_type"] == "single":

            # Reindex using two singles to make a pair
            if self.request["additional_image"] != 0:
                self.index_type = "new_pair"
                self.image1 = self.database.getImageByImageID(
                    image_id=self.original_result["image1_id"])
                self.image2 = self.database.getImageByImageID(
                    image_id=self.request["additional_image"])
            # Single image reindex
            else:
                self.index_type = "single"
                self.image1 = self.database.getImageByImageID(
                    image_id=self.original_result["image_id"])

        # Pair reindex
        elif self.request["original_type"] == "pair":
            self.index_type = "pair"
            self.image1 = self.database.getImageByImageID(
                image_id=self.original_result["image1_id"])
            self.image2 = self.database.getImageByImageID(
                image_id=self.original_result["image2_id"])

    def get_work_dir(self):
        """Calculate the new work directory for this reindexing"""

        # Toplevel
        if self.process_settings["work_dir_override"] == "False":
            # Same as before
            if "/single/" in self.original_result["work_dir"]:
                toplevel_dir = os.path.dirname(
                    self.original_result["work_dir"].split("single")[0])
            elif "/pair/" in self.original_result["work_dir"]:
                toplevel_dir = os.path.dirname(
                    self.original_result["work_dir"].split("pair")[0])
        else:
            # New toplevel dir
            toplevel_dir = self.process_settings["work_directory"]

        # Type level
        if self.index_type == "new_pair":
            typelevel_dir = "pair"
        else:
            typelevel_dir = self.index_type

        # Date level
        datelevel_dir = datetime.date.today().isoformat()

        # Sub level
        if self.index_type == "single":
            if self.settings["DETECTOR_SUFFIX"]:
                sub_dir = os.path.basename(self.image1["fullname"]).replace(
                    self.settings["DETECTOR_SUFFIX"], "")
            else:
                sub_dir = os.path.basename(self.image1["fullname"])
        elif self.index_type == "pair":
            sub_dir = "_".join((self.image1["image_prefix"],
                                "+".join((str(self.image1["image_number"]).lstrip("0"),
                                          str(self.image2["image_number"]).lstrip("0")))))
        elif self.index_type == "new_pair":
            # Image prefixes are the same
            if self.image1["image_prefix"] == self.image2["image_prefix"]:
                sub_dir = "_".join((self.image["image_prefix"],
                                    "+".join((str(self.image1["image_number"]).lstrip("0"),
                                              str(self.image2["image_number"]).lstrip("0")))))
            # Different image prefixes - same for now, but could change if decide to
            else:
                sub_dir = "_".join((self.image1["image_prefix"],
                                    "+".join((str(self.image1["image_number"]).lstrip("0"),
                                              str(self.image2["image_number"]).lstrip("0")))))

        # Join the three levels
        work_dir_candidate = os.path.join(toplevel_dir, typelevel_dir, datelevel_dir, sub_dir)

        # Make sure this is an original directory
        if os.path.exists(work_dir_candidate):
            # We have already
            self.logger.debug("%s has already been used, will add qualifier", work_dir_candidate)
            for i in range(1, 10000):
                if not os.path.exists("_".join((work_dir_candidate, str(i)))):
                    work_dir_candidate = "_".join((work_dir_candidate, str(i)))
                    self.logger.debug("%s will be used for this image", work_dir_candidate)
                    break
                else:
                    i += 1

        return work_dir_candidate, sub_dir
