"""
This file is part of RAPD

Copyright (C) 2012-2017, Cornell University
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

__created__ = "2012-02-07"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

import threading
import time
import os
import re
import sys
import json
import logging, logging.handlers
import atexit
from rapd_site import secret_settings as secrets
from rapd_utils import print_dict, date_adsc_to_sql

DETECTOR = "dectris_pilatus6m"
VENDROTYPE = "DECTRIS"

def read_header(image,
                mode=None,
                run_id=None,
                place_in_run=None,
                logger=False):
    """
    Given a full file name for a Piltus image (as a string), read the header and
    return a dict with all the header info
    """
    # print "determine_flux %s" % image
    if logger:
        logger.debug('determine_flux %s' % image)

    def mmorm(x):
        d = float(x)
        if (d < 2):
            return(d*1000)
        else:
            return(d)

    #item:(pattern,transform)
    header_items = { 'detector_sn'  : ("S\/N ([\w\d\-]*)\s*", lambda x: str(x)),
                     'date'         : ("^# ([\d\-]+T[\d\.\:]+)\s*", lambda x: str(x)),
                     'pixel_size'   : ("^# Pixel_size\s*(\d+)e-6 m.*", lambda x: int(x)),
                     'time'         : ("^# Exposure_time\s*([\d\.]+) s", lambda x: float(x)),
                     'period'       : ("^# Exposure_period\s*([\d\.]+) s", lambda x: float(x)),
                     'count_cutoff' : ("^# Count_cutoff\s*(\d+) counts", lambda x: int(x)),
                     'wavelength'   : ("^# Wavelength\s*([\d\.]+) A", lambda x: float(x)),
                     'distance'     : ("^# Detector_distance\s*([\d\.]+) m",mmorm),
	                 'transmission' : ("^# Filter_transmission\s*([\d\.]+)", lambda x: float(x)),
                     'osc_start'    : ("^# Start_angle\s*([\d\.]+)\s*deg", lambda x: float(x)),
                     'osc_range'    : ("^# Angle_increment\s*([\d\.]*)\s*deg", lambda x: float(x)),
                     'twotheta'     : ("^# Detector_2theta\s*([\d\.]*)\s*deg", lambda x: float(x))}

    count = 0
    while (count < 10):
    	try:
            rawdata = open(image,"rb").read(1024)
            headeropen = 0
            headerclose= rawdata.index("--CIF-BINARY-FORMAT-SECTION--")
            header = rawdata[headeropen:headerclose]
            break
        except:
            count +=1
            if logger:
                logger.exception('Error opening %s' % image)
            time.sleep(0.1)

    try:
        #tease out the info from the file name
        base = os.path.basename(image).rstrip(".cbf")

        parameters = {'fullname'     : image,
                      'detector'     : 'PILATUS',
                      'directory'    : os.path.dirname(image),
                      'image_prefix' : "_".join(base.split("_")[0:-2]),
                      'run_number'   : int(base.split("_")[-2]),
                      'image_number' : int(base.split("_")[-1]),
                      'axis'         : 'omega',
                      'collect_mode' : mode,
                      'run_id'       : run_id,
                      'place_in_run' : place_in_run,
                      'size1'        : 2463,
                      'size2'        : 2527}

        for label,pat in header_items.iteritems():
            # print label
            pattern = re.compile(pat[0], re.MULTILINE)
            matches = pattern.findall(header)
            if len(matches) > 0:
                parameters[label] = pat[1](matches[-1])
            else:
                parameters[label] = None

        return(parameters)

    except:
        if logger:
            logger.exception('Error reading the header for image %s' % image)


if __name__ == "__main__":

    #Test the header reading
    test_image = "/gpfs7/users/mit/schwartz_C_535/images/schwartz/snaps/0_0/TgC1_4_7_0_0002.cbf"
    header = read_header(test_image)
    import pprint
    P = pprint.PrettyPrinter()
    P.pprint(header)
