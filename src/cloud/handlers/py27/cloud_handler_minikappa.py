"""
This file is part of RAPD

Copyright (C) 2009-2018, Cornell University
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

__created__ = "2009-11-22"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

import logging
import threading

class MinikappaHandler(threading.Thread):
    """
    Handles the signaling of the beamline with a minikappa setting in a separate thread.
    Designed for use at NE-CAT
    """

    def __init__(self, request, database):
        """
        Instantiate by saving passed variables and starting the thread.

        request - a dict describing the request
        database - instance of the rapd_database.Database
        """
        self.logger = logging.getLogger("RAPDLogger")
        self.logger.info('MinikappaHandler::__init__')
        self.logger.debug(request)

        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.request        = request
        self.database       = database

        self.start()

    def run(self):
        """
        The new thread
        """

        self.logger.debug('MinikappaHandler::run')

        #get the timestamp into console format
        timestamp = self.request['timestamp'].replace('-','/').replace('T','_')[:-3]

        try:
            #send the request to the appropriate Console session
            myBEAMLINEMONITOR = BeamlineConnect(beamline=self.request['beamline'],
                                                logger=self.logger )

            myBEAMLINEMONITOR.PutStac(timestamp=timestamp,
                                             omega=self.request['omega'],
                                             kappa=self.request['kappa'],
                                             phi=self.request['phi'])

            #get rid of myBEAMLINEMONITOR
            myBEAMLINEMONITOR = None

            #mark that the request has been addressed
            self.database.markMinikappaRequest(self.request['minikappa_id'],'complete')
        except:
            self.logger.debug('Error in connecting to Console')
