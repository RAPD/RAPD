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
import threading

from rapd_launch import PerformAction

class Handler(threading.Thread):
    """
    Handles the packing and transfer of downloads in a separate thread
    """
    def __init__(self, request, database, settings, reply_settings):
        """Initialize the download handler"""

        self.logger = logging.getLogger("RAPDLOGGER")
        self.logger.info("DownloadHandler::__init__")
        self.logger.debug(request)

        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.request = request
        self.database = database
        self.settings = settings
        self.reply_settings = reply_settings

        # Start the thread
        self.start()

    def run(self):
        """The main process of the handler"""

        self.logger.debug("DownloadHandler::run")

        #mark that the request has been addressed
        self.database.markCloudRequest(self.request["cloud_request_id"], "working")

        #Structure the request to the cluster
        if self.request["request_type"] == "downproc":
            self.download_integration()

        elif self.request["request_type"] in ("downsad", "downshelx"):
            self.download_sad()

        # MAD run
        elif self.request["request_type"] in ("downmad", "downmadshelx"):
            self.download_mad()

        #Download cell analysis result from sad run
        elif self.request["request_type"] in ("downsadcell",):
            self.download_sad_cell()

        elif self.request["request_type"] in ("download_mr",):
            self.downalod_mr()

        #Download cell analysis from a data analysis of a run
        elif self.request["request_type"] in ("download_int",):
            self.download_cell_analysis()

    def download_cell_analysis(self):
        """Handle the download of cell analysis data"""
        # Figure out what to transfer
        down_info = self.database.getDownIntegrateInfo(self.request)

        if down_info:
            # Update the request dict
            self.request["download_file"] = down_info[0]
            self.request["repr"] = down_info[1]

            # Enter the request into cloud_current
            self.database.addCloudCurrent(self.request)

            # Put request in to cluster to compress the image
            PerformAction(command=("DOWNLOAD", self.request, self.reply_settings),
                          settings=self.settings)

    def download_integration(self):
        """Handle download of an integration result"""

        # Figure out what and where to transfer
        down_info = self.database.getDownprocInfo(self.request)
        if down_info:

            # The fastint pipeline
            if len(down_info) == 2:
                #update the request dict
                self.request["download_file"] = down_info[0]
                self.request["repr"] = down_info[1]
                self.request["source_dir"] = False
                self.request["image_files"] = False
                self.request["work_dir"] = False

            # The xia2 pipeline
            elif len(down_info) == 4:
                source_dir, image_files, work_dir, _repr = down_info
                self.request["download_file"] = False
                self.request["source_dir"] = source_dir
                self.request["image_files"] = image_files
                self.request["work_dir"] = work_dir
                self.request["repr"] = _repr

            # Enter the request into cloud_current
            self.database.addCloudCurrent(self.request)

            # Put request in to cluster to compress the image
            PerformAction(command=("DOWNLOAD", self.request, self.reply_settings),
                          settings=self.settings)

        # Unsuccessful run, so nothing to download
        else:
            pass

    def download_mad(self):
        """Handle a MAD-based download"""

        # Figure out what and where to transfer
        down_info = self.database.getDownMadInfo(self.request)
        self.logger.debug(down_info)

        if down_info:
            # Update the request dict
            self.request["download_file"] = down_info[0]
            self.request["repr"] = down_info[1]

            # Enter the request into cloud_current
            self.database.addCloudCurrent(self.request)

            #put request in to cluster to compress the image
            PerformAction(command=("DOWNLOAD", self.request, self.reply_settings),
                          settings=self.settings)

    def downalod_mr(self):
        """Handle the download of an MR result"""

        # Figure out what to transfer
        down_info = self.database.getDownMrInfo(self.request)

        if down_info:
            # Update the request dict
            self.request["download_file"] = down_info[0]
            self.request["repr"] = down_info[1]

            # Enter the request into cloud_current
            self.database.addCloudCurrent(self.request)

            # Put request in to cluster to compress the image
            PerformAction(command=("DOWNLOAD", self.request, self.reply_settings),
                          settings=self.settings)

    def download_sad(self):
        """Handle a SAD-based download"""

        # Figure out what and where to transfer
        down_info = self.database.getDownSadInfo(self.request)
        self.logger.debug(down_info)

        if down_info:
            # Update the request dict
            self.request["download_file"] = down_info[0]
            self.request["repr"] = down_info[1]

            # Enter the request into cloud_current
            self.database.addCloudCurrent(self.request)

            # Put request in to cluster to compress the image
            PerformAction(command=("DOWNLOAD", self.request, self.reply_settings),
                          settings=self.settings)

    def download_sad_cell(self):
        """Handle the download of a SAD result from cell analysis step"""

        # Figure out what to transfer
        down_info = self.database.getDownSadCellInfo(self.request)

        if down_info:
            # Update the request dict
            self.request["download_file"] = down_info[0]
            self.request["repr"] = down_info[1]

            # Enter the request into cloud_current
            self.database.addCloudCurrent(self.request)

            # Put request in to cluster to compress the image
            PerformAction(command=("DOWNLOAD", self.request, self.reply_settings),
                          settings=self.settings)
