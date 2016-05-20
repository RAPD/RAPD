# -*- coding: utf-8 -*-

""" XIO plugin for the minicbf format of images (DECTRIS-PILATUS).
"""

__version__ = "0.1.0"
__author__ = "Pierre Legrand (pierre.legrand@synchrotron-soleil.fr)"
__date__ = "12-11-2009"
__copyright__ = "Copyright (c) 2009 Pierre Legrand"
__license__ = "New BSD, http://www.opensource.org/licenses/bsd-license.php"

import time

HEADER_KEYS = ["Detector:", "Pixel_size", "Silicon", "Exposure_time",
"Exposure_period", "Tau", "Count_cutoff", "Threshold_setting",
"N_excluded_pixels","Excluded_pixels:", "Flat_field:", "Trim_directory:",
"Wavelength", "Energy_range", "Detector_distance", "Detector_Voffset",
"Beam_xy","Flux","Filter_transmission","Start_angle", "Angle_increment",
"Detector_2theta", "Polarization", "Alpha", "Kappa", "Phi", "Chi",
"Oscillation_axis", "N_oscillations"]

def date_time(timestr):
    "from str return timestr + msec"
    t_a, t_b = timestr.split(".")
    return time.strptime(t_a, "%Y/%b/%d %H:%M:%S"), float("0."+t_b)

def date_seconds(timestr):
    "from str return seconds"
    t_a, msec = date_time(timestr)
    return time.mktime(t_a) + msec

def get_edge_resolution(pixel_x, width, distance, wavelength):
    "Calculate EdgeResolution"
    from math import sin, atan
    if distance > 0.0:
        rad = 0.5 * float(pixel_x) * int(width)
        return float(wavelength)/sin(atan(rad/float(distance)))
    else:
        return 0.

FLOAT1 = lambda x: float(x.split()[0])
FLOAT2 = lambda x: float(x.split()[0])*1e3

BEAMX = lambda x, y: float(x[x.find("(")+1:x.find(")")-1].split(",")[0])\
                                                               *FLOAT2(y)
BEAMY = lambda x, y: float(x[x.find("(")+1:x.find(")")-1].split(",")[1])\
                                                               *FLOAT2(y)

class Interpreter:
    "Dummy class, container for standard Dict and Function."

    HTD = {
    # The adsc Header Translator Dictionary.
    # Potential problems:
    # - There are multiple SIZE1, SIZE2 instances.
    # = The orientation of SIZE1 and SIZE2 is unknown
    #     Not a problem as long as SIZE1 = SIZE2..

    'ExposureTime':(['Exposure_time'], FLOAT1),
    'BeamX':(['Beam_xy', 'Pixel_size'], BEAMX),
    'BeamY':(['Beam_xy', 'Pixel_size'], BEAMY),
    'Distance':(['Detector_distance'], FLOAT2),
    'Wavelength':(['Wavelength'], FLOAT1),
    'PixelX':(['Pixel_size'], FLOAT2),
    'PixelY':(['Pixel_size'], FLOAT2),
    'Width':(['Binary-Size-Fastest-Dimension'], int),
    'Height':(['Binary-Size-Second-Dimension'], int),
    #'Message':(['MESSAGE'], lambda x: x.split(';')),
    'PhiStart':(['Start_angle'], FLOAT1),
    'PhiEnd':(['Start_angle', 'Angle_increment'], \
                     lambda x, y: FLOAT1(x)+FLOAT1(y)),
    'PhiWidth':(['Angle_increment'], FLOAT1),
    #'EdgeResolution':(['PIXEL_SIZE','SIZE1','DISTANCE','WAVELENGTH'],
    #    getEdgeResolution),

    # Added keys from Graeme's convention.
    'TwoTheta':(['Detector_2theta'], FLOAT1),   # No example yet...
    'SerialNumber':(['Detector:'], str),
    'HeaderSize':(['HEADER_SIZE'], int),
    'OscAxis':(['Oscillation_axis'], lambda x: x.split(",")[0].lower().strip()),
    'DateStr':(['DATE'], str),
    'DateSeconds':(['DATE'], date_seconds),
    }

    SpecialRules = {
    # No special rules for now
    }

    Identifiers = {
    # Based on Serial Number. Contains (Synchrotron,BLname,DetectorType)
    #413:('ESRF','ID14EH2','ADSC Q4'),
    #420:('ESRF','ID14EH4','ADSC Q4R'),
    }

    def __init__(self):
        self.raw_head_dict = None

    def getRawHeadDict(self, raw_head):
        "Intepret the ascii structure of the minicbf image header."

        i_1 = 28+raw_head.find("_array_data.header_contents")
        i_2 = raw_head.find("_array_data.data", i_1)
        i_3 = raw_head.find("--CIF-BINARY-FORMAT-SECTION--", i_2)+29
        i_4 = i_3+500
        lis = [line[2:].strip().split(" ", 1) \
                   for line in raw_head[i_1:i_2].splitlines() \
                       if line and line[0]=="#"]
        lis2 = [line[2:].strip().split(": ", 1) \
                   for line in raw_head[i_3:i_4].splitlines() \
                       if line and line[0:2]=="X-"]
        self.raw_head_dict = {}
        for val in lis:
            if (val[0] in HEADER_KEYS):
                if len(val) == 2:
                    self.raw_head_dict[val[0]] = val[1]
                else:
                    self.raw_head_dict[val[0]] = None
        self.raw_head_dict.update(dict([ val for val in lis2 \
                                             if "Binary-" in val[0]]))
        self.raw_head_dict.update({'HEADER_SIZE': i_3})
        self.raw_head_dict.update({'DATE': " ".join(lis[1])})
        self.raw_head_dict.update({'MESSAGE': '', 'TWO_THETA': '0'})
        return self.raw_head_dict
