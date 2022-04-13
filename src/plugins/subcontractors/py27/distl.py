"""Methods for running DISTL in RAPD"""

"""
This file is part of RAPD

Copyright (C) 2017, Cornell University
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

__created__ = "2021-02-23"
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjpy@anl.gov"
__status__ = "Development"

import urllib2

from multiprocessing import Process
from utils.processes import local_subprocess

def process_distl_server(IP,
                         port,
                         image,
                         res_inner=50.0,
                         res_outer=3.0,
                         queue=False,
                         logfile=False,
                         logger=False):
    """
    Setup Distl for running on Distl server, if enabled. Results should come out in less than 1s.
    """
    if logger:
        logger.debug("process_distl_server")
    # Setup the URL for the DISTL server
    url = "http://%s:%d/spotfinder/distl.signal_strength?distl.image=%s&distl.bins.verbose=False&distl.res.outer=%.1f&distl.res.inner=%.1f" \
        %(IP, port, image, res_outer, res_inner)
    # Pass "+" signs correctly
    url = url.replace("+", "%2b")
    # Run URL and get response
    response = urllib2.urlopen(url)
    raw = response.read()
    response.close()
    # Save out as logfile
    if logfile:
        with open(logfile, 'w') as out_file:
            out_file.write(raw)
    # Pass results back to queue mimicking local_subprocess results
    if queue:
        queue.put({'stdout': raw})
    else:
        return raw

def process_distl_local(image,
                        res_inner=50.0,
                        res_outer=3.0,
                        queue=False,
                        logfile=False,
                        logger=False):
    """
    Run distl from command line on local machine. This takes several seconds to run so results should be put on queue or logfile.
    """
    if logger:
        logger.debug('process_distl_local')

    # Setup the command
    command = "distl.signal_strength %s distl.res.outer=%.1f distl.res.inner=%.1f distl.bins.verbose=False" \
        %(image, res_outer, res_inner)
    # Setup keywords
    kw = {"command": command}
    if queue:
        kw.update({"result_queue": queue})
    if logfile:
        kw.update({"logfile": logfile})
    # Launch the job
    job = Process(target=local_subprocess,
                  kwargs=kw)
    job.start()
    # send back job so main knows when it completes.
    return job
  
