"""
Methods for reading and understanding the images from SERCAT Rayonix MX300
detector
"""

__license__ = """
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

__created__ = "2016-02-26"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
import grp
import math
import os
from pprint import pprint
import pwd

# RAPD imports
import detectors.rayonix.rayonix_mx225 as detector
import detectors.detector_utils as utils

# Detector information
DETECTOR = "rayonix_mx225"
VENDORTYPE = "MARCCD"
DETECTOR_SN = 7
DETECTOR_SUFFIX = ""
IMAGE_TEMPLATE = "%s.????"
RUN_NUMBER_IN_TEMPLATE = False
HEADER_VERSION = 1

# XDS information
XDS_FLIP_BEAM = True
# Import from more generic detector
XDSINP0 = detector.XDSINP
# Update the XDS information from the imported detector
# only if there are differnces or new keywords.
# The tuple should contain two items (key and value)
# ie. XDSINP1 = [("SEPMIN", "4"),]
XDSINP1 = [
    ('ROTATION_AXIS', '-1 0 0') ,
          ]
XDSINP = utils.merge_xds_input(XDSINP0, XDSINP1)


def parse_file_name(fullname):
    """
    Parse the fullname of an image and return
    (directory, basename, prefix, run_number, image_number)

    Keyword arguments
    fullname -- the full path name of the image file
    """
    # print fullname
    directory = os.path.dirname(fullname)
    # print directory
    basename = os.path.basename(fullname).rstrip(DETECTOR_SUFFIX)
    # print basename
    sbase = basename.split(".")
    # print sbase
    prefix = ".".join(sbase[0:-1])
    # print prefix
    image_number = int(sbase[-1])
    # print image_number
    run_number = None

    return directory, basename, prefix, run_number, image_number

# Derive data root dir from image name
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

def get_group_and_session(data_root_dir):
    """
    Return the group and session for the directory input. This should be the RAPD system user and
    group

    Keyword arguments
    data_root_dir -- root directory of the images being collected
    """

    # Get the session name
    # /raw/ID_16_04_22_NIH_dxia_2 >> ID_16_04_22_NIH_dxia_2
    try:
        rapd_session_name = data_root_dir.split(os.path.sep)[2]
    except IndexError:
        rapd_session_name = None

    # Get the RAPD group
    # /raw/ID_16_04_22_NIH_dxia_2 >>
    stat_info = os.stat(data_root_dir)
    user = pwd.getpwuid(stat_info.st_uid)[0]
    group = grp.getgrgid(stat_info.st_gid)[0]
    # Filter group for "wheel"
    if group == "wheel":
        group = "staff"
    rapd_group = "_".join((group, user))

    return rapd_group, rapd_session_name

def create_image_template(image_prefix, run_number):
    """
    Create an image template for XDS
    """

    image_template = IMAGE_TEMPLATE % image_prefix

    return image_template

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

    if not run_number in (None, "unknown"):
        filename = "%s.%s.%04d" % (image_prefix,
                                   run_number,
                                   image_number)
    else:
        filename = "%s.%04d" % (image_prefix,
                                   image_number)

    fullname = os.path.join(directory, filename)

    return fullname

# Calculate the flux of the beam
def calculate_flux(header, beam_settings={}):
    """
    Return the flux and size of the beam given parameters

    Keyword arguments
    header -- data from the header of the image file
    beam_settings -- incident beam information from the site definitions module
    """

    # Save some typing
    beam_size_raw_x = beam_settings.get("BEAM_SIZE_X", 100)
    beam_size_raw_y = beam_settings.get("BEAM_SIZE_Y", 100)
    aperture_x = header["aperture_x"]
    aperture_y = header["aperture_y"]
    raw_flux = beam_settings.get("BEAM_FLUX", 1000000) * header["transmission"] / 100.0

    # Calculate the size of the beam incident on the sample in mm
    beam_size_x = min(beam_size_raw_x, aperture_x)
    beam_size_y = min(beam_size_raw_y, aperture_y)

    # Calculate the raw beam area
    if beam_settings.get("BEAM_SHAPE", "ellipse") == "ellipse":
        raw_beam_area = math.pi * beam_size_raw_x * beam_size_raw_y / 4
    elif beam_settings.get("BEAM_SHAPE", "ellipse") == "rectangle":
        raw_beam_area = beam_size_raw_x * beam_size_raw_y

    # Calculate the incident beam area
    # Aperture is smaller than the beam in x & y
    if beam_size_x <= beam_size_raw_x and beam_size_y <= beam_size_raw_y:
        if beam_settings.get("BEAM_APERTURE_SHAPE", "circle") == "circle":
            beam_area = math.pi * (beam_size_x / 2)**2
        elif beam_settings.get("BEAM_APERTURE_SHAPE", "circle") == "rectangle":
            beam_area = beam_size_x * beam_size_y

    # Getting the raw beam coming through
    elif beam_size_x > beam_size_raw_x and beam_size_y > beam_size_raw_y:
        if beam_settings.get("BEAM_SHAPE", "ellipse") == "ellipse":
            beam_area = math.pi * (beam_size_x / 2) * (beam_size_y / 2)
        elif beam_settings.get("BEAM_SHAPE", "ellipse") == "rectangle":
            beam_area = beam_size_x * beam_size_y

    # Aperture is not smaller than beam in both directions
    else:
        if beam_settings.get("BEAM_APERTURE_SHAPE", "circle") == "circle":
            # Use an ellipse as an imperfect description of this case
            beam_area = math.pi * (beam_size_x / 2) * (beam_size_y / 2)
        if beam_settings.get("BEAM_APERTURE_SHAPE", "circle") == "rectangle":
            # Use a rectangle description of this case
            beam_area = beam_size_x * beam_size_y

    # Calculate the flux
    flux = raw_flux * (beam_area / raw_beam_area)

    return flux, beam_size_x/1000.0, beam_size_y/1000.0

def calculate_beam_center(distance, beam_settings, v_offset=0):
    """
    Return a beam center, given a distance and vertical offset

    Keyword arguments
    distance -- sample to detector distance in mm
    beam_settings -- incident beam information from the site definitions module
    v_offset -- the vertical offset of the detector
    """

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
def read_header(fullname, beam_settings={}, extra_header=False):
    """
    Read the header and add some site-specific data

    Keyword variables
    fullname -- full path name of the image file to be read
    beam_settings -- source information from site file
    """

    # Perform the header read form the file
    header = detector.read_header(fullname)

    # pprint(header)

    # Label with detector
    header["detector"] = DETECTOR

    # Set the header version value - future flexibility
    header["header_version"] = HEADER_VERSION

    # Add tag for module to header
    header["rapd_detector_id"] = "sercat_rayonix_mx225"

    # The image template for processing
    header["image_template"] = IMAGE_TEMPLATE % header["image_prefix"]
    header["run_number_in_template"] = RUN_NUMBER_IN_TEMPLATE

    # Add some values HACK
    header["aperture_x"] = 50
    header["aperture_y"] = 50
    header["transmission"] = 50

    # Correct error wavelength >> energy
    header["energy"] = header["wavelength"]
    # del header["wavelength"]

    # Translate from mar to RAPD
    header["osc_axis"] = header["axis"]
    header["omega"] = header["omega_start"]

    # Binning
    # if header["size1"] == 4096:
    #     header["binning"] = False
    # else:
    #     header["binning"] = True

    # Missing values
    header["kappa"] = None
    header["phi"] = None
    header["robot_position"] = None
    header["run_number"] = None
    header["sample_id"] = None
    header["sample_pos_x"] = None
    header["sample_pos_y"] = None
    header["sample_pos_z"] = None
    header["source_current"] = None
    header["source_mode"] = None

    # Perform flux calculation
    flux, beam_size_x, beam_size_y = calculate_flux(header, beam_settings)
    header["flux"] = flux
    header["beam_size_x"] = beam_size_x
    header["beam_size_y"] = beam_size_y

    # Add source parameters
    header["gauss_x"] = beam_settings.get("BEAM_GAUSS_X", 0.05)
    header["gauss_y"] = beam_settings.get("BEAM_GAUSS_Y", 0.05)

    # Calculate beam center - cannot be done with just header information!
    if beam_settings:
        calc_beam_center_x, calc_beam_center_y = calculate_beam_center(
            distance=header["distance"],
            beam_settings=beam_settings,
            v_offset=0)
        header["beam_center_calc_x"] = calc_beam_center_x
        header["beam_center_calc_y"] = calc_beam_center_y
        header["x_beam"] = calc_beam_center_x
        header["y_beam"] = calc_beam_center_y
    else:
        header["x_beam"] = header["beam_center_x"]
        header["y_beam"] = header["beam_center_y"]


    # Get the data_root_dir
    header["data_root_dir"] = get_data_root_dir(fullname)

    # Group and session are interpreted from the image name
    # rapd_session_name, rapd_group = get_group_and_session(header["data_root_dir"])
    # header["rapd_session_name"] = rapd_session_name
    # header["rapd_group"] = rapd_group

    # Return the header
    return header

def get_commandline():
    """
    Grabs the commandline
    """

    # Parse the commandline arguments
    commandline_description = "Read header from Rayonix MX225"
    parser = argparse.ArgumentParser(description=commandline_description)

    # File name to be generated
    parser.add_argument(action="store",
                        dest="file",
                        nargs="?",
                        default=False,
                        help="Name of file to be read")

    return parser.parse_args()

def main(args):
    """
    Read header for test image and print out retrieved data
    """

    if args.file:
        test_image = os.path.abspath(args.file)
    else:
        raise Exception("No test image input!")

    # Read the header
    header = read_header(test_image)

    # And print it out
    pprint(header)

if __name__ == "__main__":

    # Get the commandline args
    commandline_args = get_commandline()

    # Execute code
    main(args=commandline_args)
