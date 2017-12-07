"""
This file is part of RAPD

Copyright (C) 2016-2017 Cornell University
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

__created__ = "2016-02-01"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import math
import os
import sys

# RAPD imports
import detectors.adsc.adsc_q315 as detector
from detectors.detector_utils import merge_xds_input

# Detector information
DETECTOR = "adsc_q315"
VENDORTYPE = "ADSC"
DETECTOR_SN = (911, 916)
DETECTOR_SUFFIX = ".img"
IMAGE_TEMPLATE = "%s_%d_???.img"
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
XDSINP = merge_xds_input(XDSINP0, XDSINP1)


# Source information
# Flux of the beam
BEAM_FLUX = 8E11
# Size of the beam in microns
BEAM_SIZE_X = 50
BEAM_SIZE_Y = 20
# Shape of the beam - ellipse, rectangle
BEAM_SHAPE = "ellipse"
# Shape of the attenuated beam - circle or rectangle
BEAM_APERTURE_SHAPE = "circle"
# Gaussian description of the beam for raddose
BEAM_GAUSS_X = 0.03
BEAM_GAUSS_Y = 0.01
# Beam center calibration
BEAM_CENTER_DATE = "2015-12-07"
# Beamcenter equation coefficients (b, m1, m2, m3, m4, m5, m6)
BEAM_CENTER_X = (153.94944895756946,
                 -0.016434436106566495,
                 3.5990848937868658e-05,
                 -8.2987834172005917e-08,
                 1.0732920112697317e-10,
                 -7.339858946384788e-14,
                 2.066312749407257e-17)
BEAM_CENTER_Y = (158.56546190593907,
                 0.0057578279496966192,
                 -3.9726067083100419e-05,
                 1.1458201832002297e-07,
                 -1.7875879553926729e-10,
                 1.4579198435694557e-13,
                 -4.7910792416525411e-17)
# Aggregator - be extra careful when modifying
BEAM_SETTINGS = {"BEAM_FLUX":BEAM_FLUX,
                 "BEAM_SIZE_X":BEAM_SIZE_X,
                 "BEAM_SIZE_Y":BEAM_SIZE_Y,
                 "BEAM_SHAPE":BEAM_SHAPE,
                 "BEAM_APERTURE_SHAPE":BEAM_APERTURE_SHAPE,
                 "BEAM_GAUSS_X":BEAM_GAUSS_X,
                 "BEAM_GAUSS_Y":BEAM_GAUSS_Y,
                 "BEAM_CENTER_DATE":BEAM_CENTER_DATE,
                 "BEAM_CENTER_X":BEAM_CENTER_X,
                 "BEAM_CENTER_Y":BEAM_CENTER_Y}

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
def calculate_flux(input_header, beam_settings=BEAM_SETTINGS):
    """Return the flux and size of the beam given parameters"""

    # Save some typing
    beam_size_raw_x = beam_settings["BEAM_SIZE_X"]
    beam_size_raw_y = beam_settings["BEAM_SIZE_Y"]
    aperture_size = input_header["aperture_x"]
    raw_flux = beam_settings["BEAM_FLUX"] * input_header["transmission"] / 100.0

    # Calculate the size of the beam incident on the sample in mm
    if aperture_size != None:
        beam_size_x = min(beam_size_raw_x, aperture_size)
        beam_size_y = min(beam_size_raw_y, aperture_size)
    else:
        beam_size_x = beam_size_raw_x
        beam_size_y = beam_size_raw_y

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

def calculate_beam_center(distance, beam_settings=BEAM_SETTINGS, v_offset=0):
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

# Standard header reading
def read_header(fullname, beam_settings=BEAM_SETTINGS, run_id=None, place_in_run=None):
    """Read the NE-CAT ADSC Q315 header and add some site-specific data"""

    # Perform the header read form the file
    header = detector.read_header(fullname, run_id, place_in_run)

    # Massage header values
    header["aperture_x"] = header["aperture"]
    header["aperture_y"] = header["aperture_x"]
    del header["aperture"]

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

    # Set the header version value - future flexibility
    header["header_version"] = HEADER_VERSION

    # Add tag for module to header
    header["rapd_detector_id"] = "necat_adsc_q315"

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
        test_image = "/Users/frankmurphy/workspace/rapd_github/src/test/necat_e_test/test_data/thaum10_PAIR_0_001.img"

    # Flux of the beam
    BEAM_FLUX = 8E11
    # Size of the beam in microns
    BEAM_SIZE_X = 50
    BEAM_SIZE_Y = 20
    # Shape of the beam - ellipse, rectangle
    BEAM_SHAPE = "ellipse"
    # Shape of the attenuated beam - circle or rectangle
    BEAM_APERTURE_SHAPE = "circle"
    # Gaussian description of the beam for raddose
    BEAM_GAUSS_X = 0.03
    BEAM_GAUSS_Y = 0.01
    # Beam center calibration
    BEAM_CENTER_DATE = "2015-12-07"
    # Beamcenter equation coefficients (b, m1, m2, m3, m4, m5, m6)
    BEAM_CENTER_X = (153.94944895756946,
                     -0.016434436106566495,
                     3.5990848937868658e-05,
                     -8.2987834172005917e-08,
                     1.0732920112697317e-10,
                     -7.339858946384788e-14,
                     2.066312749407257e-17)
    BEAM_CENTER_Y = (158.56546190593907,
                     0.0057578279496966192,
                     -3.9726067083100419e-05,
                     1.1458201832002297e-07,
                     -1.7875879553926729e-10,
                     1.4579198435694557e-13,
                     -4.7910792416525411e-17)
    BEAM_SETTINGS = {"BEAM_FLUX":BEAM_FLUX,
                     "BEAM_SIZE_X":BEAM_SIZE_X,
                     "BEAM_SIZE_Y":BEAM_SIZE_Y,
                     "BEAM_SHAPE":BEAM_SHAPE,
                     "BEAM_APERTURE_SHAPE":BEAM_APERTURE_SHAPE,
                     "BEAM_GAUSS_X":BEAM_GAUSS_X,
                     "BEAM_GAUSS_Y":BEAM_GAUSS_Y,
                     "BEAM_CENTER_DATE":BEAM_CENTER_DATE,
                     "BEAM_CENTER_X":BEAM_CENTER_X,
                     "BEAM_CENTER_Y":BEAM_CENTER_Y}

    header = read_header(test_image, BEAM_SETTINGS)

    import pprint
    pp = pprint.PrettyPrinter()
    pp.pprint(header)


    # result = parse_file_name("/gpfs1/users/cornell_murphy_1001/images/frank/runs/test/0_0/test_1_001.img")
