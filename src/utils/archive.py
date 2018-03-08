"""This is a docstring for this container file"""

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

__created__ = "2017-09-21"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
# import argparse
from collections import OrderedDict
# import datetime
import glob
import hashlib
# import json
# import logging
# import multiprocessing
import os
from pprint import pprint
# import pymongo
# import re
# import redis
# import shutil
# import subprocess
# import sys
import tarfile
# import time
# import unittest

# RAPD imports
# import commandline_utils
# import detectors.detector_utils as detector_utils
# import utils

def compress_dir(target):
    """Compress a target and return the result file name"""

    print "compress_dir target:", target

    # Save where we were
    start_dir = os.getcwd()

    # Move to target directory
    os.chdir(os.path.dirname(target))

    # Shorten the target from abspath
    my_target = os.path.basename(target)

    archive_name = "%s.tar.bz2" % my_target

    with tarfile.open(archive_name, "w:bz2") as tar:
        tar.add(my_target)

    # Move bach to starting work directory
    os.chdir(start_dir)

    return os.path.abspath(archive_name)

def compress_file(target):
    """
    Compresses an individual file with an accompanying hash value
    """
    # print "compress_file", target

    target = os.path.abspath(target)

    # Save where we were
    start_dir = os.getcwd()
    # print "start_dir", start_dir

    # Move to target directory
    os.chdir(os.path.dirname(target))
    # print os.getcwd()

    # Shorten the target from abspath
    my_target = os.path.basename(target)
    # print my_target

    # Get hash of target file
    my_hash = get_hash(my_target)

    archive_name = os.path.abspath("%s.tar.bz2" % my_target)
    # print archive_name

    with tarfile.open(archive_name, "w:bz2") as tar:
        tar.add(my_target)

    # Move bach to starting work directory
    os.chdir(start_dir)

    return (archive_name, my_hash)

def create_archive(directory, archive_name=False):
    """
    Creates an archive file for the input directory
    """
    # print "create_archive"
    # print "  directory: %s" % directory
    # print "  archive_name: %s" % archive_name
    cwd = os.getcwd()

    if not os.path.isdir(directory):
        return False

    # Move to directory that contains directory to be archived
    parent_dir = os.path.dirname(directory)
    # print "  parent_dir:", parent_dir
    os.chdir(parent_dir)

    # Create a manifest and put it in the archive directory
    records = create_manifest(directory, True)

    # Compress the archive
    archive_name = compress_dir(directory)

    # Get a hash value for the archive
    archive_hash = get_hash(archive_name)

    return_dict = {
        "path": archive_name,
        "hash": archive_hash
    }

    # Return to the original directory
    if not cwd == directory:
        os.chdir(cwd)

    return return_dict

def create_manifest(directory, write=True):
    """
    Creates a manifest for all files in a directory
    If write is True, will write files.sha in the dirctory
    """
    # Storage for results of hash
    records = OrderedDict()

    # Retrieve files in the directory and sort alphabetically
    globfiles = glob.glob(directory + "/*")
    globfiles.sort()

    # Run through files
    for globfile in globfiles:
        trunc_file = globfile.replace(directory+"/", "")
        # It's a file
        if os.path.isfile(globfile):
            # Compute hash
            file_hash = hashlib.sha1(open(globfile, "r").read()).hexdigest()
            # Store hash
            records[trunc_file] = file_hash

    if write:
        with open(directory + "/files.sha", "w") as output_file:
            for key, val in records.iteritems():
                output_file.write("%s  %s\n" % (val, key))

    # Return the dict
    return records

def get_hash(filename):
    """Returns a hash for a file"""
    return hashlib.sha1(open(filename, "r").read()).hexdigest()


if __name__ == "__main__":
    create_manifest("./", True)
