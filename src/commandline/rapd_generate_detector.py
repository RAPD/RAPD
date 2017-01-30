"""Generate a RAPD detector scaffold file"""

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

__created__ = "2017-1-19"
_maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
# import argparse
# import datetime
# import glob
# import logging
# import multiprocessing
# import os
# import pprint
# import pymongo
# import redis
# import shutil
# import subprocess
# import sys
# import time

# RAPD imports
from rapd_generate_basefile import CommandlineFileGenerator, split_text_blob
# import commandline_utils
# import import detectors.detector_utils as detector_utils
# import utils

class DetectorFileGenerator(CommandlineFileGenerator):
    """File generator for detector wrapper"""

    def run(self):
        """The main actions of the module"""

        self.preprocess()

        self.write_file_docstring()
        self.write_license()
        self.write_docstrings()
        self.write_imports(write_list=("json",
                                       "os",
                                       "re",
                                       "time"))
        self.write_commandline()
        self.write_main_func()
        self.write_main(main_lines=[
            "    if len(sys.argv) > 1:\n",
            "        test_image = sys.argv[1]\n",
            "    else:\n",
            "        raise Error(\"No test image input!\")\n"
            "        # test_image = \"\"\n"])

    #     """if len(sys.argv) > 1:
    #         test_image = sys.argv[1]
    #     else:
    #         test_image = "/Users/frankmurphy/workspace/rapd_github/src/test/sercat_id/t\
    # est_data/THAU10_r1_1.0001"""

def main():
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    file_generator = DetectorFileGenerator()
    file_generator.run()

if __name__ == "__main__":
    main()
