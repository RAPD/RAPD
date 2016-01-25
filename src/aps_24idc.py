"""Working on method for reading the Pilatus header for APS 24ID-C"""
import re
import os
import unittest

_FACILITY = "APS"
_BEAMLINE = "24IDE"
_DETECTOR = "PILATUS 6M-F"
_START = "2014-01-01"
_END = False
_TESTIMAGE = "test_image.cbf"

def read_header(image):
    """Return header items for APS 24ID-C Pilatus 6M-F"""
    # Make sure the image has the correct suffix
    if not image.endswith(".cbf"):
        return False

    # Go through the file header until we find the end of the data we need
    try:
        filehandle = open(image, "rb", 2048)
        counter = 0
        file_buffer = ""
        while counter < 10:
            try:
                file_buffer += filehandle.read(1024)
                end = file_buffer.index("_array_data.data") - 1
                #end = buffer.index("X-Binary-Size-Padding:") + 29
                header = file_buffer[0:end]
                break
            # Exception triggered if the search string is not found
            except ValueError:
                counter += 1
        # Explicitly close the file
        filehandle.close()
        # Parse the header
        #item:(pattern,transform[,units])
        header_items = {
          "cbf_ver"      : (r"^###CBF: VERSION\s*([\d\.]+)",
                            lambda x: float(x)),
          "cbflib_ver"   : (r"\s*CBFlib v([\d\.]+)",
                            lambda x: str(x)),
          "header_conv"  : (r"header_convention\s*\"([\w\d\._]+)\"",
                            lambda x: str(x)),
          "detector"     : (r"^# Detector:\s*([\w\d\s\-]+)\s*\,",
                            lambda x: str(x)),
          "detector_sn"  : (r"S\/N ([\w\d\-]*)\s*",
                            lambda x: str(x)),
          "date"         : (r"^# ([\d\-]+T[\d\.\:]+)\s*",
                            lambda x: str(x)),
          "pixel_size"   : (r"^# Pixel_size\s*(\d+)e-6 m.*",
                            lambda x: float(x)/1000,
                            "um"),
          "time"         : (r"^# Exposure_time\s*([\d\.]+) s",
                            lambda x: float(x),
                            "s"),
          "period"       : (r"^# Exposure_period\s*([\d\.]+) s",
                            lambda x: float(x),
                            "s"),
          "tau"          : (r"^# Tau\s*\=\s*([\d\.\-e]+)\s*s",
                            lambda x: float(x),
                            "s"),
          "count_cutoff" : (r"^# Count_cutoff\s*(\d+) counts",
                            lambda x: int(x)),
          "threshold"    : (r"^# Threshold_setting:\s*(\d+)\s*eV",
                            lambda x: int(x),
                            "ev"),
          "gain"         : (r"# Gain_setting:[\s\w]*\([\s\w]*=\s*([\d\.\-]*)\s*\)",
                            lambda x: float(x)),
          "excluded_px"  : (r"^# N_excluded_pixels\s*=\s*(\d*)",
                            lambda x: int(x)),
          "wavelength"   : (r"^# Wavelength\s*([\d\.]+) A",
                            lambda x: float(x),      "ang"),
          "beam_y"       : (r"^# Beam_xy \(([\d\.]+)\,\s*[\d\.]+\)\s*pixels",
                            lambda x: float(x),
                            "px"),
          "beam_x"       : (r"^# Beam_xy \([\d\.]+\,\s*([\d\.]+)\)\s*pixels",
                            lambda x: float(x),
                            "px"),
          "distance"     : (r"^# Detector_distance\s*([\d\.]+) m",
                            lambda x: float(x)*1000,
                            "mm"),
          "transmission" : (r"^# Filter_transmission\s*([\d\.]+)",
                            lambda x: float(x),
                            "pct"),
          "osc_start"    : (r"^# Start_angle\s*([\d\.]+)\s*deg",
                            lambda x: float(x),
                            "deg"),
          "osc_range"    : (r"^# Angle_increment\s*([\d\.]*)\s*deg",
                            lambda x: float(x),
                            "deg"),
          "twotheta"     : (r"^# Detector_2theta\s*([\d\.]*)\s*deg",
                            lambda x: float(x),
                            "deg")}
        
        # Store the derived data
        parameters = {"fullname":os.path.realpath(image)}
        # Use the header items to search the header
        for label, pat in header_items.iteritems():
            # print label
            pattern = re.compile(pat[0], re.MULTILINE)
            matches = pattern.findall(header)
            if len(matches) > 0:
                parameters[label] = pat[1](matches[-1])
            else:
                parameters[label] = None
        #Get correct beam center
        parameters['beam_x']*=parameters['pixel_size']
        parameters['beam_y']*=parameters['pixel_size']
        # Return what has been gleaned from the header
        return parameters

    # Image file missing
    except IOError:
        return False


class TestReadHeader(unittest.TestCase):
    """Test cases for the read_header function"""

    def test_data_missing(self):
        """read_header should return False if called on a missing file"""
        self.assertFalse(read_header("none"))

    def test_wrong_suffix(self):
        """read_header should return False for wrong suffix"""
        self.assertFalse(read_header("test_image.img"))

    def test_data_correct(self):
        """read_header can return correct values from test image"""
        result = read_header(_TESTIMAGE)
        expected_result = {"tau": 1.991e-07,
                           "period": 1.0,
                           "osc_start": 237.0,
                           "threshold": 6333,
                           "wavelength": 0.9789,
                           "cbf_ver": 1.5,
                           "osc_range": 0.15,
                           "pixel_size": 172,
                           "detector": "PILATUS 6M-F",
                           "count_cutoff": 1380198,
                           "cbflib_ver": "0.7.8",
                           "twotheta": 0.0,
                           "gain": -0.2,
                           "date": "2014-02-22T23:42:20.102",
                           "detector_sn": "60-0112-F",
                           "beam_x": 1282.68,
                           "beam_y": 1259.31,
                           "distance": 600.0,
                           "transmission": 17.6786,
                           "excluded_px": 536,
                           "time": 1.0,
                           "header_conv": "PILATUS_1.2"}
        expected_result["fullname"] = os.path.realpath(_TESTIMAGE)
        self.assertEqual(expected_result, result)

if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TestReadHeader)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
