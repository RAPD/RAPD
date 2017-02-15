"""HDF5 utilities for RAPD"""

"""
This file is part of RAPD

Copyright (C) 2017, Cornell University
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
import multiprocessing
import os
import subprocess
import sys
import time

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

    output_images = []

    def __init__(self,
                 master_file,
                 output_dir=False,
                 prefix=False,
                 start_image=False,
                 end_image=False,
                 zfill=5,
                 nproc=False,
                 verbose=False,
                 logger=False):
        """
        Run eiger2cbf on HDF5 dataset. Returns path of new CBF files.
        Not sure I need multiprocessing.Pool, but used as saftety.

        master_file - master file of data to be converted to cbf
        output_dir is output directory
        prefix is new image prefix
        imgn is the image number for the output frame.
        zfill is the number digits for snap image numbers
        returns header
        """

        # from rapd_pilatus import pilatus_read_header as readHeader

        if logger:
            logger.debug("Utilities::convert_hdf5_cbf")

        self.master_file = master_file
        self.output_dir = output_dir
        self.prefix = prefix
        self.start_image = start_image
        self.end_image = end_image
        self.zfill = zfill
        self.nproc = nproc
        self.verbose = verbose
        self.logger = logger

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
            self.prefix = self.master_file.replace("master.h5", "")

        # Check start_image - default to 1
        if not self.start_image:
            self.start_image = 1

        # Multiprocessing
        if not self.nproc:
            self.nproc = multiprocessing.cpu_count()

    def process(self):
        """Perform the conversion"""

        # The base eiger2cbf command
        command0 = "eiger2cbf %s" % self.master_file

        # Check how many frames are in dataset
        myoutput = subprocess.Popen([command0, self.master_file],
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        stdout, stderr = myoutput.communicate()
        number_of_images = int(stdout.split("\n")[-2])
        print "Number of images: %d" % number_of_images

        # Work out end image
        if not self.end_image:
            self.end_image = number_of_images + self.start_image - 1
        print "Converting images %d - %d" % (self.start_image, self.end_image)

        # Single image in master file
        if number_of_images == 1:
            img = "%s_%s.cbf" % (os.path.join(self.output_dir, self.prefix), str(self.start_image).zfill(self.zfill))
            command = "%s 1 %s" % (command0, img)

            # Now convert
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
        elif self.start_image == self.end_image:
            img = "%s_%s.cbf" % (os.path.join(self.output_dir, self.prefix), str(self.start_image).zfill(self.zfill))
            command = "%s %d:%d %s" % (command0,
                                       self.start_image,
                                       self.start_image,
                                       img)

            # Now convert
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
                command = "%s %d:%d %s" % (command0, self.start_image, self.end_image, os.path.join(self.output_dir, self.prefix))

                # Now convert
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

                for i in range(self.start_image, self.end_image+1):
                    self.output_images.append(os.path.join(self.output_dir, self.prefix) + "_%05d" % i)


            # Multiple processors
            else:

                print "Employing multiple threads"

                # Construct commands to run in parallel
                number_of_images = self.end_image - self.start_image + 1
                batch = int(number_of_images / self.nproc)
                final_batch = batch + (number_of_images % self.nproc)
                print "batch: %d" % batch
                print "final_batch %d" % final_batch
                iteration = 0
                start = self.start_image
                stop = 0
                commands = []
                while iteration < self.nproc:

                    if iteration == (self.nproc - 1):
                        batch = final_batch

                    stop = start + batch -1
                    commands.append(("%s %d:%d %s" % (command0, start, stop, os.path.join(self.output_dir, self.prefix)), self.verbose))

                    iteration += 1
                    start = stop + 1

                # Run in pool
                pool = multiprocessing.Pool(processes=self.nproc)
                results = pool.map_async(run_process, commands)
                pool.close()
                pool.join()

            for i in range(self.start_image, self.end_image+1):
                self.output_images.append(os.path.join(self.output_dir, self.prefix) + "_%05d.cbf" % i)

        return True

def main(args):
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    args = get_commandline()

    converter = hdf5_to_cbf_converter(master_file=args.master_file[0],
                                      output_dir=args.output_dir,
                                      prefix=args.prefix,
                                      start_image=args.start_image,
                                      end_image=args.end_image,
                                      nproc=args.nproc,
                                      verbose=args.verbose)
    converter.run()

def get_commandline():
    """
    Grabs the commandline
    """

    # Parse the commandline arguments
    commandline_description = "Generate a generic RAPD file"
    parser = argparse.ArgumentParser(description=commandline_description)

    # Verbose
    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        dest="verbose",
                        help="Verbose")

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

    # Execute code
    main(args=commandline_args)
