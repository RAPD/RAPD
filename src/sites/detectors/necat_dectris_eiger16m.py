"""
Detector description for LS-CAT Eiger 9M
Designed to read the CBF version of the Eiger file
"""
#from detectors.adsc.adsc import header

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
import redis
import threading

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

class FileLocation():
    """Check if images are in RAMDISK or NMVe drive space."""
    def __init__(self, logger=False, verbose=False):
        #threading.Thread.__init__ (self)
        #self.logger = logger
        #self.ip = '164.54.212.218'
        #self.ram_prefix = '/epu/rdma'
        self.ip = '164.54.212.219'
        self.ram_prefix = '/epu2/rdma'
        self.nvme_prefix = '/epu/nvme'
        self.ft_redis = self.redis_ft_connect()

    def redis_ft_connect(self):
        """Connect to the Eiger file_tracker.py redis server."""
        # Used for quick calls to beamline redis
        return(redis.Redis(host=self.ip,
                           port=6379,
                           db=0))

    def get_alt_path(self, img_path):
        """
        Check if image in RAMDISK and pass back new path,
        Otherwise pass back img_path
        """
        file_name = os.path.basename(img_path)
        dir = self.get_redis_key(img_path)
        # Check if key in Redis DB. Should get False, 'ram', or 'nvme'.
        loc = self.ft_redis.get(dir)
        if loc == 'ram':
            # Tell file_tracker to not remove dataset!
            #self.hold_data(dir)
            # Pass back location in RAMDISK
            return os.path.join('%s%s'%(self.ram_prefix,dir), file_name)
        elif loc == 'nvme':
            # Tell file_tracker to not remove dataset!
            #self.hold_data(dir)
            # Pass back location on NMVe drive
            return os.path.join('%s%s'%(self.nvme_prefix,dir), file_name)
        else:
            # None key, use GPFS location
            return img_path

    def get_redis_key(self, img_path):
        """Return the redis key for the dataset"""
        # In our case the key is the image path minus suffix.
        return img_path[:img_path.rfind('.')]

    def hold_data(self, dir):
        """Make sure dataset is not deleted during processing."""
        self.ft_redis.sadd('working', dir)
        print 'holding: %s' %self.ft_redis.smembers('working')

    def release_data(self, img_path):
        """Allow dataset in RAMDISK to be deleted."""
        self.ft_redis.srem('working', self.get_redis_key(img_path))
        print 'release: %s' %self.ft_redis.smembers('working')

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

    # print "create_image_template %s %d" % (image_prefix, run_number)

    image_template = IMAGE_TEMPLATE % (image_prefix, run_number)

    # print "image_template: %s" % image_template

    return image_template

def calculate_flux(header, site_params):
    """
    Calculate the flux as a function of transmission and aperture size.
    """
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

    if path_split[st].startswith("gpfs"):
        gpfs = path_split[st]
        if path_split[st+1] == "users":
            users = path_split[st+1]
            if path_split[st+2]:
                inst = path_split[st+2]
                if path_split[st+3]:
                    group = path_split[st+3]

    if group:
        data_root_dir = os.path.join("/", *path_split[st:st+4])
    elif inst:
        data_root_dir = os.path.join("/", *path_split[st:st+3])
    else:
        data_root_dir = False

    #return the determined directory
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

    # Calculate flux, new beam size and add them to header
    if beam_settings:
        flux, x_size, y_size = calculate_flux(header, beam_settings)
        header['flux'] = flux
        header['x_beam_size'] = x_size
        header['y_beam_size'] = y_size

    basename = os.path.basename(input_file)
    header["image_prefix"] = "_".join(basename.replace(".cbf", "").split("_")[:-2])
    header["run_number"] = int(basename.replace(".cbf", "").split("_")[-2])

    # Add tag for module to header
    header["rapd_detector_id"] = "necat_dectris_eiger16m"

    # The image template for processing
    header["image_template"] = IMAGE_TEMPLATE % (header["image_prefix"], header["run_number"])
    header["run_number_in_template"] = RUN_NUMBER_IN_TEMPLATE
    header['data_root_dir'] = get_data_root_dir(input_file)

    # Return the header
    return header

# functions for RDMA
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

    # Test get_data_root_dir with new epu filenames
    #print get_data_root_dir("/epu2/rdma/gpfs2/users/stanford/feng_E_3426/images/minrui/snaps/ZH_PAIR_0_000144/ZH_PAIR_0_000144.cbf")
    #print get_data_root_dir("/gpfs1/users/ucsd/corbett_C_3425/images/Kevin/runs/2_9/0_0/2_9_1_0854.cbf")
    fl = FileLocation()
    fl.test()
    print fl.get_path('/gpfs2/users/mskcc/stewart_E_3436/images/yehuda/runs/m12a/m12a_1_000001.cbf')
    fl.release_data('/gpfs2/users/mskcc/stewart_E_3436/images/yehuda/runs/m12a/m12a_1_000001.cbf')