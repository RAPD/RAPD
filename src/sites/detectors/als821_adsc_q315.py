"""
This file is part of RAPD

Copyright (C) 2016-2021 Cornell University
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

__created__ = "2016-03-20"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import math
import os
from pprint import pprint
import re
import sys

# RAPD imports
import detectors.adsc.adsc_q315 as detector
import detectors.detector_utils as utils
"""
Header from ALS 8.2.1 test image
{
HEADER_BYTES= 1024;
DIM=2;
TYPE=unsigned_short;
BYTE_ORDER=little_endian;
BIN=2x2;
DETECTOR_SN=905;
BEAM_CENTER_X=147.1;
BEAM_CENTER_Y=156.000000;
DENZO_XBEAM=147.100000;
DENZO_YBEAM=156.0;
TIME=1;
DATE=Wed Aug 19 14:34:50 PDT 2015;
TWOTHETA=0.063008;
DISTANCE=250.000000;
OSC_RANGE=1.000000;
PHI=70.17;
OSC_START=70.17;
AXIS=phi;
PIXEL_SIZE=0.1024;
WAVELENGTH=1;
LOGNAME=55879:55110;
CREV=1;
CCD=TH7899;
BIN_TYPE=SW;
ACC_TIME=1797;
UNIF_PED=1500;
IMAGE_PEDESTAL=40;
SIZE1=3072;
SIZE2=3072;
CCD_IMAGE_SATURATION=65535;
}
"""

# Detector information
DETECTOR = "adsc_q315"
VENDORTYPE = "ADSC"
DETECTOR_SN = 905
DETECTOR_SUFFIX = ".img"
IMAGE_TEMPLATE = "%s_%d_?????.img"
RUN_NUMBER_IN_TEMPLATE = True
HEADER_VERSION = 1

# XDS input information
XDS_FLIP_BEAM = detector.XDS_FLIP_BEAM
# Import from more generic detector
XDSINP0 = detector.XDSINP
# Update the XDS information from the imported detector
# only if there are differnces or new keywords.
# The tuple should contain two items (key and value)
# ie. XDSINP1 = [("SEPMIN", "4"),]
XDSINP1 = [(),
          ]
XDSINP = utils.merge_xds_input(XDSINP0, XDSINP1)


def parse_file_name(fullname):
    """Parse the fullname of an image and return
    (directory, basename, prefix, run_number, image_number)
    """

    directory = os.path.dirname(fullname)
    basename = os.path.basename(fullname).rstrip(DETECTOR_SUFFIX)
    sbase = basename.split("_")
    prefix = "_".join(sbase[0:-2])
    image_number = int(sbase[-1])
    run_number = int(sbase[-2])

    return directory, basename, prefix, run_number, image_number

def create_image_fullname(directory,
                          image_prefix,
                          run_number,
                          image_number):
    """Create an image name from parts - the reverse of parse"""

    fullname = os.path.join(directory, "%s_%d_%03d%s") % (
        image_prefix,
        run_number,
        image_number,
        DETECTOR_SUFFIX)

    return fullname

def create_image_template(image_prefix, run_number):
    """
    Create an image template for XDS
    """

    image_template = IMAGE_TEMPLATE % (image_prefix, run_number)

    return image_template

# Calculate the flux of the beam
def calculate_flux(input_header, beam_settings=False):
    """Return the flux and size of the beam given parameters"""

    if beam_settings:
        # Save some typing
        beam_size_raw_x = beam_settings["BEAM_SIZE_X"]
        beam_size_raw_y = beam_settings["BEAM_SIZE_Y"]
        aperture_size = input_header["aperture_x"]
        raw_flux = beam_settings["BEAM_FLUX"] * input_header["transmission"] / 100.0

        # Calculate the size of the beam incident on the sample in mm
        beam_size_x = min(beam_size_raw_x, aperture_size)
        beam_size_y = min(beam_size_raw_y, aperture_size)

        # Calculate the raw beam area
        if beam_settings["BEAM_SHAPE"] == "ellipse":
            raw_beam_area = math.pi * beam_size_raw_x * beam_size_raw_y
        elif beam_settings["BEAM_SHAPE"] == "rectangle":
            raw_beam_area = beam_size_raw_x * beam_size_raw_y

        # Calculate the incident beam area
        # Aperture is smaller than the beam in x & y
        if beam_size_x <= beam_size_raw_x and beam_size_y <= beam_size_raw_y:
            if beam_settings["BEAM_APERTURE_SHAPE"] == "circle":
                beam_area = math.pi * (beam_size_x / 2)**2
            elif beam_settings["BEAM_APERTURE_SHAPE"] == "rectangle":
                beam_area = beam_size_x * beam_size_y

        # Getting the raw beam coming through
        elif beam_size_x > beam_size_raw_x and beam_size_y > beam_size_raw_y:
            if beam_settings["BEAM_SHAPE"] == "ellipse":
                beam_area = math.pi * (beam_size_x / 2) * (beam_size_y / 2)
            elif beam_settings["BEAM_SHAPE"] == "rectangle":
                beam_area = beam_size_x * beam_size_y

        # Aperture is not smaller than beam in both directions
        else:
            if beam_settings["BEAM_APERTURE_SHAPE"] == "circle":
                # Use an ellipse as an imperfect description of this case
                beam_area = math.pi * (beam_size_x / 2) * (beam_size_y / 2)

        # Calculate the flux
        flux = raw_flux * (beam_area / raw_beam_area)

        return flux, beam_size_x/1000.0, beam_size_y/1000.0

def calculate_beam_center(distance, beam_settings={}, v_offset=0):
    """ Return a beam center, given a distance and vertical offset"""

    x_coeff = beam_settings["BEAM_CENTER_X"]
    y_coeff = beam_settings["BEAM_CENTER_Y"]

    x_beam = distance**6 * x_coeff[6] + \
             distance**5 * x_coeff[5] + \
             distance**4 * x_coeff[4] + \
             distance**3 * x_coeff[3] + \
             distance**2 * x_coeff[2] + \
             distance * x_coeff[1] + \
             x_coeff[0] + \
             v_offset

    y_beam = distance**6 * y_coeff[6] + \
             distance**5 * y_coeff[5] + \
             distance**4 * y_coeff[4] + \
             distance**3 * y_coeff[3] + \
             distance**2 * y_coeff[2] + \
             distance * y_coeff[1] + \
             y_coeff[0]

    return x_beam, y_beam

def read_header_base(image, run_id=None, place_in_run=None):
    """
    Given a full file name for an ADSC image (as a string), read the header and
    return a dict with all the header info

    NB - This code was modified from the NE-CAT ADSC Q315, specifically for this
         detector
    """

    #item:(pattern,transform)
    header_items = {
        "acc_time": (r"^ACC_TIME=\s*(\d+)\;", lambda x: int(x)),
        "axis": (r"^AXIS=\s*(\w+)\;", lambda x: str(x)),
        "beam_center_x": (r"^BEAM_CENTER_X=\s*([\d\.]+)\;", lambda x: float(x)),
        "beam_center_y": (r"^BEAM_CENTER_Y=\s*([\d\.]+)\;", lambda x: float(x)),
        "bin": (r"^BIN=\s*(\w*)\;", lambda x: str(x)),
        "bin_type": (r"^BIN_TYPE=\s*(\w*)\;", lambda x: str(x)),
        "byte_order": (r"^BYTE_ORDER=\s*([\w_]+)\;", lambda x: str(x)),
        "ccd": (r"^CCD=\s*([\w_]+)\;", lambda x: str(x)),
        "ccd_image_saturation": (r"^CCD_IMAGE_SATURATION=\s*(\d+)\;", lambda x: int(x)),
        "crev": (r"^CREV=\s*(\d+)\;", lambda x: int(x)),
        "date": (r"^DATE=\s*([\w\d\s\:]*)\;", lambda x: str(x)),
        "denzo_beam_center_x": (r"^DENZO_XBEAM=\s*([\d\.]+)\;", lambda x: float(x)),
        "denzo_beam_center_y": (r"^DENZO_YBEAM=\s*([\d\.]+)\;", lambda x: float(x)),
        "detector_sn": (r"^DETECTOR_SN=\s*(\d+)\;", lambda x: int(x)),
        "dim": (r"^DIM=\s*(\d+)\;", lambda x: int(x)),
        "distance": (r"^DISTANCE=\s*([\d\.]+)\;", lambda x: float(x)),
        "header_bytes": (r"^HEADER_BYTES=\s*(\d+)\;", lambda x: int(x)),
        "image_pedestal": (r"^IMAGE_PEDESTAL=\s*(\d+)\;", lambda x: int(x)),
        "logname": (r"^LOGNAME=\s*(.*)\;", lambda x: str(x)),
        "osc_range": (r"^OSC_RANGE=\s*([\d\.]+)\;", lambda x: float(x)),
        "osc_start": (r"^OSC_START=\s*([\d\.]+)\;", lambda x: float(x)),
        "phi": (r"^PHI=\s*([\d\.]+)\;", lambda x: float(x)),
        "pixel_size": (r"^PIXEL_SIZE=\s*([\d\.]+)\;", lambda x: float(x)),
        "size1": (r"^SIZE1=\s*(\d+)\;", lambda x: int(x)),
        "size2": (r"^SIZE2=\s*(\d+)\;", lambda x: int(x)),
        "time": (r"^TIME=\s*([\d\.]+)\;", lambda x: float(x)),
        "twotheta": (r"^TWOTHETA=\s*([\d\.]+)\;", lambda x: float(x)),
        "type": (r"^TYPE=\s*([\w_]+)\;", lambda x: str(x)),
        "unif_ped": (r"^UNIF_PED=\s*(\d+)\;", lambda x: int(x)),
        "wavelength": (r"^WAVELENGTH=\s*([\d\.]+)\;", lambda x: float(x)),
        }
    count = 0
    while count < 10:
        try:
            rawdata = open(image, "rb").read()
            headeropen = rawdata.index("{")
            headerclose = rawdata.index("}")
            header = rawdata[headeropen+1:headerclose-headeropen]
            break
        except:
            count += 1
            time.sleep(0.1)

    # Tease out the info from the file name
    base = os.path.basename(image).rstrip(".img")
    # The parameters
    parameters = {"fullname": image,
                  "detector": "ADSC-Q315",
                  # directory of the image file
                  "directory": os.path.dirname(image),
                  # image name without directory or image suffix
                  "basename": base,
                  # image name without directory, run_number, image_number or image suffix
                  "image_prefix": "_".join(base.split("_")[0:-2]),
                  "run_number": int(base.split("_")[-2]),
                  "image_number": int(base.split("_")[-1]),
                  "run_id": run_id,
                  "place_in_run": place_in_run}

    for label, pat in header_items.iteritems():
        pattern = re.compile(pat[0], re.MULTILINE)
        matches = pattern.findall(header)
        if len(matches) > 0:
            parameters[label] = pat[1](matches[-1])
        else:
            parameters[label] = None

    # Translate the wavelength to energy E = hc/lambda
    parameters["energy"] = 1239.84193 / parameters["wavelength"]

    parameters["count_cutoff"] = parameters["ccd_image_saturation"]

    # Return parameters to the caller
    return parameters

def read_header(fullname, beam_settings={}, run_id=None, place_in_run=None):
    """Read the NE-CAT ADSC Q315 header and add some site-specific data"""

    # Perform the header read form the file
    header = read_header_base(fullname, run_id, place_in_run)

    # # Massage header values
    # header["aperture_x"] = header["aperture"]
    # header["aperture_y"] = header["aperture_x"]
    # del header["aperture"]

    if beam_settings:
        # Perform flux calculation
        flux, beam_size_x, beam_size_y = calculate_flux(header, beam_settings)
        header["flux"] = flux
        header["beam_size_x"] = beam_size_x
        header["beam_size_y"] = beam_size_y

        # Add source parameters
        header["gauss_x"] = beam_settings["BEAM_GAUSS_X"]
        header["gauss_y"] = beam_settings["BEAM_GAUSS_Y"]

        # Calculate beam center - cannot be done with just header information!
        calc_beam_center_x, calc_beam_center_y = calculate_beam_center(
            distance=header["distance"],
            beam_settings=beam_settings,
            v_offset=0)
        header["x_beam"] = calc_beam_center_x
        header["y_beam"] = calc_beam_center_y

    # No beam settings
    else:

        # Beam center is already in mm
        # parameters["x_beam"] = parameters["beam_y"] * parameters["pixel_size"]
        # parameters["y_beam"] = parameters["beam_x"] * parameters["pixel_size"]

        header["x_beam"] = header["beam_center_y"]
        header["y_beam"] = header["beam_center_x"]

    # Beam center in pixels
    header["beam_x"] = header["beam_center_x"] / header["pixel_size"]
    header["beam_y"] = header["beam_center_y"] / header["pixel_size"]

    # Set the header version value - future flexibility
    header["header_version"] = HEADER_VERSION

    # Add tag for module to header
    header["rapd_detector_id"] = "als821_adsc_q315"

    # The image template for processing
    header["image_template"] = IMAGE_TEMPLATE % (header["image_prefix"], header["run_number"])
    header["run_number_in_template"] = RUN_NUMBER_IN_TEMPLATE

    # Return the header
    return header

# Derive data root dir from image name
def get_data_root_dir(fullname):
    """
    Derive the data root directory from the user directory

    The logic will most likely be unique for each site
    """

    # Isolate distinct properties of the images path
    path_split = fullname.split(os.path.sep)
    data_root_dir = False

    # gpfs = False
    # users = False
    inst = False
    group = False
    # images = False

    # Break down NE-CAT standard directories
    # ex. /gpfs1/users/cornell/Ealick_E_1200/images/bob/snaps/0_0/foo_0_0001.cbf
    if path_split[1].startswith("gpfs"):
        # gpfs = path_split[1]
        if path_split[2] == "users":
            # users = path_split[2]
            if path_split[3]:
                inst = path_split[3]
                if path_split[4]:
                    group = path_split[4]

    if group:
        data_root_dir = os.path.join("/", *path_split[1:5])
    elif inst:
        data_root_dir = os.path.join("/", *path_split[1:4])
    else:
        data_root_dir = False

    # Return the determined directory
    return data_root_dir

if __name__ == "__main__":

    # Test the header reading
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
    else:
        sys.exit()

    header = read_header(test_image)

    pprint(header)


    # result = parse_file_name("/gpfs1/users/cornell_murphy_1001/images/frank/runs/test/0_0/test_1_001.img")
