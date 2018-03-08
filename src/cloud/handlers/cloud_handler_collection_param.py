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

__created__ = "2016-01-29"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

import logging
import threading

class Handler(threading.Thread):
    """
    Handles the signaling of the beamline with a datacollection setting in a separate thread.
    """

    def __init__(self,request,database,logger=None):
        """Initialize the handler"""

        self.logger = logging.getLogger("RAPDLogger")

        self.logger.info('DatacollectionHandler::__init__')
        logger.debug(request)

        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.request = request
        self.database = database

        # Start the handler
        self.start()

    def run(self):
        """The main event"""

        self.logger.debug('DatacollectionHandler::run')

        #get the timestamp into console format
        timestamp = self.request['timestamp'].replace('-','/').replace('T','_')[:-3]

        try:
            #send the request to the appropriate Console session
            myBEAMLINEMONITOR = BeamlineConnect(beamline=self.request['beamline'],
                                                logger=self.logger)

            myBEAMLINEMONITOR.PutDatacollectionRedis(timestamp=timestamp,
                                                       omega_start=self.request['omega_start'],
                                                       delta_omega=self.request['delta_omega'],
                                                       number_images=self.request['number_images'],
                                                       time=self.request['time'],
                                                       distance=self.request['distance'],
                                                       transmission=self.request['transmission'],
                                                       kappa=self.request['kappa'],
                                                       phi=self.request['phi'])

            #get rid of myBEAMLINEMONITOR
            myBEAMLINEMONITOR = None

            #mark that the request has been addressed
            self.database.markDatacollectionRequest(self.request['datacollection_id'],'complete')
        except:
            self.logger.exception('Error connecting to Console in DatacollectionHandler')
