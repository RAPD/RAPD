"""
Detector description for LS-CAT Eiger 9M
Designed to read the CBF version of the Eiger file
"""

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

__created__ = "2017-03-01"
_maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
from collections import OrderedDict
import os
from pprint import pprint
import re

# RAPD imports
# commandline_utils
# detectors.detector_utils as detector_utils
# utils

# Dectris Pilatus 6M
import detectors.dectris.dectris_eiger16m as detector
import detectors.detector_utils as utils

# Detector information
# The RAPD detector type
DETECTOR = "dectris_eiger16m"
# The detector vendor as it appears in the header
VENDORTYPE = "Eiger-16M"
# The detector serial number as it appears in the header
DETECTOR_SN = "Dectris Eiger 16M S/N E-32-0108"
# The detector suffix "" if there is no suffix
DETECTOR_SUFFIX = ".cbf"
# Template for image name generation ? for frame number places
IMAGE_TEMPLATE = "%s_%d_??????.cbf" # prefix & run number
# Is there a run number in the template?
RUN_NUMBER_IN_TEMPLATE = True
# This is a version number for internal RAPD use
# If the header changes, increment this number
HEADER_VERSION = 1

# XDS information for constructing the XDS.INP file
# Import from more generic detector
XDS_FLIP_BEAM = detector.XDS_FLIP_BEAM
# XDSINP = detector.XDSINP
# Update the XDS information from the imported detector
XDSINP = OrderedDict([
    ("REFINE(CORRECT)", "POSITION DISTANCE BEAM ORIENTATION CELL AXIS"),
    ("REFINE(IDXREF)", "BEAM AXIS ORIENTATION CELL"),
    ("REFINE(INTEGRATE)", "POSITION DISTANCE BEAM ORIENTATION CELL"),
    ("STRICT_ABSORPTION_CORRECTION", "TRUE"),
    ("TRUSTED_REGION", "0.00 1.2"),
    ("VALUE_RANGE_FOR_TRUSTED_DETECTOR_PIXELS", "8000. 30000."),
    ("MINIMUM_ZETA", "0.05"),
    ("CORRECTIONS", "DECAY MODULATION ABSORP"),
    ("STRONG_PIXEL", "6"),
    ("MINIMUM_NUMBER_OF_PIXELS_IN_A_SPOT", "4"),
    ("MINIMUM_FRACTION_OF_INDEXED_SPOTS", "0.25"),
    ("SEPMIN", "4"),
    ("CLUSTER_RADIUS", "2"),
    ("NUMBER_OF_PROFILE_GRID_POINTS_ALONG_ALPHA/BETA", "13"),
    ("NUMBER_OF_PROFILE_GRID_POINTS_ALONG_GAMMA", "9"),
    ("DETECTOR", "EIGER"),
    ("MINIMUM_VALID_PIXEL_VALUE", "0"),
    ("OVERLOAD", "3000000"),
    ("SENSOR_THICKNESS", "0.32"),
    ("QX", "0.075 "),
    ("QY", "0.075"),
    ("NX", "4150"),
    ("NY", "4371"),
    ("DIRECTION_OF_DETECTOR_X-AXIS", "1 0 0"),
    ("DIRECTION_OF_DETECTOR_Y-AXIS", "0 1 0"),
    ("INCIDENT_BEAM_DIRECTION", "0 0 1"),
    ("ROTATION_AXIS", "1 0 0"),
    ("FRACTION_OF_POLARIZATION", "0.99"),
    ("POLARIZATION_PLANE_NORMAL", "0 1 0"),
    ("UNTRUSTED_RECTANGLE1", "    0 4151    514  552"),
    ("UNTRUSTED_RECTANGLE2", "    0 4151   1065 1103"),
    ("UNTRUSTED_RECTANGLE3", "    0 4151   1616 1654"),
    ("UNTRUSTED_RECTANGLE4", "    0 4151   2167 2205"),
    ("UNTRUSTED_RECTANGLE5", "    0 4151   2718 2756"),
    ("UNTRUSTED_RECTANGLE6", "    0 4151   3269 3307"),
    ("UNTRUSTED_RECTANGLE7", "    0 4151   3820 3858"),
    ("UNTRUSTED_RECTANGLE8", "    0 4151    225  260"),
    ("UNTRUSTED_RECTANGLE9", "    0 4151    806  811"),
    ("UNTRUSTED_RECTANGLE10", "    0 4151   1357 1362"),
    ("UNTRUSTED_RECTANGLE11", "    0 4151   1908 1913"),
    ("UNTRUSTED_RECTANGLE12", "    0 4151   2459 2464"),
    ("UNTRUSTED_RECTANGLE13", "    0 4151   3010 3015"),
    ("UNTRUSTED_RECTANGLE14", "    0 4151   3561 3566"),
    ("UNTRUSTED_RECTANGLE15", "    0 4151   4112 4117"),
    ("UNTRUSTED_RECTANGLE16", " 1030 1041      0 4372"),
    ("UNTRUSTED_RECTANGLE17", " 2070 2081      0 4372"),
    ("UNTRUSTED_RECTANGLE18", " 3110 3121      0 4372"),
    ])

def parse_file_name(fullname):
    """
    Parse the fullname of an image and return
    (directory, basename, prefix, run_number, image_number)
    Keyword arguments
    fullname -- the full path name of the image file
    """
    # Directory of the file
    directory = os.path.dirname(fullname)

    # The basename of the file (i.e. basename - suffix)
    basename = os.path.basename(fullname).rstrip(DETECTOR_SUFFIX)

    # The prefix, image number, and run number
    sbase = basename.split("_")
    prefix = "_".join(sbase[0:-2])
    image_number = int(sbase[-1])
    run_number = int(sbase[-2])
    return directory, basename, prefix, run_number, image_number

def create_image_fullname(directory,
                          image_prefix,
                          run_number=None,
                          image_number=None):
    """
    Create an image name from parts - the reverse of parse

    Keyword arguments
    directory -- in which the image file appears
    image_prefix -- the prefix before run number or image number
    run_number -- number for the run
    image_number -- number for the image
    """

    filename = IMAGE_TEMPLATE.replace("??????", "%06d") % (image_prefix, run_number, image_number)

    fullname = os.path.join(directory, filename)

    return fullname

def create_image_template(image_prefix, run_number):
    """
    Create an image template for XDS
    """

    print "create_image_template %s %d" % (image_prefix, run_number)

    image_template = IMAGE_TEMPLATE % (image_prefix, run_number)

    print "image_template: %s" % image_template

    return image_template

def get_data_root_dir(fullname):
    """
    Derive the data root directory from the user directory
    The logic will most likely be unique for each site

    Keyword arguments
    fullname -- the full path name of the image file
    """

    # Isolate distinct properties of the images path
    path_split = fullname.split(os.path.sep)
    data_root_dir = os.path.join("/", *path_split[1:3])

    # Return the determined directory
    return data_root_dir

def base_read_header(image,
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
    header_items = header_items = {
        "beam_x": ("^# Beam_xy\s*\(([\d\.]+)\,\s[\d\.]+\) pixels", lambda x: float(x)),
        "beam_y": ("^# Beam_xy\s*\([\d\.]+\,\s([\d\.]+)\) pixels", lambda x: float(x)),
        "count_cutoff": ("^# Count_cutoff\s*(\d+) counts", lambda x: int(x)),
        "detector_sn": ("S\/N ([\w\d\-]*)\s*", lambda x: str(x)),
        "date": ("^# ([\d\-]+T[\d\.\:]+)\s*", lambda x: str(x)),
        "distance": ("^# Detector_distance\s*([\d\.]+) m", mmorm),
        "excluded_pixels": ("^# Excluded_pixels\:\s*([\w\.]+)", lambda x: str(x)),
        "flat_field": ("^# Flat_field\:\s*([\(\)\w\.]+)", lambda x: str(x)),
        "gain": ("^# Gain_setting\:\s*([\s\(\)\w\.\-\=]+)", lambda x: str(x).rstrip()),
        "n_excluded_pixels": ("^# N_excluded_pixels\s\=\s*(\d+)", lambda x: int(x)),
        "osc_range": ("^# Angle_increment\s*([\d\.]*)\s*deg", lambda x: float(x)),
        "osc_start": ("^# Start_angle\s*([\d\.]+)\s*deg", lambda x: float(x)),
        "period": ("^# Exposure_period\s*([\d\.]+) s", lambda x: float(x)),
        "pixel_size": ("^# Pixel_size\s*([\.\d]+)e-6 m.*", lambda x: float(x)/1000.0),
        "sensor_thickness": ("^#\sSilicon\ssensor\,\sthickness\s*([\d\.]+)\sm", lambda x: float(x)*1000),
        "tau": ("^#\sTau\s\=\s*([\d\.]+e\-09) s", lambda x: float(x)),
        "threshold": ("^#\sThreshold_setting\:\s*([\d\.]+)\seV", lambda x: float(x)),
        "time": ("^# Exposure_time\s*([\d\.]+) s", lambda x: float(x)),
        "transmission": ("^# Filter_transmission\s*([\d\.]+)", lambda x: float(x)),
        "trim_file": ("^#\sTrim_file\:\s*([\w\.]+)", lambda x:str(x).rstrip()),
        "twotheta": ("^# Detector_2theta\s*([\d\.]*)\s*deg", lambda x: float(x)),
        "wavelength": ("^# Wavelength\s*([\d\.]+) A", lambda x: float(x))
        }

    rawdata = open(image,"rb").read(2048)
    headeropen = 0
    headerclose= rawdata.index("--CIF-BINARY-FORMAT-SECTION--")
    header = rawdata[headeropen:headerclose]

    # try:
    #tease out the info from the file name
    base = os.path.basename(image).rstrip(".cbf")

    parameters = {
        "fullname": image,
        "detector": "Eiger-16M",
        "directory": os.path.dirname(image),
        "image_prefix": "_".join(base.split("_")[0:-2]),
        # "run_number": int(base.split("_")[-2]),
        "image_number": int(base.split("_")[-1]),
        "axis": "omega",
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

    pprint(parameters)

    # Put beam center into RAPD format mm
    parameters["x_beam"] = parameters["beam_y"] * parameters["pixel_size"]
    parameters["y_beam"] = parameters["beam_x"] * parameters["pixel_size"]

    return(parameters)

    # except:
    #     if logger:
    #         logger.exception('Error reading the header for image %s' % image)

def read_header(input_file=False, beam_settings=False):
    """
    Read header from image file and return dict

    Keyword variables
    fullname -- full path name of the image file to be read
    beam_settings -- source information from site file
    """

    # Perform the header read from the file
    # If you are importing another detector, this should work
    if input_file.endswith(".h5"):
        header = utils.read_hdf5_header(input_file)

    elif input_file.endswith(".cbf"):
        header = base_read_header(input_file)
        # header = detector.read_header(input_file)

    basename = os.path.basename(input_file)
    header["image_prefix"] = "_".join(basename.replace(".cbf", "").split("_")[:-2])
    header["run_number"] = int(basename.replace(".cbf", "").split("_")[-1])

    # Add tag for module to header
    header["rapd_detector_id"] = "necat_dectris_eiger16m"

    # The image template for processing
    header["image_template"] = IMAGE_TEMPLATE % (header["image_prefix"], header["run_number"])
    header["run_number_in_template"] = RUN_NUMBER_IN_TEMPLATE

    # Return the header
    return header

def get_commandline():
    """
    Grabs the commandline
    """

    print "get_commandline"

    # Parse the commandline arguments
    commandline_description = "Generate a generic RAPD file"
    parser = argparse.ArgumentParser(description=commandline_description)

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

    print "main"

    if args.file:
        test_image = os.path.abspath(args.file)
    else:
        raise Error("No test image input!")

    # Read the header
    if test_image.endswith(".h5"):
        header = read_header(hdf5_file=test_image)
    elif test_image.endswith(".cbf"):
        header = read_header(cbf_file=test_image)

    # And print it out
    pprint(header)

if __name__ == "__main__":

    # Get the commandline args
    commandline_args = get_commandline()

    # Execute code
    main(args=commandline_args)
