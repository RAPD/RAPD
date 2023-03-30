"""Detector description for Dectris Pilatus 6M"""

"""
This file is part of RAPD

Copyright (C) 2012-2018, Cornell University
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

# Standard imports
import argparse
import os
import pprint
import re
import sys
import time

# RAPD imports
# from rapd_site import secret_settings as secrets
# from rapd_utils import print_dict, date_adsc_to_sql

DETECTOR = "dectris_pilatus6m"
VENDORTYPE = "DECTRIS"

# XDS input information
XDS_FLIP_BEAM = True
XDSINP = [
    ('CLUSTER_RADIUS', '2') ,
    ('DETECTOR', 'PILATUS') ,
    ('DIRECTION_OF_DETECTOR_X-AXIS', '1 0 0') ,
    ('DIRECTION_OF_DETECTOR_Y-AXIS', '0 1 0') ,
    ('FRACTION_OF_POLARIZATION', '0.99') ,
    ('INCIDENT_BEAM_DIRECTION', '0 0 1') ,
    ('INCLUDE_RESOLUTION_RANGE', '200.0 0.0') ,
    ('MAX_CELL_ANGLE_ERROR', '2.0') ,
    ('MAX_CELL_AXIS_ERROR', '0.03') ,
    ('MAX_FAC_Rmeas', '2.0') ,
    ('MINIMUM_NUMBER_OF_PIXELS_IN_A_SPOT', '4') ,
    ('MINIMUM_VALID_PIXEL_VALUE', '0') ,
    ('MINIMUM_ZETA', '0.05') ,
    ('MIN_RFL_Rmeas', '50') ,
    ('NUMBER_OF_PROFILE_GRID_POINTS_ALONG_ALPHA/BETA', '13') ,
    ('NUMBER_OF_PROFILE_GRID_POINTS_ALONG_GAMMA', '9') ,
    ('NX', '2463') ,
    ('NY', '2527') ,
    ('OVERLOAD', '1048500') ,
    ('POLARIZATION_PLANE_NORMAL', '0 1 0') ,
    ('QX', '0.172') ,
    ('QY', '0.172') ,
    ('REFINE(CORRECT)', 'BEAM ORIENTATION CELL AXIS POSITION') ,
    ('REFINE(IDXREF)', 'BEAM AXIS ORIENTATION CELL') ,
    #('REFINE(INTEGRATE)', 'POSITION BEAM ORIENTATION CELL') ,
    ('REFINE(INTEGRATE)', 'BEAM ORIENTATION CELL') ,
    ('ROTATION_AXIS', '1 0 0') ,
    ('SENSOR_THICKNESS', '0.32') ,
    ('SEPMIN', '4') ,
    ('STRICT_ABSORPTION_CORRECTION', 'TRUE') ,
    ('STRONG_PIXEL', '6') ,
    ('TRUSTED_REGION', '0.0 1.05') ,
    ('UNTRUSTED_RECTANGLE1', ' 487  495     0 2527') ,
    ('UNTRUSTED_RECTANGLE10', '   0 2463  1255 1273') ,
    ('UNTRUSTED_RECTANGLE11', '   0 2463  1467 1485') ,
    ('UNTRUSTED_RECTANGLE12', '   0 2463  1679 1697') ,
    ('UNTRUSTED_RECTANGLE13', '   0 2463  1891 1909') ,
    ('UNTRUSTED_RECTANGLE14', '   0 2463  2103 2121') ,
    ('UNTRUSTED_RECTANGLE15', '   0 2463  2315 2333') ,
    ('UNTRUSTED_RECTANGLE2', ' 981  989     0 2527') ,
    ('UNTRUSTED_RECTANGLE3', '1475 1483     0 2527') ,
    ('UNTRUSTED_RECTANGLE4', '1969 1977     0 2527') ,
    ('UNTRUSTED_RECTANGLE5', '   0 2463   195  213') ,
    ('UNTRUSTED_RECTANGLE6', '   0 2463   407  425') ,
    ('UNTRUSTED_RECTANGLE7', '   0 2463   619  637') ,
    ('UNTRUSTED_RECTANGLE8', '   0 2463   831  849') ,
    ('UNTRUSTED_RECTANGLE9', '   0 2463  1043 1061') ,
    ('VALUE_RANGE_FOR_TRUSTED_DETECTOR_PIXELS', '7000 30000') ,
    ]

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
        logger.debug("read_header %s" % image)

    # Make sure the image is a full path image
    image = os.path.abspath(image)

    def mmorm(x):
        d = float(x)
        if (d < 2):
            return(d*1000)
        else:
            return(d)

    #item:(pattern,transform)
    header_items = {
        "beam_x": ("^# Beam_xy\s*\(([\d\.]+)\,\s[\d\.]+\) pixels", lambda x: float(x)),
        "beam_y": ("^# Beam_xy\s*\([\d\.]+\,\s([\d\.]+)\) pixels", lambda x: float(x)),
        "count_cutoff": ("^# Count_cutoff\s*(\d+) counts", lambda x: int(x)),
        "detector_sn": ("S\/N ([\w\d\-]*)\s*", lambda x: str(x)),
        "date": ("^# ([\d\-]+T[\d\.\:]+)\s*", lambda x: str(x)),
        "distance": ("^# Detector_distance\s*([\d\.]+) m",mmorm),
        "excluded_pixels": ("^# Excluded_pixels\:\s*([\w\.]+)", lambda x: str(x)),
        "flat_field": ("^# Flat_field\:\s*([\(\)\w\.]+)", lambda x: str(x)),
        "gain": ("^# Gain_setting\:\s*([\s\(\)\w\.\-\=]+)", lambda x: str(x).rstrip()),
        "n_excluded_pixels": ("^# N_excluded_pixels\s\=\s*(\d+)", lambda x: int(x)),
        "osc_range": ("^# Angle_increment\s*([\d\.]*)\s*deg", lambda x: float(x)),
        "osc_start": ("^# Start_angle\s*([\d\.]+)\s*deg", lambda x: float(x)),
        "period": ("^# Exposure_period\s*([\d\.]+) s", lambda x: float(x)),
        "pixel_size": ("^# Pixel_size\s*(\d+)e-6 m.*", lambda x: int(x)/1000),
        "sensor_thickness": ("^#\sSilicon\ssensor\,\sthickness\s*([\d\.]+)\sm", lambda x: float(x)*1000),
        "tau": ("^#\sTau\s\=\s*([\d\.]+e\-09) s", lambda x: float(x)),
        "threshold": ("^#\sThreshold_setting\:\s*(\d+)\seV", lambda x: int(x)),
        "time": ("^# Exposure_time\s*([\d\.]+) s", lambda x: float(x)),
        "transmission": ("^# Filter_transmission\s*([\d\.]+)", lambda x: float(x)),
        "trim_file": ("^#\sTrim_file\:\s*([\w\.]+)", lambda x:str(x).rstrip()),
        "twotheta": ("^# Detector_2theta\s*([\d\.]*)\s*deg", lambda x: float(x)),
        "wavelength": ("^# Wavelength\s*([\d\.]+) A", lambda x: float(x)),
        "size1": ("X-Binary-Size-Fastest-Dimension:\s*([\d\.]+)", lambda x: int(x)),
        "size2": ("X-Binary-Size-Second-Dimension:\s*([\d\.]+)", lambda x: int(x)),
        }

    count = 0
    while (count < 10):
        try:
             # Use 'with' to make sure file closes properly. Only read header.
            header = ""
            with open(image, "rb") as raw:
                for line in raw:
                    header += line
                    if line.count("X-Binary-Size-Padding"):
                        break
            break
        except:
            count +=1
            if logger:
                logger.exception('Error opening %s' % image)
            time.sleep(0.1)

    # try:
    #tease out the info from the file name
    base = os.path.basename(image).rstrip(".cbf")

    parameters = {
        "fullname": image,
        "detector": "PILATUS",
        "directory": os.path.dirname(image),
        "image_prefix": "_".join(base.split("_")[0:-2]),
        "run_number": int(base.split("_")[-2]),
        "image_number": int(base.split("_")[-1]),
        "axis": "omega",
        #"collect_mode": mode,
        #"run_id": run_id,
        #"place_in_run": place_in_run,
        #"size1": 2463,
        #"size2": 2527
        }

    for label, pat in header_items.iteritems():
        # print label
        pattern = re.compile(pat[0], re.MULTILINE)
        matches = pattern.findall(header)
        if len(matches) > 0:
            parameters[label] = pat[1](matches[-1])
        else:
            parameters[label] = None

    # Put beam center into RAPD format mm
    parameters["x_beam"] = parameters["beam_y"] * parameters["pixel_size"]
    parameters["y_beam"] = parameters["beam_x"] * parameters["pixel_size"]

    return(parameters)

    # except:
    #     if logger:
    #         logger.exception('Error reading the header for image %s' % image)

def get_commandline():
    """
    Grabs the commandline
    """

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Parse Pilatus header"
    parser = argparse.ArgumentParser(description=commandline_description)

    # A True/False flag
    parser.add_argument("-c", "--commandline",
                        action="store_true",
                        dest="commandline",
                        help="Generate commandline argument parsing")

    # File name to be generated
    parser.add_argument(action="store",
                        dest="file",
                        nargs="?",
                        default=False,
                        help="Name of file to be generated")

    return parser.parse_args()

def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    if args.file:
        test_image = args.file
    else:
        raise Error("No test image input!")

    # Read the header
    header = read_header(test_image)

    # And print it out
    pprint.pprint(header)


if __name__ == "__main__":

    # Get the commandline args
    commandline_args = get_commandline()

    # Execute code
    main(args=commandline_args)
