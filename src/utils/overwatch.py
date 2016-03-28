"""
This file is part of RAPD

Copyright (C) 2016 Cornell University
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

__created__ = "2016-03-18"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

"""
Provides tools for registration, autodiscovery, monitoring and launching
"""

# Standard imports
import multiprocessing

import redis

class Overwatch(object):
    """Provides microservice monitoring tools"""

    def __init__(self):
        """
        Set up the Overwatch
        """

        pass

    def register(self):
        """
        Register the process with the central db
        """
        pass

    def update(self):
        """
        Update the status with the central db
        """
        pass

    def discover(self):
        """
        Query for available services
        """
        pass



class Startover(multiprocessing.Process):
    """Provides methods for restarting failed microservices"""

    def __init__(self):
        """
        Setup the Startover
        """
        pass
