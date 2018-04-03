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
import os
from pprint import pprint
import re
import time
import numpy

# RAPD imports
# commandline_utils
# detectors.detector_utils as detector_utils
# utils

# Dectris Pilatus 6M
import detectors
import detectors.dectris.dectris_eiger16m as detector
import detectors.detector_utils as utils

# Detector information
# The RAPD detector type
DETECTOR = "dectris_eiger16m"
# The detector vendor as it appears in the header
VENDORTYPE = "Eiger-16M"
# The detector serial number as it appears in the header
DETECTOR_SN = "Dectris Eiger 16M S/N E-32-0115"
# The detector suffix "" if there is no suffix
DETECTOR_SUFFIX = ".cbf"
# Template for image name generation ? for frame number places
IMAGE_TEMPLATE = "%s_??????.cbf" # prefix
# Is there a run number in the template?
RUN_NUMBER_IN_TEMPLATE = False
SNAP_IN_TEMPLATE = True
# This is a version number for internal RAPD use
# If the header changes, increment this number
HEADER_VERSION = 1

# XDS information for constructing the XDS.INP file
# Import from more generic detector
XDS_FLIP_BEAM = detector.XDS_FLIP_BEAM

# Get the reference input
XDSINP0 = detector.XDSINP
# Update the XDS information from the imported detector
# only if there are differnces or new keywords.
# The tuple should contain two items (key and value)
# ie. XDSINP1 = [("SEPMIN", "4"),]
XDSINP1 = [('MINIMUM_NUMBER_OF_PIXELS_IN_A_SPOT', '4') ,
    ('NUMBER_OF_PROFILE_GRID_POINTS_ALONG_ALPHA/BETA', '13') ,
    ('NUMBER_OF_PROFILE_GRID_POINTS_ALONG_GAMMA', '9') ,
    ('OVERLOAD', '3000000') ,
    ('REFINE(CORRECT)', 'POSITION DISTANCE BEAM ORIENTATION CELL AXIS') ,
    ('REFINE(INTEGRATE)', 'POSITION DISTANCE BEAM ORIENTATION CELL') ,
    ('TRUSTED_REGION', '0.00 1.2') ,
    ('VALUE_RANGE_FOR_TRUSTED_DETECTOR_PIXELS', '8000. 30000.') ,
    ('UNTRUSTED_RECTANGLE11', '    0 4151    225  260'),
    ('UNTRUSTED_RECTANGLE12', '    0 4151    806  811'),
    ('UNTRUSTED_RECTANGLE13', '    0 4151   1357 1362'),
    ('UNTRUSTED_RECTANGLE14', '    0 4151   1908 1913'),
    ('UNTRUSTED_RECTANGLE15', '    0 4151   2459 2464'),
    ('UNTRUSTED_RECTANGLE16', '    0 4151   3010 3015'),
    ('UNTRUSTED_RECTANGLE17', '    0 4151   3561 3566'),
    ('UNTRUSTED_RECTANGLE18', '    0 4151   4112 4117'),
    ]

XDSINP = utils.merge_xds_input(XDSINP0, XDSINP1)


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
    prefix = "_".join(sbase[0:-1])
    image_number = int(sbase[-1])
    run_number = None

    return directory, basename, prefix, run_number, image_number

def is_snap(fullname):
    """Returns if image is a snap based on the filename"""
    result = re.search("_s\_\d{6}$", fullname)
    if result:
        return True
    else:
        return False

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
    if run_number !=None:
        filename = "%s_%s_%06d.cbf" % (image_prefix,
                                       run_number,
                                       image_number)
    else:
        filename = "%s_%06d.cbf" % (image_prefix,
                                    image_number)

    fullname = os.path.join(directory, filename)

    return fullname

def create_image_template(image_prefix, run_number):
    """
    Create an image template for XDS
    """

    image_template = IMAGE_TEMPLATE % (image_prefix)

    return image_template

def calculate_flux(header, site_params):
    """
    Calculate the flux as a function of transmission and aperture size.
    """
    beam_size_x = site_params.get('BEAM_SIZE_X')
    beam_size_y = site_params.get('BEAM_SIZE_Y')
    aperture = header.get('md2_aperture', 0.05)
    if aperture == None:
        aperture = 0.05
    new_x = beam_size_x
    new_y = beam_size_y

    if aperture < beam_size_x:
        new_x = aperture
    if aperture < beam_size_y:
        new_y = aperture

    # Calculate area of full beam used to calculate the beamline flux
    # Assume ellipse, but same equation works for circle.
    # Assume beam is uniform
    full_beam_area = numpy.pi*(beam_size_x/2)*(beam_size_y/2)

    # Calculate the new beam area (with aperture) divided by the full_beam_area.
    # Since aperture is round, it will be cutting off edges of x length until it matches beam height,
    # then it would switch to circle
    if beam_size_y <= aperture:
        # ellipse
        ratio = (numpy.pi*(aperture/2)*(beam_size_y/2)) / full_beam_area
    else:
        # circle
        ratio = (numpy.pi*(aperture/2)**2) / full_beam_area

    # Calculate the new_beam_area ratio to full_beam_area
    flux = int(round(site_params.get('BEAM_FLUX') * (header.get('transmission')/100) * ratio))

    # Return the flux and beam size
    return (flux, new_x, new_y)

# Calculate the flux of the beam
def calculate_flux_OLD(header, beam_settings={}):
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

def get_alt_path(image):
    """Pass back the alternate path of image located in long term storage."""
    prefix = ['/epu2/rdma', '/epu/rdma']
    dirname, imagename = os.path.split(image)
    for i in range(len(prefix)):
        if image.startswith(prefix[i]):
            newdir = dirname.replace(prefix[i],'')[:dirname.rfind('/')]
            break
    newpath = os.path.join(newdir[:newdir.rfind('/')], imagename)
    return newpath

def get_alt_path_WORKING(image):
    """Pass back the alternate path of image located in long term storage."""
    dirname, imagename = os.path.split(image)
    newdir = dirname.replace('/epu/rdma','')[:dirname.rfind('/')]
    newpath = os.path.join(newdir[:newdir.rfind('/')], imagename)
    return newpath

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
    #tease out the info from the file name
    base = os.path.basename(image).rstrip(".cbf")

    def mmorm(x):
        d = float(x)
        if (d < 2):
            return (d*1000)
        else:
            return d

    #item:(pattern,transform)
    header_items = {
        "md2_aperture": ("^# MD2_aperture_size\s*(\d+) microns", lambda x: int(x)/1000),
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
        "wavelength": ("^# Wavelength\s*([\d\.]+) A", lambda x: float(x)),
        "ring_current": ("^# Ring_current\s*([\d\.]*)\s*mA", lambda x: float(x)),
        "sample_mounter_position": ("^#\sSample_mounter_position\s*([\w\.]+)", lambda x:str(x).rstrip()),
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

    return parameters

    # except:
    #     if logger:
    #         logger.exception('Error reading the header for image %s' % image)

def read_header(input_file=False, beam_settings=False, extra_header=False):
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

    # Add some values HACK
    #header["aperture_x"] = 0.05
    #header["aperture_y"] = 0.05

    # Calculate flux, new beam size and add them to header
    if beam_settings:
        flux, x_size, y_size = calculate_flux(header, beam_settings)
        header['flux'] = flux
        header['x_beam_size'] = x_size
        header['y_beam_size'] = y_size

    basename = os.path.basename(input_file)
    header["image_prefix"] = "_".join(basename.replace(".cbf", "").split("_")[:-1])
    header["run_number"] = None
    #header["image_prefix"] = "_".join(basename.replace(".cbf", "").split("_")[:-2])
    #header["run_number"] = int(basename.replace(".cbf", "").split("_")[-2])
    

    # Add tag for module to header
    header["rapd_detector_id"] = "sercat_dectris_eiger16m"

    # The image template for processing
    header["image_template"] = IMAGE_TEMPLATE % header["image_prefix"]
    header["run_number_in_template"] = RUN_NUMBER_IN_TEMPLATE
    header['data_root_dir'] = get_data_root_dir(input_file)

    # Add source parameters
    header["gauss_x"] = beam_settings.get("BEAM_GAUSS_X", 0.05)
    header["gauss_y"] = beam_settings.get("BEAM_GAUSS_Y", 0.05)

    # Get the data_root_dir
    header["data_root_dir"] = get_data_root_dir(fullname)

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
    #commandline_args = get_commandline()

    # Execute code
    #main(args=commandline_args)
    #get_alt_path('/epu/rdma/gpfs2/users/wvu/robart_E_2985/images/robart/runs/F_2/F_2_1_000001/F_2_1_000287.cbf')

    # header = base_read_header('/gpfs2/users/mskcc/patel_E_2891/images/juncheng/snaps/chengwI5_PAIR_0_000005.cbf')
    # site_params = {'BEAM_APERTURE_SHAPE': 'circle',
    #                  'BEAM_CENTER_DATE': '2017-3-02',
    #                  'BEAM_CENTER_X': (163.2757684023,
    #                                    0.0003178917,
    #                                    -5.0236657815e-06,
    #                                    5.8164218288e-09),
    #                  'BEAM_CENTER_Y': (155.1904879862,
    #                                    -0.0014631216,
    #                                    8.60559283424e-07,
    #                                    -2.5709929645e-10),
    #                  'BEAM_FLUX': 1500000000000.0,
    #                  'BEAM_GAUSS_X': 0.03,
    #                  'BEAM_GAUSS_Y': 0.01,
    #                  'BEAM_SHAPE': 'ellipse',
    #                  'BEAM_SIZE_X': 0.05,
    #                  'BEAM_SIZE_Y': 0.02,
    #                  'DELTA_OMEGA_MIN': 0.05,
    #                  'DETECTOR_DIST_MAX': 1000.0,
    #                  'DETECTOR_DIST_MIN': 150.0,
    #                  'EXPOSURE_TIME_MIN': 0.05}
    # calculate_flux(header, site_params)
    pass