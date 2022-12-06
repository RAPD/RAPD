"""
Detector utilities
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2016-2023 Cornell University
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
from pprint import pprint
import shutil
import sys
import tempfile

# CCTBX imports
# from dxtbx.format.Registry import Registry
from dxtbx.format import Registry
import h5py
from iotbx.detectors import ImageFactory

# RAPD imports
import detectors.detector_list as detector_list
import utils.convert_hdf5_cbf as convert_hdf5_cbf
import utils.text as text

parameters_to_get = (
    "beam_center_x",
    "beam_center_y",
    ####
    "chi",
    "chi_end",
    "chi_increment",
    "chi_range_average",
    "chi_range_total",
    "chi_start",
    "data_collection_date",
    "kappa",
    "kappa_end",
    "kappa_increment",
    "kappa_range_average",
    "kappa_range_total",
    "kappa_start",
    "omega",
    "omega_end",
    "omega_increment",
    "omega_range_average",
    "omega_range_total",
    "omega_start",
    "phi",
    "phi_end",
    "phi_increment",
    "phi_range_average",
    "phi_range_total",
    "phi_start",
    ####
    "incident_wavelength",
    ####
    "bit_depth_image",
    "bit_depth_readout",
    "count_time",
    "detector_distance",
    "detector_number",
    "detector_readout_time",
    "frame_count_time",
    "frame_period",
    "frame_time",
    "number_of_excluded_pixels",
    # "pixel_mask",
    "sensor_thickness",
    "threshold_energy",
    "two_theta",
    "two_theta_end",
    "two_theta_increment",
    "two_theta_range_average",
    "two_theta_range_total",
    "two_theta_start",
    "x_pixel_size",
    "x_pixels_in_detector",
    "y_pixel_size",
    "y_pixels_in_detector",
)

def print_detector_info(image: str) -> None:
    """
    Print out information on the detector given an image
    """

    image_basename = os.path.basename(image)

    try:
        i = ImageFactory(image)
    except IOError as e:
        if "no format support found for" in e.message:
            print("No format support for %s" % image_basename)
            return False
        else:
            print(e)
            return False
    except AttributeError as e:
        if "object has no attribute 'detectorbase'" in e.message:
            print("No format support for %s" % image_basename)
            return False
        else:
            print(text.red + e.message + text.stop)
            return False


    print("\nInformation from iotbx ImageFactory")
    print("=====================================")
    print("%20s::%s" % ("image", image_basename))
    print("%20s::%s" % ("vendortype", str(i.vendortype)))
    # print "%20s" % "Parameters"
    for key, val in i.parameters.items():
        print("%20s::%s" % (key, val))

def print_detector_info2(image: str) -> None:
    """
    Print out information on the detector given an image
    """

    format_instance = Registry.find(image)
    instance = format_instance(image)
    # adds parameters (iotbx)
    temp = instance.get_detectorbase()

    print("\nInformation from dxtbx Registry")
    print("=================================")
    for key, val in temp.parameters.items():
        print("%20s::%s" % (key, val))

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

def get_detector_file(image: str):
    """
    Returns the RAPD detector file given an image file
    """

    # print "get_detector_file %s" % image
    try:
        i = ImageFactory(image)
        # print i.vendortype
        # print i.parameters["DETECTOR_SN"]
    except (IOError, AttributeError, RuntimeError):
        print(error)
        return False

    # print ">>>%s<<<" % i.vendortype
    # print ">>>%s<<<" % i.parameters["DETECTOR_SN"]

    v_type = i.vendortype.strip()
    sn = str(i.parameters["DETECTOR_SN"]).strip()

    # pprint(detector_list.DETECTORS)

    if (v_type, sn) in detector_list.DETECTORS:
        # print "%s: %s %s %s" % (image, detector_list.DETECTORS[(v_type, sn)], v_type, sn)
        return detector_list.DETECTORS[(v_type, sn)]
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
        raise Exception("No detector file found for %s" % detector)
    else:
        module = importlib.import_module(detector_file)
        return module

def merge_xds_input(base, new):
    """Merge base xds_inp with changes/additions from new"""
    new_inp = []
    skip = False
    # replace existing keywords in base xds
    for line in base:
        try:
            if len(new[0]) > 0:
                for x in range(len(new)):
                    if line[0] == new[x][0]:
                        line = new.pop(x)
                        break
        except IndexError:
            # print 'nothing left in inp1'
            skip = True
        #new_inp.append("%s%s"%('='.join(line), '\n'))
        new_inp.append(line)
    # Skip if nothing left to add
    if skip == False:
        # Add new keywords
        if len(new[0]) > 0:
            for line in new:
                #new_inp.append("%s%s"%('='.join(line), '\n'))
                new_inp.append(line)

    return new_inp

def reorder_input(inp0, inp1):
    """
    Compares the detector file to the sites.detector file.
    Generates new XDS parameters to put in the site.detector file"""
    # inp0 is from detector
    # inp1 is from site
    temp0 = []
    temp1 = []
    unt0 = []
    unt1 = []
    same = []
    
    # put into list if not otherwise
    if isinstance(inp0, dict):
        temp0 = [(key, value) for key, value in inp0.items()]
        temp0.sort()
        # print converted
        print('-------inp0-------')
        for line in temp0:
            print(line, ',')
            #print '(%s, %s),'%tuple(line)
    else:
        temp0 = inp0
        temp0.sort()

    if isinstance(inp1, dict):
        temp1 = [(key, value) for key, value in inp1.items()]
        temp1.sort()
        # print converted
        print('-------inp1-------')
        for line in temp1:
            print(line, ',')
    else:
        temp1 = inp1
        temp1.sort()
    # Separate the UNTRUSTED_ lines for separate sorting
    if len(temp0[0]) > 0:
        unt0 = [ l0[1] for l0 in temp0 if l0[0].count('UNTRUSTED_')]
        unt0.sort()
        temp0 = [ l0 for l0 in temp0 if l0[0].count('UNTRUSTED_') == False]
    if len(temp1[0]) > 0:
        unt1 = [ l1[1] for l1 in temp1 if l1[0].count('UNTRUSTED_')]
        unt1.sort()
        temp1 = [ l1 for l1 in temp1 if l1[0].count('UNTRUSTED_') == False]
        # Assuming we are adding new untrusted regions
        unt1 = [ line for line in unt1 if unt0.count(line) == False]
    if temp0 == []:
        temp0 = [()]
    if temp1 == []:
        temp1 = [()]
    
    
    if len(temp0[0]) > 0 and len(temp1[0]) > 0:
        print('\n-------new params-------')
        # If the same keywords are used, then inp1 takes priority
        for x, l0 in enumerate(temp0):
            for y, l1 in enumerate(temp1):
                # if keyword is the same
                if l0[0] == l1[0]:
                    if l0[1].strip() != l1[1].strip():
                        print(l1, ',')
        for x in range(len(unt1)):
            print("('UNTRUSTED_RECTANGLE%s', '%s'),"%((len(unt0)+1+x), unt1[x]))

def print_hdf5_file_structure(file_name) :
    """
    Prints the HDF5 file structure
    Taken from https://confluence.slac.stanford.edu/display/PSDM/How+to+access+HDF5+data+from+Python#HowtoaccessHDF5datafromPython-Example1:Basicoperations
    """
    file = h5py.File(file_name, 'r') # open read-only
    item = file #["/Configure:0000/Run:0000"]
    print_hdf5_item_structure(item)
    file.close()

def print_hdf5_item_structure(g, offset='    ') :
    """
    Prints the input file/group/dataset (g) name and begin iterations on its content
    Taken from https://confluence.slac.stanford.edu/display/PSDM/How+to+access+HDF5+data+from+Python#HowtoaccessHDF5datafromPython-Example1:Basicoperations
    """
    if   isinstance(g,h5py.File) :
        print(g.file, '(File)', g.name)

    elif isinstance(g,h5py.Dataset) :
        if g.parent.name == "/entry/sample/goniometer":
            print('(Dataset)', g.name, '    len =', g.shape, '    value =', g.value) #, g.dtype
        else:
            print('(Dataset)', g.name, '    len =', g.shape) #, g.dtype

    elif isinstance(g,h5py.Group) :
        print('(Group)', g.name)

    else :
        print('WORNING: UNKNOWN ITEM IN HDF5 FILE', g.name)
        sys.exit ( "EXECUTION IS TERMINATED" )

    if isinstance(g, h5py.File) or isinstance(g, h5py.Group) :
        for key,val in dict(g).items() :
            subg = val
            print(offset, key, end=' ') #,"   ", subg.name #, val, subg.len(), type(subg),
            print_hdf5_item_structure(subg, offset + '    ')

def print_hdf5_header_info(file_name):
    """Prints out information from an hdf5 file"""


    header = read_hdf5_header(file_name)

    print("\n Information from HDF5 file")
    print("============================")

    keys = list(header.keys())
    keys.sort()
    for key in keys:
        print("%20s::%s" % (key, header[key]))
    print("")

def read_hdf5_header(file_name) :
    """Searched the HDF5 file header for information and returns a dict"""
    h5_file = h5py.File(file_name, 'r') # open read-only
    # item = h5_file #["/Configure:0000/Run:0000"]
    header = {}
    interrogate_hdf5_item_structure("root", h5_file, header)
    h5_file.close()
    return header

def interrogate_hdf5_item_structure(key, g, header) :
    """Prints the input file/group/dataset (g) name and begin iterations on its content"""


    if isinstance(g, h5py.Dataset):
        # print "dataset"
        if key in parameters_to_get:
            header[key] = g.value

    if isinstance(g, h5py.File) or isinstance(g, h5py.Group):
        # print "file"
        for new_key, val in dict(g).items():
            # print new_key, val
            subg = val
            #print offset, key, #,"   ", subg.name #, val, subg.len(), type(subg),
            interrogate_hdf5_item_structure(new_key, subg, header)

    return header

def get_resolution_at_edge(xdsinp):
    # Calculate the detector distance or a resolution
    import math
    
    for line in xdsinp:
        print(line)
        
    """
    if self.vendortype.startswith('ADSC'):
        from rapd_site import settings_E as settings
    else:
        from rapd_site import settings_C as settings
    max_dis = settings.get('max_distance')
    min_dis = settings.get('min_distance')
    # percent of resolution to use for distance calculation range.
    percent = 0.1
    _l0 = []
    # Determine the size of the detector face for calc distance using ImageFactory.
    header = read_header(image).parameters
    _l = [header['SIZE1']*header['PIXEL_SIZE'],
          header['SIZE2']*header['PIXEL_SIZE']]
    # Pick the smallest detector dimension
    m = min(_l)
    rad1 = m / 2.0
    #rad2 = math.sqrt(2) * rad1 # For res at corner
    _l = [round(float(res)-float(res)*percent, 1),
          round(float(res),1), 
          round(float(res)+float(res)*percent, 1)]
    try:
        for i in range(len(_l)):
            dis = round(rad1 / math.tan(2 * math.asin(header['WAVELENGTH'] / (2 * _l[i]))), -1)
            # Calc res at min_dis
            if dis < min_dis:
                if i == 0:
                    _l0.append([round(header['WAVELENGTH'] / (2 * math.sin(0.5 * math.atan(rad1 / min_dis))), 1), min_dis])
            # Calc res at max_dis
            elif dis > max_dis:
                _l0.append([round(header['WAVELENGTH'] / (2 * math.sin(0.5 * math.atan(rad1 / max_dis))), 1), max_dis])
                break
            else:
                _l0.append([_l[i], dis])
        return(_l0)
    except:
        return(False)
    """

def main(test_images):
    """Print out some detector information"""

    for test_image in test_images:

        tmp_dir = False

        if test_image.endswith(".h5"):

            print_hdf5_header_info(test_image)

            tmp_dir = tempfile.mkdtemp()
            #prefix = os.path.basename(test_image).replace("_master.h5", "")
            prefix = convert_hdf5_cbf.get_prefix(test_image)

            converter = convert_hdf5_cbf.hdf5_to_cbf_converter(master_file=test_image,
                                                               output_dir=tmp_dir,
                                                               prefix=prefix,
                                                               start_image=1,
                                                               end_image=1,
                                                               overwrite=True)
            converter.run()

            test_image = "%s/%s_000001.cbf" % (tmp_dir, prefix)

        # try:
        print_detector_info(test_image)
        print_detector_info2(test_image)

        print("\nRAPD detector registry")
        print("========================")
        detector = get_detector_file(test_image)
        if detector:
            print("%20s::%s" % ("detector", detector))

        else:
            print("%20s::%s" % ("detector", "unknown"))
            print("RAPD uses (vendortype, DETECTOR_SN) as a key for its detector registry")
        # except:
        #     print "%20s::%s" % ("error", "Severe error reading %s" % os.path.basename(test_image))

        if isinstance(detector, dict):
            print("\nHeader information")
            print("====================")
            if "detector" in detector:
                SITE = False
                detector_target = detector.get("detector")
                detector_module = load_detector(detector_target)
            header = detector_module.read_header(test_image)
            keys = list(header.keys())
            keys.sort()
            for key in keys:
                print("%20s::%s" % (key, header[key]))

        if tmp_dir:
            shutil.rmtree(tmp_dir)



if __name__ == "__main__":
    
    # Get image name from the commandline
    if len(sys.argv) > 1:
        test_images = sys.argv[1:]
        main(test_images)
    else:
        print(text.red + "No input image" + text.stop)
        sys.exit(9)
    """
    import detectors.rigaku.raxis as inp0
    import sites.detectors.ucla_rigaku_raxisivpp as inp1
    reorder_input(inp0.XDSINP, inp1.XDSINP)
    print '----TEST-----'
    for line in inp1.XDSINP:
        print line
    """
    