"""
This file is part of RAPD

Copyright (C) 2009-2016, Cornell University
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

__created__ = "2009-07-08"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

"""
rapd_adsc provides a connection to the adsc image computer by connecting
via xmlrpclib to rapd_adscserver running on the adsc data collection
computer

If you are adapting rapd to your locality, you will need to check this
carefully
"""

import json
# import logging
import os
import re
import time

# RAPD imports
# from rapd_utils import date_adsc_to_sql
import monitors.redis_monitor

def print_dict(in_dict):
    """Pring a dict in a pretty format"""
    keys = in_dict.keys()
    keys.sort()
    for key in keys:
        print key, '::', in_dict[key]
    print ''

MONTHS = {'Jan' : '01',
          'Feb' : '02',
          'Mar' : '03',
          'Apr' : '04',
          'May' : '05',
          'Jun' : '06',
          'Jul' : '07',
          'Aug' : '08',
          'Sep' : '09',
          'Oct' : '10',
          'Nov' : '11',
          'Dec' : '12'}

def zerofillday(day_in):
    """Return a zero-filled day string"""

    #print day_in
    intday = int(day_in)
    #print intday
    strday = str(intday)
    #print strday
    if len(strday) == 2:
        return strday
    else:
        return '0'+strday

def date_adsc_to_sql(datetime_in):
    """Convert date from ADSC to SQL format"""

    #print datetime_in
    spldate = datetime_in.split()
    #print spldate
    time_str = spldate[3]
    #print time_str
    year = spldate[4]
    #print year
    month = MONTHS[spldate[1]]
    #print month
    day = zerofillday(spldate[2])
    #print day

    date = '-'.join((year, month, day))
    #print date
    #print ' '.join((date,time_str))
    return 'T'.join((date, time_str))

class Monitor(monitors.redis_monitor.RedisMonitor):
    """Redis-based image collection signalling"""


def read_header(image, run_id=None, place_in_run=None):
    """
    Given a full file name for an ADSC image (as a string), read the header and
    return a dict with all the header info

    NB - This code was developed for the NE-CAT ADSC Q315, so the header is bound
         to be very specific.
    """

    #item:(pattern,transform)
    header_items = {"header_bytes" : (r"^HEADER_BYTES=\s*(\d+)\;", lambda x: int(x)),
                    "dim"          : (r"^DIM=\s*(\d+)\;", lambda x: int(x)),
                    "byte_order"   : (r"^BYTE_ORDER=\s*([\w_]+)\;", lambda x: str(x)),
                    "type"         : (r"^TYPE=\s*([\w_]+)\;", lambda x: str(x)),
                    "size1"        : (r"^SIZE1=\s*(\d+)\;", lambda x: int(x)),
                    "size2"        : (r"^SIZE2=\s*(\d+)\;", lambda x: int(x)),
                    "pixel_size"   : (r"^PIXEL_SIZE=\s*([\d\.]+)\;", lambda x: float(x)),
                    "bin"          : (r"^BIN=\s*(\w*)\;", lambda x: str(x)),
                    "adc"          : (r"^ADC=\s*(\w+)\;", lambda x: str(x)),
                    "detector_sn"  : (r"^DETECTOR_SN=\s*(\d+)\;", lambda x: int(x)),
                    "collect_mode" : (r"^COLLECT_MODE=\s*(\w*)\;", lambda x: str(x)),
                    "beamline"     : (r"^BEAMLINE=\s*(\w+)\;", lambda x: str(x)),
                    "date"         : (r"^DATE=\s*([\w\d\s\:]*)\;", date_adsc_to_sql),
                    "time"         : (r"^TIME=\s*([\d\.]+)\;", lambda x: float(x)),
                    "distance"     : (r"^DISTANCE=\s*([\d\.]+)\;", lambda x: float(x)),
                    "osc_range"    : (r"^OSC_RANGE=\s*([\d\.]+)\;", lambda x: float(x)),
                    "phi"          : (r"^PHI=\s*([\d\.]+)\;", lambda x: float(x)),
                    "osc_start"    : (r"^OSC_START=\s*([\d\.]+)\;", lambda x: float(x)),
                    "twotheta"     : (r"^TWOTHETA=\s*([\d\.]+)\;", lambda x: float(x)),
                    "thetadistance": (r"^THETADISTANCE=\s*([\d\.]+)\;", lambda x: float(x)),
                    #"axis"         : (r"^AXIS=\s*(\w+)\;", lambda x: str(x)),
                    "wavelength"   : (r"^WAVELENGTH=\s*([\d\.]+)\;", lambda x: float(x)),
                    "beam_center_x": (r"^BEAM_CENTER_X=\s*([\d\.]+)\;", lambda x: float(x)),
                    "beam_center_y": (r"^BEAM_CENTER_Y=\s*([\d\.]+)\;", lambda x: float(x)),
                    "transmission" : (r"^TRANSMISSION=\s*([\d\.]+)\;", lambda x: float(x)),
                    "puck"         : (r"^PUCK=\s*(\w+)\;", lambda x: str(x)),
                    "sample"       : (r"^SAMPLE=\s*([\d\w]+)\;", lambda x: str(x)),
                    "ring_cur"     : (r"^RING_CUR=\s*([\d\.]+)\;", lambda x: float(x)),
                    "ring_mode"    : (r"^RING_MODE=\s*(.*)\;", lambda x: str(x)),
                    "md2_aperture" : (r"^MD2_APERTURE=\s*(\d+)\;", lambda x: int(x)),
                    "period"       : (r"^# Exposure_period\s*([\d\.]+) s", lambda x: float(x)),
                    "count_cutoff" : (r"^# Count_cutoff\s*(\d+) counts", lambda x: int(x))}

    count = 0
    while count < 10:
        try:
            rawdata = open(image, "rb").read()
            headeropen = rawdata.index("{")
            headerclose = rawdata.index("}")
            header = rawdata[headeropen+1:headerclose-headeropen]
            break
            #print header
        except:
            count += 1
            time.sleep(0.1)

    try:
        #tease out the info from the file name
        base = os.path.basename(image).rstrip(".img")
        #the parameters
        parameters = {"fullname" : image,
                      "detector" : "ADSC-Q315",
                      # directory of the image file
                      "directory" : os.path.dirname(image),
                      # image name without directory or image suffix
                      "basename" : base,
                      # image name without directory, run_number, image_number or image suffix
                      "image_prefix" : "_".join(base.split("_")[0:-2]),
                      "run_number" : int(base.split("_")[-2]),
                      "image_number" : int(base.split("_")[-1]),
                      "axis" : "omega",
                      "run_id" : run_id,
                      "place_in_run" : place_in_run}

        for label, pat in header_items.iteritems():
            pattern = re.compile(pat[0], re.MULTILINE)
            matches = pattern.findall(header)
            if len(matches) > 0:
                parameters[label] = pat[1](matches[-1])
            else:
                parameters[label] = None

        # If twotheta is in use, distance = twothetadist
        try:
            if parameters["twotheta"] > 0 and parameters["thetadistance"] > 100:
                parameters["distance"] = parameters["thetadistance"]

        except:
            pass

        # Look for bad text in certain entries NECAT-code
        try:
            json.dumps(parameters["ring_mode"])
        except:
            parameters["ring_mode"] = "Error"

        # Return parameters to the caller
        return parameters

    except:
        pass

if __name__ == "__main__":

    """
    #If started on the command line, the header for the input file will be parsed and printed
    #print sys.argv[1]
    a = Q315ReadHeader("images/raster_snap_test_1_001.img")
    print_dict(a)
    """

    """
    #If started on the command line, run the AdscMonitor on the loclahost
    #set up logging
    LOG_FILENAME = "/tmp/rapd_adsc.log"
    # Set up a specific logger with our desired output level
    logger = logging.getLogger("RAPDLogger")
    logger.setLevel(logging.DEBUG)
    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=100000, backupCount=5)
    #add a formatter
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info("RAPD_ADSC.__main__")

    M= Q315_Monitor(beamline="Z",notify=None,reconnect=None,logger=logger)
    """

    """
    #testing
    #Test Hf4m_Monitor
    def notify(input):
        print input
    P = Hf4m_Monitor(beamline='E',notify=notify,reconnect=None,logger=None)
    """


    #Test the header reading
    test_image = "/gpfs9/users/harvard/Gaudet_E_1100/images/LBane/snaps/RG006_15_PAIR_0_0004.cbf"
    # header = Hf4mReadHeader(test_image)
    import pprint
    pp = pprint.PrettyPrinter()
    pp.pprint(header)
