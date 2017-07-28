# -*- coding: utf-8 -*-

""" XIO plugin for the ADSC image format.
"""

__version__ = "0.4.1"
__author__ = "Pierre Legrand (pierre.legrand \at synchrotron-soleil.fr)"
__date__ = "30-11-2009"
__copyright__ = "Copyright (c) 2005-2009 Pierre Legrand"
__license__ = "New BSD, http://www.opensource.org/licenses/bsd-license.php"

import time

def date_time(time_str):
    "from str return standard str: 'Wed Oct 28 16:42:12 2009'"
    return time.ctime(date_seconds(time_str))

#def _dateseconds(timestr):
#    return time.mktime(time.strptime(timestr))

def date_seconds(time_str):
    "from tupple return seconds"
    try:
        return time.mktime(time.strptime(time_str))
    except (ValueError, TypeError), err:
        print "Warning:", err
        print "... Using time.time() instead."
        return time.time()

def get_edge_resolution(pixel_x, width, distance, wavelength):
    "Calculate EdgeResolution: Graeme's Method"
    from math import sin, atan
    if distance > 0.0:
        rad = 0.5 * float(pixel_x) * int(width)
        return float(wavelength)/sin(atan(rad/float(distance)))
    else:
        return 0.

def endian(code):
    "From str to struct convention."
    if code == 'big_endian':
        return '>'
    else:
        return '<'

class Interpreter:
    "Dummy class, container for standard Dict and Function."

    HTD = {
    # The adsc Header Translator Dictionary.
    # Potential problems:
    # - There are multiple SIZE1, SIZE2 instances.
    # = The orientation of SIZE1 and SIZE2 is unknown
    #     Not a problem as long as SIZE1 = SIZE2..

    'ExposureTime':(['TIME'],float),
    'BeamX':(['BEAM_CENTER_X'], float),
    'BeamY':(['BEAM_CENTER_Y'], float),
    'Distance':(['DISTANCE'], float),
    'Wavelength':(['WAVELENGTH'], float),
    'PixelX':(['PIXEL_SIZE'], float),
    'PixelY':(['PIXEL_SIZE'], float),
    'Width':(['SIZE1'], int),
    'Height':(['SIZE2'], int),
    'Message':(['MESSAGE'], lambda x: x.split(';')),
    'PhiStart':(['OSC_START'], float),
    'PhiEnd':(['OSC_START','OSC_RANGE'], lambda x,y: float(x)+float(y)),
    'PhiWidth':(['OSC_RANGE'], float),
    'EdgeResolution':(['PIXEL_SIZE','SIZE1','DISTANCE','WAVELENGTH'],
           get_edge_resolution),

    # Added keys from Graeme's convention.
    'TwoTheta':(['TWO_THETA'], float),   # Example missing.
    'SerialNumber':(['DETECTOR_SN'], str),
    'HeaderSize':(['HEADER_BYTES'], int),
    'EndianType':(['BYTE_ORDER'], endian),
    'OscAxis':(['OSC_AXIS'], lambda x: x.lower()),
    # Date and time
    #'DateTime':(['DATE'], date_time),
    'DateStr':(['DATE'], str),
    'DateSeconds':(['DATE'], date_seconds),
    }

    SpecialRules = {
    # No special rules for now
    }

    Identifiers = {
    # ESRF info found at
    # http://www.esrf.eu/UsersAndScience/Experiments/MX/Software/PXSOFT/Denzo
    # Based on Serial Number. Contains (Synchrotron,BLname,DetectorType)
    '401':('ALS','???','ADSC Q4'),
    '413':('ESRF','ID14-2','ADSC Q4'),
    '420':('ESRF','ID14-3','ADSC Q4R'),
    '428':('ESRF','ID14-2','ADSC Q4'),
    '444':('ESRF','ID29 or ID14-1','ADSC Q210'),
    '445':('USA?','UNKN','ADSC 210'),
    '917':('ESRF','ID23-1','ADSC 315'),
    '918':('ESRF','ID14-4','ADSC 315'),
    '926':('ALS','ALS831','ADSC 315r'),
    '927':('SOLEIL','PROXIMA1','ADSC 315r'),
    }

    def __init__(self):
        self.raw_head_dict = None

    def getRawHeadDict(self, raw_head):
        "Intepret the ascii structure of the asdc image header."

        _lis = raw_head[2:].split("}")[0].split(";\n")[:-1]
        self.raw_head_dict = dict([par.split("=") for par in _lis])
        self.raw_head_dict.update({'MESSAGE': '', 'TWO_THETA': '0'}) # Example missing
        return self.raw_head_dict
