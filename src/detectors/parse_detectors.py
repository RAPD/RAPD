"""
Parse through detector information file compilation and identify unique detectors
"""

__license__ = """
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

__created__ = "2016-12-01"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import pprint
import sys

# RAPD imports
import utils.text as text

if __name__ == "__main__":

    # Get image name from the commandline
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        print input_file
    else:
        print text.red + "No input file" + text.stop
        sys.exit(9)

    # Import the file
    inlines = open(input_file, "r").readlines()

    # Hold stuff
    detectors = []
    detectors_sorted = {}
    detector = {}

    for line in inlines:
        sline = line.strip()
        if len(sline) > 0:
            # print ">>%s<<" % sline
            if "=====" == sline:
                print len(detectors)
                pprint.pprint(detector)
                detectors.append(detector.copy())
                detector_key = (detector.get("vendortype", "unknown"), detector.get("DETECTOR_SN", "0"))
                if not detector_key in detectors_sorted:
                    detectors_sorted[detector_key] = []
                detectors_sorted[detector_key].append(detector)
                detector = {}
            elif "***** oscillation angle not omega" == sline:
                continue
            elif "No format support for fetch.txt" == sline:
                continue
            elif "No format support for ones_filtered.txt" == sline:
                continue
            else:
                key, val = sline.split("::")
                detector[key] = val

    pprint.pprint(detectors_sorted)
