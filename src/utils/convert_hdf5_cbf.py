"""HDF5 utilities for RAPD"""

"""
This file is part of RAPD

Copyright (C) 2017-2018, Cornell University
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

__created__ = "2017-02-08"
_maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
from itertools import groupby
import multiprocessing
from operator import itemgetter
import os
import subprocess
import sys
import shlex
# import time

# RAPD imports


VERSIONS = {
    "eiger2cbf": ("160415",)
}
# Create function for running
def run_process(input_args, output=False):
    """Run the command in a subprocess.Popen call"""

    command, verbose = input_args

    if verbose:
        print command
    if output:
        job = subprocess.Popen(shlex.split(command),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        #job.wait()
        #return (job.stdout, job.stderr)
        stdout, stderr = job.communicate()
        return (stdout, stderr)
    else:
        job = subprocess.Popen(shlex.split(command))
        job.wait()

class hdf5_to_cbf_converter(object):

    output_images = []
    
    # Parameters used when calculating second image in a pair to convert
    user_overwrite = False
    second_image_number = False

    def __init__(self,
                 master_file,
                 output_dir=False,
                 prefix=False,
                 image_range=False,
                 wedge_range=False,
                 renumber_image=False,
                 nproc=False,
                 overwrite=False,
                 verbose=False,
                 #logger=False
                 ):
        """
        Run eiger2cbf on HDF5 dataset. Returns path of new CBF files.
        Not sure I need multiprocessing.Pool, but used as saftety.

        master_file -- master file of data to be converted to cbf
        output_dir -- output directory
        prefix -- new image prefix
        image_range -- image numbers to convert
        wedge_range -- separation in oscillation axis between 2 images
        nproc -- number of processors to use
        overwrite -- overwrite files already present
        returns header
        """

        #if logger:
        #    logger.debug("Utilities::convert_hdf5_cbf")

        self.master_file = master_file
        self.output_dir = output_dir
        self.prefix = prefix
        self.image_range = image_range.replace(':', '-').split(',')
        self.wedge_range = wedge_range
        self.renumber_image = renumber_image
        self.nproc = nproc
        self.overwrite = overwrite
        # Have to run conversion to get delta omega
        if self.wedge_range:
            # Save original overwrite setting
            self.user_overwrite = overwrite
            self.overwrite = True
        self.verbose = verbose
        #self.logger = logger

        # Clear out output images on init
        self.output_images = []

    def run(self):
        """Coordinates the running of the conversion process"""

        self.preprocess()
        self.process()

    def preprocess(self):
        """Set up the conversion"""

        # Only master file
        if not "master" in self.master_file:
            raise Exception("Convert needs to be passed a master file")

        # Check directory
        if not self.output_dir:
            self.output_dir = "cbf_files"

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Check prefix
        if not self.prefix:
            self.prefix = get_prefix(self.master_file)

        # Multiprocessing
        if not self.nproc:
            self.nproc = multiprocessing.cpu_count() - 1

        # Calculate total number of images in dataset
        self.total_nimages = self.get_number_of_images()

        # Check image range for string parsing
        self.check_image_range()

    def process(self):
        """Coordinates the conversion"""
        # Create list of expected files to be generated
        self.calculate_expected_files()

        # Check for already present files
        self.check_for_output_images()
        
        # Convert images
        for range_to_make in self.ranges_to_make:
            self.convert_images(start_image=range_to_make[0],
                                end_image=range_to_make[-1])

        # Add previously converted images to output
        for range_not_to_make in self.ranges_not_to_make:
            self.output_images.extend(self.make_image_list(range_not_to_make[0], range_not_to_make[-1]))
        
        # Rerun for second image if wedge_range was specified and single frame converted.
        if self.second_image_number and len(self.output_images) == 1:
            self.image_range = [str(self.second_image_number)]
            # Reset overwrite to whatever was input
            self.overwrite = self.user_overwrite
            # rerun process
            self.process()

    def convert_images(self, start_image, end_image):
        """Actually convert the images"""

        if self.verbose:
            print "Converting images %d - %d" % (start_image, end_image)

        # The base eiger2cbf command
        command0 = "eiger2cbf %s" % self.master_file

        # Single image in master file
        if start_image == end_image:
            # Renumber image in pair so root name is same for Labelit.
            if self.renumber_image:
                img = "%s_%06d.cbf" % (os.path.join(self.output_dir, self.prefix), self.renumber_image)
            else:
                img = "%s_%06d.cbf" % (os.path.join(self.output_dir, self.prefix), start_image)
            command = "%s %d %s" % (command0, start_image, img)
            # Save outout to determine delta omega to calculate second image number
            if self.wedge_range and len(self.output_images) == 0:
                self.second_image_number = self.calculate_second_image(command, start_image)
            else:
                run_process((command, self.verbose))

            self.output_images.append(img)

        else:
            # One processor
            if self.nproc == 1:
                command = "%s %d:%d %s_" % (command0, start_image, end_image, os.path.join(self.output_dir, self.prefix))
                run_process((command, self.verbose))

            # Multiple processors
            else:
                #if active:
                print "Employing multiple threads"

                # Construct commands to run in parallel
                number_of_images = end_image - start_image + 1
                commands = []
                iteration = 0

                # In case the command may have single image to convert, run this...
                if number_of_images < 2 * self.nproc:
                    while iteration < number_of_images:
                        img = "%s_%06d.cbf" % (os.path.join(self.output_dir, self.prefix), start_image)
                        commands.append(("%s %d %s" % (command0, start_image, img), self.verbose))
                        iteration += 1
                        start_image += 1

                # IF more than 1 image per processor
                else:
                    batch = int(number_of_images / self.nproc)
                    final_batch = batch + (number_of_images % self.nproc)

                    start = start_image
                    stop = 0
                    while iteration < self.nproc:
                        if iteration == (self.nproc - 1) :
                            batch = final_batch
                        stop = start + batch -1
                        commands.append(("%s %d:%d %s_" % (command0, start, stop, os.path.join(self.output_dir, self.prefix)), self.verbose))
                        iteration += 1
                        start = stop + 1

                # Run in pool
                pool = multiprocessing.Pool(processes=self.nproc)
                pool.map_async(run_process, commands)
                pool.close()
                pool.join()

            self.output_images.extend(self.make_image_list(start_image, end_image))
        self.output_images.sort()

    def make_image_list(self, start, end):
        """Passback list with image file names"""
        l = []
        if start == end:
            l.append("%s_%06d.cbf" % (os.path.join(self.output_dir, self.prefix), int(start)))
        else:
            for i in range(int(start), int(end)+1):
                l.append("%s_%06d.cbf" % (os.path.join(self.output_dir, self.prefix), i))
        return l

    def calculate_second_image(self, command, first_image_number):
        """Calculate second image number based on wedge_range"""
        # Run the first image and grab the results
        stdout, stderr = run_process((command, self.verbose), output=True)
        delta_omega = False
        for line in stderr.split("\n"):
            if line.count('omega_range_average'):
                delta_omega = float(line.split()[-2])
        if delta_omega:
            # Calculate second image number 
            second_image_number = int(round(first_image_number + float(self.wedge_range) / delta_omega))
            if first_image_number == second_image_number:
                return False
            elif second_image_number > self.total_nimages:
                return self.total_nimages
            else:
                return second_image_number
        else:
            return False

    def check_image_range(self):
        """Setup image_range if user specifies 'all' or 'end' in input"""
        # Set last image number for 'all'
        if self.image_range.count('all'):
            # if 1 image in dataset or wedge specified convert just 1 image
            if self.total_nimages == 1 or self.wedge_range:
                self.image_range = ['1']
            else:
                self.image_range = ['1-%d'%self.total_nimages]
        # Look for 'end' and replace with last image number
        else:
            for x in range(len(self.image_range)):
                if self.image_range[x].count('end'):
                    new = self.image_range[x].replace('end', str(self.total_nimages))
                    self.image_range.pop(x)
                    self.image_range.insert(x, new)

    def get_number_of_images(self):
        """Query the master file for the number of images in the data set"""
        stdout, stderr = run_process(("eiger2cbf %s" % self.master_file, self.verbose), output=True)
        #number_of_images = int(stdout.split("\n")[-2])
        number_of_images = int(stdout.split("\n")[-2])
        if self.verbose:
            print "Number of images: %d" % number_of_images
        return number_of_images

    def calculate_expected_files(self):
        """Take inputs and create a list of files to be made"""
        self.expected_images = []
        for n in self.image_range:
            # If it includes a range of images
            if n.count('-'):
                s = n.split('-')
                self.expected_images.extend(self.make_image_list(int(s[0]), int(s[1])))
            else:
                self.expected_images.extend(self.make_image_list(int(n), int(n)))

    def check_for_output_images(self):
        """Perform a check for output images that already exist"""
        self.ranges_to_make = []
        self.ranges_not_to_make = []
        images_expected = []
        images_exist = []

        # Compare expected to what is already there
        for image in self.expected_images:
            image_number = int(image.split(".")[-2].split("_")[-1])
            images_expected.append(image_number)
            if os.path.exists(image):
                images_exist.append(image_number)

        # print images_exist, self.start_image, self.end_image
        if self.overwrite:
            images_exist = []

        expected_set = set(images_expected)
        exists_set = set(images_exist)

        to_make_set = expected_set - exists_set
        to_make_list = list(to_make_set)
        to_make_list.sort()

        not_to_make_list = list(expected_set - to_make_set)
        not_to_make_list.sort()

        if len(to_make_set) == 0:

            if self.verbose:
                print "Requested files already present"

        elif len(to_make_set) > 0:

            for k, g in groupby(enumerate(to_make_list), lambda (i, x):i - x):
                self.ranges_to_make.append(map(itemgetter(1), g))

        if len(not_to_make_list) > 0:
            for k, g in groupby(enumerate(not_to_make_list), lambda (i, x):i - x):
                self.ranges_not_to_make.append(map(itemgetter(1), g))

def get_prefix(img_path):
    """Return the image prefix"""
    # get rif of '_master.h5' and any extra '.' which will screw up Labelit.
    return os.path.basename(img_path).replace("_master.h5", "").replace('.', '_')

def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    args = get_commandline()
    print args
    # Convert from NameSpace to Python dict
    input_args = vars(args)
    # Launch converter
    converter = hdf5_to_cbf_converter(**input_args)
    converter.run()

def get_commandline():
    """
    Grabs the commandline
    """

    # Parse the commandline arguments
    commandline_description = "Generate a generic RAPD file"
    parser = argparse.ArgumentParser(description=commandline_description)

    # Verbose
    parser.add_argument("-q", "--quiet",
                        action="store_false",
                        dest="verbose",
                        help="Verbose")

    # Overwrite
    parser.add_argument("--overwrite",
                        action="store_true",
                        dest="overwrite",
                        help="""Overwrite -- default to overwriting cbf files that already exist.
                        Default bahavior is to only convert files which do not already exist""")

    # Multiprocessing capabilities
    parser.add_argument("--nproc",
                        action="store",
                        dest="nproc",
                        type=int,
                        default=multiprocessing.cpu_count() - 1,
                        help="Number of processors to be used")

    # Image numbers to convert
    parser.add_argument("-n", "--image_range",
                        action="store",
                        dest="image_range",
                        default='all',
                        help="Comma separated list of images to be converted (ie. -n 1,90,95-100,105:110)")

    # used for calculation which second image to convert based on oscillation angle spacing
    parser.add_argument("-w", "--wedge_range",
                        action="store",
                        dest="wedge_range",
                        default=False,
                        type=float,
                        help="Determines the second image in a pair based on the oscillation angle wedge range between images")

    # Output directory
    parser.add_argument("-o", "--output_dir",
                        action="store",
                        dest="output_dir",
                        default=False,
                        help="Output directory for cbf files")

    # Output directory
    parser.add_argument("-p", "--prefix",
                        action="store",
                        dest="prefix",
                        default=False,
                        help="Prefix for cbf files (including run number)")

    # Input HDF5 master file
    parser.add_argument(action="store",
                        dest="master_file",
                        #nargs=1,
                        help="Name of input HDF5 master file")

    return parser.parse_args()

if __name__ == "__main__":

    # Get the commandline args
    commandline_args = get_commandline()

    # Execute code
    main(args=commandline_args)
