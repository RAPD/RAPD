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
import argparse
# import datetime
# import glob
# import logging
# import multiprocessing
import os
# import pprint
# import pymongo
# import redis
# import shutil
# import subprocess
import sys
# import time

# RAPD imports
from rapd_generate_basefile import CommandlineFileGenerator, split_text_blob
# import commandline_utils
# import import detectors.detector_utils as detector_utils
# import utils

class TestFileGenerator(CommandlineFileGenerator):
    """File generator for detector wrapper"""

    def __init__(self, args=False):
        """Initialize the TestFileGenerator"""

        # Store args
        self.args = args

    def run(self):
        """The main actions of the module"""

        self.preprocess()

        self.write_file_docstring()
        self.write_license()
        self.write_docstrings()
        self.write_imports()
        self.write_example_test()
        self.write_commandline(description="Parse image file header")
        self.write_main_func()
        self.write_main()

    def preprocess(self):
        """Prepare for action"""

        # Output file name
        if self.args:
            if not self.args.file:
                # Determine output file name from target
                if self.args.target:
                    print self.args.target
                    full_path = os.path.abspath(self.args.target).split("/")
                    print full_path
                    self.args.file = "test_" + "_".join(full_path[full_path.index("src")+1:])

        # Run the inherited version
        super(TestFileGenerator, self).preprocess()

    def write_imports(self):
        """Manage the import statements"""

        # The file to be tested
        if self.args.target:
            full_path = os.path.abspath(self.args.target).split("/")
            import_path = ".".join(full_path[full_path.index("src")+1:])[:-3]
            import_name = full_path[-1][:-3]
            self.args.import_name = import_name
            import_statement = import_path + " as " + import_name
            # Run the inherited version
            super(TestFileGenerator, self).write_imports(
                write_list=("argparse", "unittest"),
                added_rapd_imports=((import_statement,)))
        else:
            # Run the inherited version
            super(TestFileGenerator, self).write_imports(
                write_list=("argparse", "subprocess", "sys", "unittest"))

    def write_example_test(self):
        """Write some example tests"""

        test_lines = [
            "class TestDependencies(unittest.TestCase):",
            "    \"\"\"Example test fixture WITHOUT setUp and tearDown\"\"\"",
            "",
            "   def test_executable(self):",
            "        \"\"\"Make sure the eiger2cbf executable is present\"\"\"",
            "",
            "        p = subprocess.Popen([\"eiger2cbf\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)",
            "        stdout, stderr = p.communicate()",
            "        assert stderr.startswith(\"EIGER HDF5 to CBF converter\")",
            "        assert stdout.startswith(\"Usage:\")",
            "",
            "    def test_version(self):",
            "        \"\"\"Make sure the eiger2cbf executable is an acceptable version\"\"\"",
            "",
            "        p = subprocess.Popen([\"eiger2cbf\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)",
            "        stdout, stderr = p.communicate()",
            "",
            "        found = False",
            "        for version in convert_hdf5_cbf.VERSIONS[\"eiger2cbf\"]:",
            "            if version in stderr:",
            "                found = True",
            "                break",
            "",
            "        assert found == True",
            "class ExampleTestCase(unittest.TestCase):",
            "    \"\"\"Example test fixture with setUp and tearDown\"\"\"\n",
            "    def setUp(self):",
            "        \"\"\"Set up the test fixture\"\"\"\n",
            "        self.widget = Widget('The widget')",
            "",
            "    def tearDown(self):",
            "        \"\"\"Tear down the test fixture\"\"\"\n",
            "        self.widget.dispose()",
            "        self.widget = None",
            "",
            "    def test_default_size(self):",
            "        self.assertEqual(self.widget.size(), (50,50),",
            "                         'incorrect default size')",
            "",
            "    def test_resize(self):",
            "        self.widget.resize(100,150)",
            "        self.assertEqual(self.widget.size(), (100,150),",
            "                         'wrong size after resize')",
            "",
            "class ExampleTestCaseLight(unittest.TestCase):",
            "    \"\"\"Example test fixture WITHOUT setUp and tearDown\"\"\"\n",
            "    def test_default_size(self):",
            "        self.assertEqual(self.widget.size(), (50,50),",
            "                         'incorrect default size')",
            "",
            "    def test_resize(self):",
            "        self.widget.resize(100,150)",
            "        self.assertEqual(self.widget.size(), (100,150),",
            "                         'wrong size after resize')",
            "",
        ]

        self.output_function(test_lines)

    def write_commandline(self, description=False):
        """Write commanling handling into the file"""

        if not description:
            description = "Generate a generic RAPD file"

        commandline_lines = [
            "def get_commandline():",
            "    \"\"\"",
            "    Grabs the commandline",
            "    \"\"\"\n",
            "    print \"get_commandline\"\n",
            "    # Parse the commandline arguments",
            "    commandline_description = \"%s\"" % description,
            "    parser = argparse.ArgumentParser(description=commandline_description)\n",
            "    # Verbosity",
            "    parser.add_argument(\"-v\", \"--verbose\",",
            "                        action=\"store_true\",",
            "                        dest=\"verbose\",",
            "                        help=\"Enable verbose output\")\n",
            "    # A True/False flag",
            "    # parser.add_argument(\"-c\", \"--commandline\",",
            "    #                     action=\"store_true\",",
            "    #                     dest=\"commandline\",",
            "    #                     help=\"Generate commandline argument parsing\")\n",
            "    # File name to be generated",
            "    # parser.add_argument(action=\"store\",",
            "    #                     dest=\"file\",",
            "    #                     nargs=\"?\",",
            "    #                     default=False,",
            "    #                     help=\"Name of file to be generated\")\n",
            "    # Print help message is no arguments",
            "    # if len(sys.argv[1:])==0:",
            "    #     parser.print_help()",
            "    #     parser.exit()\n",
            "    return parser.parse_args()\n",
            ]

        self.output_function(commandline_lines)

    def write_main_func(self, main_func_lines=False):
        """Write the main function"""

        main_func_lines = [
            "def main(args):",
            "    \"\"\"",
            "    The main process docstring",
            "    This function is called when this module is invoked from",
            "    the commandline",
            "    \"\"\"\n",
            "    print \"main\"\n",
            "    unittest.main()\n"]

        super(TestFileGenerator, self).write_main_func(main_func_lines=main_func_lines)



def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """Generate a RAPD detector file scaffold"""

    parser = argparse.ArgumentParser(description=commandline_description)

    # Verbosity
    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        dest="verbose",
                        help="Enable verbose feedback")

    # Test mode?
    parser.add_argument("--test",
                        action="store_true",
                        dest="test",
                        help="Run in test mode")

    # Test mode?
    parser.add_argument("-f", "--force",
                        action="store_true",
                        dest="force",
                        help="Allow overwriting of files")

    # Maintainer
    parser.add_argument("-m", "--maintainer",
                        action="store",
                        dest="maintainer",
                        default="Your name",
                        help="Maintainer's name")

    # Maintainer's email
    parser.add_argument("-e", "--email",
                        action="store",
                        dest="email",
                        default="Your email",
                        help="Maintainer's email")

    # File name to be generated
    parser.add_argument("-t", "--target",
                        action="store",
                        dest="target",
                        default=False,
                        help="File to be tested")

    # File to be generated
    parser.add_argument(action="store",
                        dest="file",
                        nargs="?",
                        default=False,
                        help="Name of file to be generated")

    return parser.parse_args()

def main():
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    # Get the commandline args
    commandline_args = get_commandline()

    print commandline_args

    file_generator = TestFileGenerator(commandline_args)
    file_generator.run()

if __name__ == "__main__":
    main()
