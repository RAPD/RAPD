"""
Detector utilities
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

__created__ = "2016-11-21"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import glob
import os
import sys

# RAPD imports
import utils.text as text
import detector_list

def print_detector_info(image):
    """
    Print out information on the detector given an image
    """

    from iotbx.detectors import ImageFactory

    try:
        i = ImageFactory(image)
    except IOError as e:
        if "no format support found for" in e.message:
            print text.red + "No format support for %s" % image + text.stop
            return False
        else:
            print e
            return False
    except AttributeError as e:
        if "object has no attribute 'detectorbase'" in e.message:
            print text.red + "No format support for %s" % image + text.stop
            return False
        else:
            print text.red + e.message + text.stop
            return False


    print "\n" + image
    print "%20s: %s" % ("vendortype", str(i.vendortype))
    print "%20s" % "Parameters"
    for key, val in i.parameters.iteritems():
        print "%20s: %s" % (key, val)

def get_detector_files():
    """
    Returns a list of detector files

    Uses the PYTHONPATH to find the sites/detectors directory and the detectors directory
    for this rapd install and then walks them to find all files that have names that match "*.py"
    and do not start with "_" or have the word "secret"
    """

    def look_for_detector_files(directory):
        """
        Look for detector files in the given directory
        """
        potential_files = []
        for filename in glob.glob(directory+"/*.py"):
            # No secret-containing files
            if "secret" in filename:
                continue
            # No files that start with _
            if os.path.basename(filename).startswith("_"):
                continue
            # Filename OK
            potential_files.append(os.path.join(path, filename))

        return potential_files

    possible_files = []

    # Looking for the rapd src directory
    detectors_dir = False
    for path in sys.path:
        if path.endswith("src") and os.path.exists(os.path.join(path, "detectors")):
            detectors_dir = os.path.join(path, "detectors")
            break
    # print detectors_dir

    if detectors_dir:
        possible_files += look_for_detector_files(detectors_dir + "/*")
        # print possible_files

    site_detectors_dir = False
    for path in sys.path:
        if path.endswith("src") and os.path.exists(os.path.join(path, "sites/detectors")):
            site_detectors_dir = os.path.join(path, "sites/detectors")
            break

    if site_detectors_dir:
        possible_files += look_for_detector_files(site_detectors_dir)

    return possible_files

def get_detector_file(image):
    """
    Returns the RAPD detector file given an image file
    """

    from iotbx.detectors import ImageFactory

    try:
        i = ImageFactory(image)
        # print i.vendortype
        # print i.parameters["DETECTOR_SN"]
    except: # (IOError, AttributeError, RuntimeError):
        # print error
        return False


    if (i.vendortype, i.parameters["DETECTOR_SN"]) in detector_list.DETECTORS:
        print "%s: %s %s %s" % (image, detector_list.DETECTORS[(i.vendortype, i.parameters["DETECTOR_SN"])], i.vendortype, i.parameters["DETECTOR_SN"])
        return True
    else:
        return False

if __name__ == "__main__":

    # Get image name from the commandline
    if len(sys.argv) > 1:
        test_images = sys.argv[1:]
    else:
        print text.red + "No input image" + text.stop
        sys.exit(9)


    for test_image in test_images:
        try:
            if not get_detector_file(test_image):
                print_detector_info(test_image)
        except:
            print text.red + "Severe error reading %s" % test_image + text.stop
