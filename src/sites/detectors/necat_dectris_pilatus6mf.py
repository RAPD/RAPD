"""Detector description for NE-CAT Pilatus 6M"""

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

__created__ = "2017-02-06"
_maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
import os
import pprint
import numpy
import re

# Dectris Pilatus 6M
import detectors.dectris.dectris_pilatus6m as detector
import detectors.detector_utils as utils

# Detector information
# The RAPD detector type
DETECTOR = "dectris_pilatus6m"
# The detector vendor as it appears in the header
VENDORTYPE = "DECTRIS"
# The detector serial number as it appears in the header
DETECTOR_SN = "60-0112-F"
# The detector suffix "" if there is no suffix
DETECTOR_SUFFIX = ".cbf"
# Template for image name generation ? for frame number places
IMAGE_TEMPLATE = "%s_%s_????.cbf" # prefix & run number
# Is there a run number in the template?
RUN_NUMBER_IN_TEMPLATE = True
# This is a version number for internal RAPD use
# If the header changes, increment this number
HEADER_VERSION = 1

# XDS information for constructing the XDS.INP file
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

# Testing information
TEST_DATA_DIR = "APS/NECAT/24-ID-C"
TEST_INDEX_COMMANDS = [
    "rapd.index --json images/run_1_0001.cbf",
    "rapd.index --json images/run_1_0001.cbf  images/run_1_0091.cbf"
    ]
TEST_INTEGRATE_COMMAND = "rapd.integrate --json images/run_1_####.cbf"

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

    filename = IMAGE_TEMPLATE.replace("????", "%04d") % (image_prefix, run_number, image_number)

    fullname = os.path.join(directory, filename)

    return fullname

def create_image_template(image_prefix, run_number):
    """
    Create an image template for XDS
    """

    image_template = IMAGE_TEMPLATE % (image_prefix, run_number)

    return image_template

def is_run_from_imagename():
    """
    Determine if image is in a run from the image
    """
    
    # Tease out the info from the file name
    directory, basename, image_prefix, run_number, image_number = detector.parse_file_name(fullname)

    # Run number 0 for snaps at NECAT
    if run_number > 0:
        return True
    else:
        return False
    

def calculate_flux(header, site_params):
    """
    Calculate the flux as a function of transmission and aperture size.
    """
    print header
    print site_params
    beam_size_x = site_params.get('BEAM_SIZE_X')
    beam_size_y = site_params.get('BEAM_SIZE_Y')
    aperture = header.get('md2_aperture')
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

def get_data_root_dir_OLD(fullname):
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

def get_data_root_dir(fullname):
    """
    Derive the data root directory from the user directory
    The logic will most likely be unique for each site

    Keyword arguments
    fullname -- the full path name of the image file
    """

    path_split    = fullname.split(os.path.sep)
    data_root_dir = False

    gpfs   = False
    users  = False
    inst   = False
    group  = False
    images = False

    for p in path_split:
        if p.startswith('gpfs'):
            st = path_split.index(p)
            break
        else:
            st = 0
    if path_split[st].startswith("gpfs"):
        gpfs = path_split[st]
        if path_split[st+1] == "users":
            users = path_split[st+1]
            if path_split[st+2]:
                inst = path_split[st+2]
                if path_split[st+3]:
                    group = path_split[st+3]

    if group:
        data_root_dir = os.path.join("/",*path_split[1:st+4])
    elif inst:
        data_root_dir = os.path.join("/",*path_split[1:st+3])
    else:
        data_root_dir = False

    # return the determined directory
    return data_root_dir

def base_read_header_OLD(image,
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
        #"md2_aperture": ("^# MD2_aperture_size\s*(\d+) microns", lambda x: int(x)/1000),
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
        #"ring_current": ("^# Ring_current\s*([\d\.]*)\s*mA", lambda x: float(x)),
        #"sample_mounter_position": ("^#\sSample_mounter_position\s*([\w\.]+)", lambda x:str(x).rstrip()),
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
        "detector": "PILATUS",
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

    #pprint(parameters)

    # Put beam center into RAPD format mm
    parameters["x_beam"] = parameters["beam_y"] * parameters["pixel_size"]
    parameters["y_beam"] = parameters["beam_x"] * parameters["pixel_size"]

    return parameters

def read_header(fullname, beam_settings=False, extra_header=False):
    """
    Read header from image file and return dict

    Keyword variables
    fullname -- full path name of the image file to be read
    beam_settings -- source information from site file
    """

    # Perform the header read from the file
    # If you are importing another detector, this should work
    header = detector.read_header(fullname)
    #header = base_read_header(fullname)

    # Get additional beamline info not in header
    if extra_header:
        header.update(extra_header)

    # Calculate flux, new beam size and add them to header
    if beam_settings:
        flux, x_size, y_size = calculate_flux(header, beam_settings)
        header['flux'] = flux
        header['x_beam_size'] = x_size
        header['y_beam_size'] = y_size

    basename = os.path.basename(fullname)
    header["image_prefix"] = "_".join(basename.replace(".cbf", "").split("_")[:-2])
    header["run_number"] = int(basename.replace(".cbf", "").split("_")[-2])

    # Add tag for module to header
    header["rapd_detector_id"] = "necat_dectris_pilatus6mf"

    # The image template for processing
    header["image_template"] = IMAGE_TEMPLATE % (header["image_prefix"], header["run_number"])
    header["run_number_in_template"] = RUN_NUMBER_IN_TEMPLATE
    header['data_root_dir'] = get_data_root_dir(fullname)

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

    # File exists
    if os.path.exists(test_image):
        # Read the header
        header = read_header(test_image)

        # And print it out
        pprint.pprint(header)

    # No file
    else:
        print get_data_root_dir(test_image)

if __name__ == "__main__":

    # Get the commandline args
    commandline_args = get_commandline()

    # Execute code
    main(args=commandline_args)
