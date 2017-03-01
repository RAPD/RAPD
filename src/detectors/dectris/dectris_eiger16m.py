"""Detector description for Dectris Eiger 9M"""

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

__created__ = "2017-02-13"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

# import threading
import argparse
import os
import pprint
import re
import shutil
import sys
import tempfile

# RAPD imports
import utils.convert_hdf5_cbf as convert_hdf5_cbf


DETECTOR = "dectris_eiger9m"
VENDROTYPE = "DECTRIS"

# Taken from Dectris data
XDSINP = {
    "MAX_CELL_ANGLE_ERROR": " 2.0",
    "MINIMUM_NUMBER_OF_PIXELS_IN_A_SPOT": "6",
    "VALUE_RANGE_FOR_TRUSTED_DETECTOR_PIXELS": " 6000 30000",
    "UNTRUSTED_RECTANGLE10": "    0 4151   3820 3858",
    "MIN_RFL_Rmeas": " 50",
    "NUMBER_OF_PROFILE_GRID_POINTS_ALONG_ALPHA/BETA": "21",
    "REFINE(INTEGRATE)": " POSITION ORIENTATION",
    "REFINE(CORRECT)": " POSITION BEAM ORIENTATION CELL AXIS",
    "INCLUDE_RESOLUTION_RANGE": "50.0 1.5",
    "REFINE(IDXREF)": " BEAM AXIS ORIENTATION CELL",
    "SPACE_GROUP_NUMBER": "197",
    "NX": " 4150 ",
    "NY": " 4371",
    "OVERLOAD": " 19405",
    "UNTRUSTED_RECTANGLE4": "    0 4151    514  552",
    "UNTRUSTED_RECTANGLE5": "    0 4151   1065 1103",
    "UNTRUSTED_RECTANGLE6": "    0 4151   1616 1654",
    "UNTRUSTED_RECTANGLE7": "    0 4151   2167 2205",
    "UNTRUSTED_RECTANGLE1": " 1030 1041      0 4372",
    "UNTRUSTED_RECTANGLE2": " 2070 2081      0 4372",
    "UNTRUSTED_RECTANGLE3": " 3110 3121      0 4372",
    "NUMBER_OF_PROFILE_GRID_POINTS_ALONG_GAMMA": "21",
    "UNTRUSTED_RECTANGLE8": "    0 4151   2718 2756",
    "UNTRUSTED_RECTANGLE9": "    0 4151   3269 3307",
    "FRACTION_OF_POLARIZATION": "0.99",
    "TEST_RESOLUTION_RANGE": " 8.0 4.5",
    "MAX_CELL_AXIS_ERROR": " 0.03",
    "DIRECTION_OF_DETECTOR_X-AXIS": " 1.0 0.0 0.0",
    "SENSOR_THICKNESS": "0.32",
    "POLARIZATION_PLANE_NORMAL": " 0.0 1.0 0.0",
    "MAX_FAC_Rmeas": " 2.0",
    "TRUSTED_REGION": "0.0 1.41",
    "ROTATION_AXIS": " 1.0 0.0 0.0",
    "MINIMUM_VALID_PIXEL_VALUE": "0",
    "QY": "0.075",
    "QX": "0.075 ",
    "INCIDENT_BEAM_DIRECTION": "0.0 0.0 1.0",
    "DIRECTION_OF_DETECTOR_Y-AXIS": " 0.0 1.0 0.0",
    "SEPMIN": "4.0",
    "CLUSTER_RADIUS": "2",
    "DETECTOR": "EIGER",
    }

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
        "detector": ("^# Detector\: ([\w\s]+)\, S\/N [\w\d\-]*\s*", lambda x: str(x)),
        "detector_sn": ("^# Detector\:[\w\s]+\, S\/N ([\w\d\-]*)\s*", lambda x: str(x)),
        "pixel_size": ("^# Pixel_size\s*(\d+)e-6 m.*", lambda x: int(x)/1000),
        "sensor_thickness": ("^#\sSilicon\ssensor\,\sthickness\s*([\d\.]+)\sm", lambda x: float(x)*1000),
        "time": ("^# Exposure_time\s*([\d\.]+) s", lambda x: float(x)),
        "period": ("^# Exposure_period\s*([\d\.]+) s", lambda x: float(x)),
        "count_cutoff": ("^# Count_cutoff\s*(\d+) counts", lambda x: int(x)),
        "wavelength": ("^# Wavelength\s*([\d\.]+) A", lambda x: float(x)),
        "distance": ("^# Detector_distance\s*([\d\.]+) m", mmorm),
        "beam_x": ("^# Beam_xy\s*\(([\d\.]+)\,\s[\d\.]+\) pixels", lambda x: float(x)),
        "beam_y": ("^# Beam_xy\s*\([\d\.]+\,\s([\d\.]+)\) pixels", lambda x: float(x)),
        "osc_start": ("^# Start_angle\s*([\d\.]+)\s*deg", lambda x: float(x)),
        "osc_range": ("^# Angle_increment\s*([\d\.]*)\s*deg", lambda x: float(x)),
        }

    rawdata = open(image,"rb").read(1024)
    headeropen = 0
    headerclose= rawdata.index("--CIF-BINARY-FORMAT-SECTION--")
    header = rawdata[headeropen:headerclose]

    # try:
    #tease out the info from the file name
    base = os.path.basename(image).rstrip(".cbf")

    parameters = {
        "fullname": image,
        # "detector": "EIGER",
        "directory": os.path.dirname(image),
        "image_prefix": "_".join(base.split("_")[0:-2]),
        # "run_number": int(base.split("_")[-2]),
        "image_number": int(base.split("_")[-1]),
        # "axis": "omega",
        # "collect_mode": mode,
        # "run_id": run_id,
        # "place_in_run": place_in_run,
        # "size1": 2463,
        # "size2": 2527}
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

    tmp_dir = False

    if test_image.endswith(".h5"):
        print "HDF5 file  - converting"

        tmp_dir = tempfile.mkdtemp()

        converter = convert_hdf5_cbf.hdf5_to_cbf_converter(master_file=test_image,
                                                           output_dir=tmp_dir,
                                                           prefix="tmp",
                                                           start_image=1,
                                                           end_image=1)
        converter.run()

        test_image = "%s/tmp00001.cbf" % tmp_dir

    # Read the header
    header = read_header(test_image)

    # And print it out
    pprint.pprint(header)

    if tmp_dir:
        shutil.rmtree(tmp_dir)

if __name__ == "__main__":

    # Get the commandline args
    commandline_args = get_commandline()

    # Execute code
    main(args=commandline_args)
