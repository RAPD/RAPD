"""
This file is part of RAPD

Copyright (C) 2016, Cornell University
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

import math
import os

import adsc_q315

# Standard monitor
class Monitor(adsc_q315.Monitor):
    """The standard monitor from redis"""

# Calculate the flux of the beam
def calculate_flux(header, beam_settings):
    """Return the flux and size of the beam given parameters"""

    # Save some typing
    beam_size_raw_x = beam_settings["BEAM_SIZE_X"]
    beam_size_raw_y = beam_settings["BEAM_SIZE_Y"]
    aperture_size = header["md2_aperture"]
    raw_flux = beam_settings["BEAM_FLUX"] * header["transmission"] / 100.0

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

def calculate_beam_center(distance, beam_settings, v_offset=0):
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
def read_header(fullname, beam_settings, run_id=None, place_in_run=None):
    """Read the NE-CAT ADSC Q315 header and add some site-specific data"""

    # Perform the header read form the file
    header = adsc_q315.read_header(fullname, run_id, place_in_run)

    # Perform flux calculation
    flux, beam_size_x, beam_size_y = calculate_flux(header, beam_settings)
    header["flux"] = flux
    header["beam_size_x"] = beam_size_x
    header["beam_size_y"] = beam_size_y

    # Calculate beam center
    calc_beam_center_x, calc_beam_center_y = calculate_beam_center(
        distance=header["distance"],
        beam_settings=beam_settings,
        v_offset=header["vertical_offset"])
    header["x_beam"] = calc_beam_center_x
    header["y_beam"] = calc_beam_center_y

    # Return the header
    return header

# Derive data root dir from image name
def get_data_root_dir(fullname):
    """
    Derive the data root directory from the user directory

    The logic will most likely be unique for each beamline
    """

    # Isolate distinct properties of the images path
    path_split = fullname.split(os.path.sep)
    data_root_dir = False

    gpfs = False
    users = False
    inst = False
    group = False
    images = False

    # Break down NE-CAT standard directories
    # ex. /gpfs1/users/cornell/Ealick_E_1200/images/bob/snaps/0_0/foo_0_0001.cbf
    if path_split[1].startswith("gpfs"):
        gpfs = path_split[1]
        if path_split[2] == "users":
            users = path_split[2]
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
