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

class hdf5_to_cbf_converter(object):

    def __init__(self,
                 master_file,
                 output_dir=False,
                 prefix=False,
                 start_image=False,
                 end_image=False,
                 zfill=5,
                 nproc=False,
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

    def run(self):
        """Coordinates the running of the coonversion process"""

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

        # Check end_image - default to start_image
        # if not self.end_image:
        #     self.end_image = self.start_image

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
                                    stderr=subprocess.STDOUT)
        stdout, stderr = myoutput.communicate()
        # for i in stdout.split("\n"): print i
        # print stderr
        number_of_images = int(stdout.split("\n")[-2])
        print "Number of images: %d" % number_of_images

        # Work out end image
        if not self.end_image:
            self.end_image = number_of_images + self.start_image - 1
        print "Converting images %d - %d" % (self.start_image, self.end_image)

        # Check that the number of images encompasses the end_image

        # Single image
        if number_of_images == 1:
            img = "%s%s.cbf" % (os.path.join(self.output_dir, self.prefix), str(self.start_image).zfill(self.zfill))
            command = "%s 1 %s" % (command0, img)
            print "Executing command `%s`" % command
            # Now convert
            myoutput = subprocess.Popen(command,
                                        shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)
            stdout, stderr = myoutput.communicate()

        # Single image from a run of images
        elif self.start_image == self.end_image:
            command = "%s %d:%d %s" % (command0, self.start_image, end, os.path.join(self.output_dir, self.prefix))

            # Now convert
            myoutput = subprocess.Popen(command,
                                        shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)
            stdout, stderr = myoutput.communicate()

        # Multiple images from a run of images
        else:
            # One processor
            if self.nproc == 1:
                command = "%s %d:%d %s" % (command0, self.start_image, end, os.path.join(self.output_dir, self.prefix))

                # Now convert
                myoutput = subprocess.Popen(command,
                                            shell=True,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT)
                stdout, stderr = myoutput.communicate()

            # Multiple processors
            else:

                print "Employing multiple threads"

                # Create function for running
                def run_process(command):
                    """Run the command in a subprocess.Popen call"""
                    print command
                    myoutput = subprocess.Popen(command,
                                                shell=True,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.STDOUT)
                    myoutput.wait()
                    stdout, stderr = myoutput.communicate()
                    for i in stdout.split("\n"): print i
                    print stderr
                    return (stdout, stderr)

                # Create a pool to speed things along
                pool = multiprocessing.Pool(processes=self.nproc)

                batch = int(number_of_images / self.nproc)
                iter = 1
                start = self.start_image
                stop = 0
                results = []
                while number_of_images > stop:
                    stop = start + batch -1
                    if (stop + batch) > self.end_image:
                        stop = self.end_image
                    print iter, start, stop
                    command = "%s %d:%d %s" % (command0, start, stop, os.path.join(self.output_dir, self.prefix))
                    print command
                    results.append(pool.apply_async(run_process, (command,)))
                    iter += 1
                    start = stop + 1

                # Done with the pool
                pool.close()
                pool.join()

        return True

        # if BLspec.checkCluster():
        #     # Half the number of nodes in the queue.
        #     split = int(round(number_of_images/8))
        #     cluster = True
        # else:
        #     # Least amount of splitting without running out of memory.
        #     split = 360
        #     cluster = False
        # st = 1
        # end = split
        # stop = False

        # while 1:
        #     if cluster:
        #         # No self required
        #         pool.apply_async(BLspec.processCluster_NEW, ((command,os.path.join(out,'eiger2cbf.log')),))
        #     else:
        #         pool.apply_async(processLocal, ((command,os.path.join(out,'eiger2cbf.log')),))
        #     time.sleep(0.1)
        #     if stop:
        #         break
        #     st += split
        #     end += split
        #     # Check to see if next round will be out of range
        #     if st >= number_of_images:
        #         break
        #     if st + split >= number_of_images:
        #         end = number_of_images
        #         stop = True
        #     if end > number_of_images:
        #         end = number_of_images
        # pool.close()
        # pool.join()

        # # Get the detector description from the h5 file
        # with open('eiger2cbf.log','r') as f:
        #     for line in f:
        #         if line.count('description'):
        #             det = line[line.find('=')+2:].strip()
        #             break
        #
        # # Read header from first image and pass it back.
        # header = readHeader(img)
        #
        # # change the detector
        # header['detector'] = det
        # return(header)




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
                                      nproc=args.nproc)
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
                        help="First (or only) image to be converted")

    # Last image number
    parser.add_argument("-m", "-e", "--end_image",
                        action="store",
                        dest="end_image",
                        default=False,
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
