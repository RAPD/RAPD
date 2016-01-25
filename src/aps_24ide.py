"""Working on method for reading the Pilatus header for aps24idc"""
import re
import os
import unittest

_FACILITY = "APD"
_BEAMLINE = "24IDE"
_DETECTOR = "ADSC Q315r"
_START = "2014-01-01"
_END = False
_TESTIMAGE = "test_image.img"

def read_header(image):
    """Read the header for NE-CAT ADSC Q315r"""
    # Make sure the image has the correct suffix
    if not image.endswith(".img"):
        return False

    # Go through the file header until we find the end of the data we need
    try:
        filehandle = open(image, "rb", 2048)
        counter = 0
        file_buffer = ""
        while counter < 10:
            try:
                file_buffer += filehandle.read(1024)
                start = file_buffer.index("{")
                end = file_buffer.index("}") - 1
                header = file_buffer[start:end]
                break
            # Exception triggered if the search string is not found
            except ValueError:
                counter += 1
        # Explicitly close the file
        filehandle.close()
        # Parse the header
        #item:(pattern,transform[,units])
        header_items = {
            "header_bytes" : (r"^HEADER_BYTES=\s*(\d+)\;",
                             lambda x: int(x)),
            "dim"          : (r"^DIM=\s*(\d+)\;",
                              lambda x: int(x)),
            "byte_order"   : (r"^BYTE_ORDER=\s*([\w_]+)\;",
                              lambda x: str(x)),
            "type"         : (r"^TYPE=\s*([\w_]+)\;",
                              lambda x: str(x)),
            "size1"        : (r"^SIZE1=\s*(\d+)\;",
                              lambda x: int(x)),
            "size2"        : (r"^SIZE2=\s*(\d+)\;",
                              lambda x: int(x)),
            "pixel_size"   : (r"^PIXEL_SIZE=\s*([\d\.]+)\;",
                              lambda x: float(x)),
            "bin"          : (r"^BIN=\s*(\w*)\;",
                              lambda x: str(x)),
            "adc"          : (r"^ADC=\s*(\w+)\;",
                              lambda x: str(x)),
            "detector_sn"  : (r"^DETECTOR_SN=\s*(\d+)\;",
                              lambda x: int(x)),
            "collect_mode" : (r"^COLLECT_MODE=\s*(\w*)\;",
                              lambda x: str(x)),
            "beamline"     : (r"^BEAMLINE=\s*(\w+)\;",
                              lambda x: str(x)),
            "date"         : (r"^DATE=\s*([\w\d\s\:]*)\;",
                              date_adsc_to_sql),
            "time"         : (r"^TIME=\s*([\d\.]+)\;",
                              lambda x: float(x)),
            "distance"     : (r"^DISTANCE=\s*([\d\.]+)\;",
                              lambda x: float(x)),
            "osc_range"    : (r"^OSC_RANGE=\s*([\d\.]+)\;",
                              lambda x: float(x)),
            "sweeps"       : (r"^SWEEPS=\s*(\d*)\;",
                              lambda x: int(x)),
            "phi"          : (r"^PHI=\s*([\d\.]+)\;",
                              lambda x: float(x)),
            "osc_start"    : (r"^OSC_START=\s*([\d\.]+)\;",
                              lambda x: float(x)),
            "twotheta"     : (r"^TWOTHETA=\s*([\d\.]+)\;",
                              lambda x: float(x)),
            "thetadistance": (r"^TWOTHETADIST=\s*([\d\.]+)\;",
                              lambda x: float(x)),
             #"axis"         : (r"^AXIS=\s*(\w+)\;", lambda x: str(x)),
            "wavelength"   : (r"^WAVELENGTH=\s*([\d\.]+)\;",
                              lambda x: float(x)),
            "beam_x"       : (r"^BEAM_CENTER_X=\s*([\d\.]+)\;",
                              lambda x: float(x)),
            "beam_y"       : (r"^BEAM_CENTER_Y=\s*([\d\.]+)\;",
                              lambda x: float(x)),
            "transmission" : (r"^TRANSMISSION=\s*([\d\.]+)\;",
                              lambda x: float(x)),
            "puck"         : (r"^PUCK=\s*(\w+)\;",
                              lambda x: str(x)),
            "sample"       : (r"^SAMPLE=\s*([\d\w]+)\;",
                              lambda x: str(x)),
            "ring_cur"     : (r"^RING_CUR=\s*([\d\.]+)\;",
                              lambda x: float(x)),
            "ring_mode"    : (r"^RING_MODE=\s*(.*)\;",
                              lambda x: str(x)),
            "md2_aperture" : (r"^MD2_APERTURE=\s*(\d+)\;",
                              lambda x: int(x))}
        
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

        # Return what has been gleaned from the header
        return parameters

    # Image file missing
    except IOError:
        return False

_MONTHS = {"Jan" : "01",
           "Feb" : "02",
           "Mar" : "03",
           "Apr" : "04",
           "May" : "05",
           "Jun" : "06",
           "Jul" : "07",
           "Aug" : "08",
           "Sep" : "09",
           "Oct" : "10",
           "Nov" : "11",
           "Dec" : "12"}

def date_adsc_to_sql(datetime_in):
    """Transform an ADSC-formatted date to the for YYYY-MM-DDTHH:MM:SS"""
    spldate = datetime_in.split()
    time = spldate[3]
    year = spldate[4]
    month = _MONTHS[spldate[1]]
    day = "{:02d}".format(int(spldate[2]))
    date = "-".join((year, month, day))
    return "T".join((date, time))


class TestReadHeader(unittest.TestCase):
    """Test read_header"""

    def test_data_missing(self):
        """readHeader should return False if called on a missing file"""
        self.assertFalse(read_header("none"))

    def test_wrong_suffix(self):
        """readHeader should return False for wrong suffix"""
        self.assertFalse(read_header("test_image.cbf"))

    def test_data_correct(self):
        """readHeader can return correct values from test image"""
        result = read_header(_TESTIMAGE)
        #import pprint
        #printer = pprint.PrettyPrinter()
        #printer.pprint(result)
        expected_result = {
            "puck": "A",
            "phi": 90.0,
            "sample": "1",
            "ring_mode": "0+24x1,_~1.2%_Coupling,_Cogging",
            "osc_start": 90.0,
            "wavelength": 0.97919,
            "size1": 3072,
            "size2": 3072,
            "osc_range": 1.0,
            "sweeps": 1,
            "adc": "slow",
            "beamline": "24_ID_E",
            "type": "unsigned_short",
            "bin": "2x2",
            "byte_order": "little_endian",
            "md2_aperture": 50,
            "dim": 2,
            "time": 1.0,
            "twotheta": 0.0,
            "date": "2014-02-19T10:35:53",
            "detector_sn": 916,
            "pixel_size": 0.10259,
            "distance": 1200.01,
            "transmission": 5.1602,
            "ring_cur": 102.0,
            "beam_y": 160.6486,
            "beam_x": 142.2993,
            "thetadistance": 1200.00,
            "fullname": "/Users/fmurphy/workspace/rapd2/play/python/headers/aps/24ide/test_image.img",
            "header_bytes": 1024,
            "collect_mode": "SNAP"}
        expected_result["fullname"] = os.path.realpath(_TESTIMAGE)
        self.assertEqual(expected_result, result)

if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TestReadHeader)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
