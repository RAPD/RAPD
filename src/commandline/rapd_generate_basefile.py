"""Generate a generic rapd file"""

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

__created__ = "2017-01-18"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
import os
import sys
import time

# RAPD imports
import commandline_utils

_NOW = time.localtime()
_LICENSE = """
This file is part of RAPD

Copyright (C) %d, Cornell University
All rights reserved.

RAPD is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3.

RAPD is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.""" % _NOW.tm_year


def split_text_blob(text):
    """Split a multiline text blob into a list"""

    lines = text.split("\n")
    for i in range(len(lines)):
        lines[i] += "\n"

    return lines

class BaseFileGenerator(object):

    def __init__(self, args=False):
        """Initialize the BaseFileGenerator instance"""

        self.args = args

        if args:
            if args.file:
                def write_function(lines):
                    """Function for writing strings to file"""
                    out_file = open(args.file, "a+")
                    for line in lines:
                        out_file.write(line)
                    out_file.close()

            else:
                def write_function(lines):
                    """Function for writing strings to file"""
                    for line in lines:
                        sys.stdout.write(line)
        else:

            self.args = type('args', (object,), {});
            self.args.file = False
            self.args.maintainer = "Your name"
            self.args.email = "Your email"

            def write_function(lines):
                """Function for writing strings to file"""
                for line in lines:
                    sys.stdout.write(line)

        self.output_function = write_function

    def preprocess(self):
        """Do pre-write checks"""

        # If we are writing a file, check
        if self.args.file:
            if os.path.exists(self.args.file):
                if self.args.force:
                    os.unlink(self.args.file)
                else:
                    raise Exception("%s already exists - exiting" % self.args.file)
        else:
            pass

    def run(self):
        """The main actions of the module"""

        self.preprocess()

        self.write_file_docstring()
        self.write_license()
        self.write_docstrings()
        self.write_imports()
        self.write_main_func()
        self.write_main()

    def write_file_docstring(self):
        """Write the docstring for file"""
        self.output_function(["\"\"\"This is a docstring for this file\"\"\"\n","\n"])

    def write_license(self):
        """Write the license"""
        self.output_function(["\"\"\"",] + split_text_blob(_LICENSE) + ["\"\"\"\n", "\n"])

    def write_docstrings(self):
        """Write file author docstrings"""
        self.output_function(["__created__ = \"%d-%d-%d\"\n" % (_NOW.tm_year, _NOW.tm_mon, _NOW.tm_mday),
                              "_maintainer__ = \"%s\"\n" % self.args.maintainer,
                              "__email__ = \"%s\"\n" % self.args.email,
                              "__status__ = \"Development\"\n\n"])

    def write_imports(self):
        """Write the import sections"""
        self.output_function(["# Standard imports\n",
                              "# import argparse\n",
                              "# import datetime\n",
                              "# import glob\n",
                              "# import logging\n",
                              "# import multiprocessing\n",
                              "# import os\n",
                              "# import pprint\n",
                              "# import pymongo\n",
                              "# import redis\n",
                              "# import shutil\n",
                              "# import subprocess\n",
                              "# import sys\n",
                              "# import time\n\n",
                              "# RAPD imports\n",
                              "# import commandline_utils\n",
                              "# import import detectors.detector_utils as detector_utils\n",
                              "# import utils\n\n"])

    def write_main_func(self):
        """Write the main function"""
        self.output_function(["def main():\n",
                              "    \"\"\"\n",
                              "    The main process docstring\n",
                              "    This function is called when this module is invoked from\n",
                              "    the commandline\n",
                              "    \"\"\"\n",
                              "    print \"main\"\n\n"])

    def write_main(self):
        """Write the main function"""
        self.output_function(["if __name__ == \"__main__\":\n",
                              "    main()\n"])



def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """Generate a generic RAPD file"""
    parser = argparse.ArgumentParser(parents=[commandline_utils.gf_parser],
                                     description=commandline_description)

    return parser.parse_args()

def main():

    # Get the commandline args
    commandline_args = get_commandline()

    print commandline_args

    filename = False #"foo.py"

    file_generator = BaseFileGenerator(commandline_args)
    print file_generator
    file_generator.run()

if __name__ == "__main__":

    print "rapd_generate_rapd_file.py"

    main()
