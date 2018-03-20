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
# import time

# RAPD imports


VERSIONS = {
    "eiger2cbf": ("160415",)
}

# Create function for running
def run_process(input_args):
    """Run the command in a subprocess.Popen call"""

    command, verbose = input_args

    if verbose:
        print command
        result =  subprocess.Popen(command,
                                   shell=True)
    else:
        result =  subprocess.Popen(command,
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
    result.wait()
    return result

class hdf5_to_cbf_converter(object):

    expected_images = []
    output_images = []
    ranges_to_make = []
    ranges_not_to_make = []

    def __init__(self,
                 master_file,
                 output_dir=False,
                 prefix=False,
                 start_image=False,
                 end_image=False,
                 zfill=6,
                 nproc=False,
                 overwrite=False,
                 batch_mode=False,
                 verbose=False,
                 logger=False):
        """
        Run eiger2cbf on HDF5 dataset. Returns path of new CBF files.
        Not sure I need multiprocessing.Pool, but used as saftety.

        master_file -- master file of data to be converted to cbf
        output_dir -- output directory
        prefix -- new image prefix
        start_image -- first image number
        end_image -- final image number
        zfill -- number digits for snap image numbers
        nproc -- number of processors to use
        overwrite -- overwrite files already present
        batch_mode -- run non-interactively
        returns header
        """

        if logger:
            logger.debug("Utilities::convert_hdf5_cbf")

        self.master_file = master_file
        self.output_dir = output_dir
        self.prefix = prefix
        self.start_image = start_image
        self.end_image = end_image
        self.zfill = zfill
        self.nproc = nproc
        self.overwrite = overwrite
        self.batch_mode = batch_mode
        self.verbose = verbose
        self.logger = logger

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
            #self.prefix = self.master_file.replace("master.h5", "").rstrip("_")
            #self.prefix = os.path.basename(self.master_file)[:os.path.basename(self.master_file).find('.')]
            if self.master_file.count('.') > 1:
                self.prefix = os.path.basename(self.master_file).replace("_master.h5", "").replace('.', '_')
            else:
                self.prefix = os.path.basename(self.master_file).replace("_master.h5", "")

        # Check start_image - default to 1
        if not self.start_image:
            self.start_image = 1

        # Multiprocessing
        if not self.nproc:
            self.nproc = multiprocessing.cpu_count()

        # Grab the number of images
        self.number_of_images = self.get_number_of_images()

        # Work out end image
        if not self.end_image:
            self.end_image = self.number_of_images + self.start_image - 1

        # Create list of expected files to be generated
        self.calculate_expected_files()

        # Check for already present files
        self.check_for_output_images()

    def process(self):
        """Coordinates the conversion"""

        if self.overwrite == True:

            self.convert_images(start_image=self.start_image, end_image=self.end_image)

        else:

            if len(self.ranges_to_make) == 0:
                # print "No images to make"
                self.convert_images(start_image=self.start_image,
                                    end_image=self.end_image,
                                    active=False)
                return True

            else:
                for range_to_make in self.ranges_to_make:
                    self.convert_images(start_image=range_to_make[0],
                                        end_image=range_to_make[-1])

                for range_not_to_make in self.ranges_not_to_make:
                    self.convert_images(start_image=range_not_to_make[0],
                                        end_image=range_not_to_make[-1],
                                        active=False)

    def convert_images(self, start_image, end_image, active=True):
        """Actually convert the images"""

        if self.verbose:
            print "Converting images %d - %d" % (start_image, end_image)

        # The base eiger2cbf command
        command0 = "eiger2cbf %s" % self.master_file

        # Single image in master file
        if self.number_of_images == 1:
            img = "%s_%s.cbf" % (os.path.join(self.output_dir, self.prefix), str(start_image).zfill(self.zfill))
            command = "%s 1 %s" % (command0, img)

            # Now convert
            if active:
                if self.verbose:
                    print "Executing command `%s`" % command
                    myoutput = subprocess.Popen(command,
                                                shell=True)
                else:
                    myoutput = subprocess.Popen(command,
                                                shell=True,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
                myoutput.wait()

            self.output_images.append(img)

        # Single image from a run of images
        elif start_image == end_image:
            img = "%s_%s.cbf" % (os.path.join(self.output_dir, self.prefix), str(start_image).zfill(self.zfill))
            command = "%s %d:%d %s" % (command0,
                                       start_image,
                                       start_image,
                                       img)

            # Now convert
            if active:
                if self.verbose:
                    print "Executing command `%s`" % command
                    myoutput = subprocess.Popen(command,
                                                shell=True)
                else:
                    myoutput = subprocess.Popen(command,
                                                shell=True,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
                myoutput.wait()

            self.output_images.append(img)

        # Multiple images from a run of images
        else:
            # One processor
            if self.nproc == 1:
                command = "%s %d:%d %s_" % (command0, start_image, end_image, os.path.join(self.output_dir, self.prefix))

                # Now convert
                if active:
                    if self.verbose:
                        print "Executing command `%s`" % command
                        myoutput = subprocess.Popen(command,
                                                    shell=True)
                    else:
                        myoutput = subprocess.Popen(command,
                                                    shell=True,
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE)
                    myoutput.wait()

                for i in range(start_image, end_image+1):
                    self.output_images.append(os.path.join(self.output_dir, self.prefix) + "_%06d.cbf" % i)


            # Multiple processors
            else:
                if active:
                    print "Employing multiple threads"

                    # Construct commands to run in parallel
                    number_of_images = self.end_image - start_image + 1
                    batch = int(number_of_images / self.nproc)
                    final_batch = batch + (number_of_images % self.nproc)

                    iteration = 0
                    start = start_image
                    stop = 0
                    commands = []
                    while iteration < self.nproc:

                        if iteration == (self.nproc - 1):
                            batch = final_batch

                        stop = start + batch -1
                        commands.append(("%s %d:%d %s_" % (command0, start, stop, os.path.join(self.output_dir, self.prefix)), self.verbose))

                        iteration += 1
                        start = stop + 1

                    # Run in pool
                    pool = multiprocessing.Pool(processes=self.nproc)
                    results = pool.map_async(run_process, commands)
                    pool.close()
                    pool.join()

            for i in range(start_image, end_image+1):
                self.output_images.append(os.path.join(self.output_dir, self.prefix) + "_%06d.cbf" % i)

        self.output_images.sort()

    def get_number_of_images(self):
        """Query the master file for the number of images in the data set"""

        # Check how many frames are in dataset
        myoutput = subprocess.Popen(["eiger2cbf %s" % self.master_file],
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        stdout, stderr = myoutput.communicate()
        number_of_images = int(stdout.split("\n")[-2])
        if self.verbose:
            print "Number of images: %d" % number_of_images

        return number_of_images

    def calculate_expected_files(self):
        """Take inputs and create a list of files to be made"""

        if self.number_of_images == 1:
            self.expected_images.append("%s_%s.cbf" % (os.path.join(self.output_dir, self.prefix), str(self.start_image).zfill(self.zfill)))

        elif self.start_image == self.end_image:
            self.expected_images.append("%s_%s.cbf" % (os.path.join(self.output_dir, self.prefix), str(self.start_image).zfill(self.zfill)))

        else:
            for i in range(self.start_image, self.end_image+1):
                self.expected_images.append(os.path.join(self.output_dir, self.prefix) + "_%06d.cbf" % i)

    def check_for_output_images(self):
        """Perform a check for output images that already exist"""

        images_expected = []
        images_exist = []

        # Compare expected to what is already there
        for image in self.expected_images:
            image_number = int(image.split(".")[-2].split("_")[-1])
            images_expected.append(image_number)
            if os.path.exists(image):
                images_exist.append(image_number)

        # print images_exist, self.start_image, self.end_image

        expected_set = set(images_expected)
        exists_set = set(images_exist)

        to_make_set = expected_set - exists_set
        to_make_list = list(to_make_set)
        to_make_list.sort()

        not_to_make_list = list(expected_set - to_make_set)
        not_to_make_list.sort()

        # print expected_set, exists_set
        # print expected_set - exists_set

        if len(to_make_set) == 0:

            if self.verbose:
                print "Requested files already present"

        elif len(to_make_set) > 0:

            for k, g in groupby(enumerate(to_make_list), lambda (i, x):i - x):
                self.ranges_to_make.append(map(itemgetter(1), g))

        if len(not_to_make_list) > 0:
            for k, g in groupby(enumerate(not_to_make_list), lambda (i, x):i - x):
                self.ranges_not_to_make.append(map(itemgetter(1), g))

def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    args = get_commandline()
    print args

    converter = hdf5_to_cbf_converter(master_file=args.master_file[0],
                                      output_dir=args.output_dir,
                                      prefix=args.prefix,
                                      start_image=args.start_image,
                                      end_image=args.end_image,
                                      nproc=args.nproc,
                                      overwrite=args.overwrite,
                                      verbose=args.verbose)
    converter.preprocess()
    converter.process()

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

    # Batch mode (i.e. non-interactive)
    parser.add_argument("-b", "--batch",
                        action="store_true",
                        dest="batch",
                        help="Batch mode - i.e. not interactive")

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

    # Starting image number
    parser.add_argument("-n", "-s", "--start_image",
                        action="store",
                        dest="start_image",
                        default=1,
                        type=int,
                        help="First (or only) image to be converted")

    # Last image number
    parser.add_argument("-m", "-e", "--end_image",
                        action="store",
                        dest="end_image",
                        default=False,
                        type=int,
                        help="Final image to be converted.")

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
                        nargs=1,
                        help="Name of input HDF5 master file")

    return parser.parse_args()

if __name__ == "__main__":

    # Get the commandline args
    commandline_args = get_commandline()
    print os.getcwd()

    # Execute code
    main(args=commandline_args)
