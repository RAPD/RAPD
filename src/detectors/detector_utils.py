"""
Detector utilities
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2016-2017 Cornell University
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
import importlib
import os
import shutil
import sys
import tempfile

# Phenix imports
from dxtbx.format.Registry import Registry
from iotbx.detectors import ImageFactory

# RAPD imports
import utils.convert_hdf5_cbf as convert_hdf5_cbf
import utils.text as text
import detector_list


def print_detector_info(image):
    """
    Print out information on the detector given an image
    """

    from iotbx.detectors import ImageFactory

    image_basename = os.path.basename(image)

    try:
        i = ImageFactory(image)
    except IOError as e:
        if "no format support found for" in e.message:
            print "No format support for %s" % image_basename
            return False
        else:
            print e
            return False
    except AttributeError as e:
        if "object has no attribute 'detectorbase'" in e.message:
            print "No format support for %s" % image_basename
            return False
        else:
            print text.red + e.message + text.stop
            return False


    print "\nInformation from iotbx ImageFactory"
    print "%20s::%s" % ("image", image_basename)
    print "%20s::%s" % ("vendortype", str(i.vendortype))
    # print "%20s" % "Parameters"
    for key, val in i.parameters.iteritems():
        print "%20s::%s" % (key, val)

def print_detector_info2(image):
    """
    Print out information on the detector given an image
    """

    format_instance = Registry.find(image)
    instance = format_instance(image)
    # adds parameters (iotbx)
    temp = instance.get_detectorbase()

    print "\nInformation from dxtbx Registry"
    for key, val in temp.parameters.iteritems():
        print "%20s::%s" % (key, val)

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

    print "get_detector_file %s" % image

    try:
        i = ImageFactory(image)
        # print i.vendortype
        # print i.parameters["DETECTOR_SN"]
    except (IOError, AttributeError, RuntimeError):
        print error
        return False

    # print i.vendortype
    # print i.parameters["DETECTOR_SN"]

    if (i.vendortype, i.parameters["DETECTOR_SN"]) in detector_list.DETECTORS:
        print "%s: %s %s %s" % (image, detector_list.DETECTORS[(i.vendortype, i.parameters["DETECTOR_SN"])], i.vendortype, i.parameters["DETECTOR_SN"])
        return detector_list.DETECTORS[(i.vendortype, i.parameters["DETECTOR_SN"])]
    else:
        return False

def load_detector(detector):
    """
    Search for detector file, load, and return it
    """

    # print "load_detector %s" % detector

    if isinstance(detector, dict):
        detector = detector.get("detector")

    def look_for_detector_file(file, directory):
        """
        Look for a detector file in the given directory
        """

        print "look_for_detector_file %s %s" % (file, directory)

        if "sites" in directory:
            files = glob.glob(directory+"/"+file+".py")
        else:
            files = glob.glob(directory+"/*/"+file+".py")

        if len(files):
            fullpath_file = files[0]
            split_path_file = fullpath_file.split("/")
            if "sites" in split_path_file:
                return ".".join(split_path_file[split_path_file.index("sites"):]).replace(".py", "")
            else:
                return ".".join(split_path_file[split_path_file.index("detectors"):]).replace(".py", "")
        else:
            return False

    # Look for the src/detectors directory
    detectors_dir = False
    for path in sys.path:
        if path.endswith("src") and os.path.exists(os.path.join(path, "detectors")):
            detectors_dir = os.path.join(path, "detectors")
            break

    detector_file = False

    # Search the src/detectors dir
    detector_file = look_for_detector_file(detector, detectors_dir)

    # Search the sites/detectors dir
    if not detector_file:
        sites_dir = False
        for path in sys.path:
            if path.endswith("src") and os.path.exists(os.path.join(path, "sites", "detectors")):
                sites_dir = os.path.join(path, "sites", "detectors")
                break
        detector_file = look_for_detector_file(detector, sites_dir)

    # No module found == bad
    if detector_file == False:
        raise Exception, "No detector file found for %s" % detector
    else:
        module = importlib.import_module(detector_file)
        return module

def main(test_images):
    """Print out some detector information"""

    for test_image in test_images:

        tmp_dir = False

        if test_image.endswith(".h5"):
            print "HDF5 file  - converting"

            tmp_dir = tempfile.mkdtemp()

            converter = convert_hdf5_cbf.hdf5_to_cbf_converter(master_file=test_image,
                                                               output_dir=tmp_dir,
                                                               prefix="tmp",
                                                               start_image=1,
                                                               end_image=1)
            converter.run()

            test_image = "%s/tmp00001.cbf" % tmp_dir

        # try:
        print_detector_info(test_image)
        print_detector_info2(test_image)

        print "\nRAPD detector registry"
        detector = get_detector_file(test_image)
        if detector:
            print "%20s::%s" % ("detector", detector)
        else:
            print "%20s::%s" % ("detector", "unknown")
        # except:
        #     print "%20s::%s" % ("error", "Severe error reading %s" % os.path.basename(test_image))

        print "====="

        if tmp_dir:
            shutil.rmtree(tmp_dir)



if __name__ == "__main__":

    # Get image name from the commandline
    if len(sys.argv) > 1:
        test_images = sys.argv[1:]
        main(test_images)
    else:
        print text.red + "No input image" + text.stop
        sys.exit(9)
