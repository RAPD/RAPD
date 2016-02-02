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

import os

import adsc_q315

# Standard monitor
class Monitor(adsc_q315.Monitor):
    """The standard monitor from redis"""

# Calculate the flux of the beam
def calculate_flux():
    """Return the flux of the beam given parameters"""

    return 0

def calculate_beam_center(self, distance, v_offset=0):
    """ Return a beam center, given a distance and vertical offset"""

    x_beam = distance**6 * self.Settings["beam_center_x_m6"] + \
             distance**5 * self.Settings["beam_center_x_m5"] + \
             distance**4 * self.Settings["beam_center_x_m4"] + \
             distance**3 * self.Settings["beam_center_x_m3"] + \
             distance**2 * self.Settings["beam_center_x_m2"] + \
             distance * self.Settings["beam_center_x_m1"] + \
             self.Settings["beam_center_x_b"] + \
             v_offset

    y_beam = distance**6 * self.Settings["beam_center_y_m6"] + \
             distance**5 * self.Settings["beam_center_y_m5"] + \
             distance**4 * self.Settings["beam_center_y_m4"] + \
             distance**3 * self.Settings["beam_center_y_m3"] + \
             distance**2 * self.Settings["beam_center_y_m2"] + \
             distance * self.Settings["beam_center_y_m1"] + \
             self.Settings["beam_center_y_b"]

    return x_beam, y_beam

# Standard header reading
def read_header(image, run_id=None, place_in_run=None):
    """Read the NE-CAT ADSC Q315 header and add some site-specific data"""

    # Perform the header read form the file
    header = adsc_q315.read_header(image, run_id, place_in_run)

    # Perform flux calculation

    # Calculate beam center

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
