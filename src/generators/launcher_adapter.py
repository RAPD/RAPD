"""Generate a RAPD launch adapter scaffold file"""

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
import importlib
# import logging
# import multiprocessing
import os
# import pprint
# import pymongo
# import redis
import shutil
# import subprocess
import sys
# import time
import uuid

# RAPD imports
import info
from base import FileGenerator as CommandlineFileGenerator
from base import split_text_blob
# import commandline_utils
# import import detectors.detector_utils as detector_utils
# import utils

class FileGenerator(CommandlineFileGenerator):
    """File generator for plugin wrapper"""

    def run(self):
        """The main actions of the module"""

        self.preprocess()
        self.create_adapter()
        sys.exit()

    def preprocess(self):
        """Set up the plugin generation"""

        # Check to make sure that the directory we want to create does not exist
        if os.path.exists(self.args.adapter_name):
            if self.args.force:
                shutil.rmtree(self.args.adapter_name)
            else:
                raise Exception("%s already exists - use -f option to force overwrite. Exiting." %
                                self.args.adapter_name)


    def create_adapter(self):
        """Create the adapter"""

        # Load the module
        module = importlib.import_module("generators.base")

        # Add the filename to the args
        self.args.file = self.args.adapter_name

        # Instantiate the FileGenerator
        file_generator = module.FileGenerator(self.args)

        # Go through the steps of writing the file
        file_generator.preprocess()
        file_generator.write_file_docstring("%s RAPD launcher adapter" % self.args.adapter_name)
        file_generator.write_license()
        file_generator.write_docstrings()
        file_generator.write_imports(
            write_list=("json",
                        "logging",
                        "os",
                        "pprint import pprint",
                        "shutil",
                        "subprocess",
                        "sys",
                        "time",
                        "uuid"),
            added_normal_imports=(("from distutils.spawn import find_executable",)),
            added_rapd_imports=(("from utils import exceptions",
                                 "import utils.launch_tools as launch_tools"))
            )
        self.p_write_adapter(file_generator)

    def p_write_adapter(self, file_generator):
        """Write the LauncherAdapter class"""

        plugin_lines = [
            "class LauncherAdapter(object):",
            "    \"\"\"",
            "    RAPD adapter for launcher process",
            "    \"\"\"\n",
            "    def __init__(self, site, message, settings):",
            "        \"\"\"",
            "        Initialize the plugin\n",
            "        Keyword arguments",
            "        site -- imported site definition module",
            "        message -- command from the control process, encoded as JSON",
            "        settings --",
            "        \"\"\"\n",
            "        # Get the logger Instance",
            "        self.logger = logging.getLogger(\"RAPDLogger\")",
            "        self.logger.debug(\"__init__\")\n",
            "        # Store passed-in variables",
            "        self.site = site",
            "        self.message = message",
            "        self.settings = settings\n",
            "        # Decode message",
            "        self.decoded_message = json.loads(self.message)\n",
            "        self.run()\n",
            "    def run(self):",
            "        \"\"\"Orchestrate the adapter's actions\"\"\"\n",
            "        self.preprocess()",
            "        self.process()",
            "        self.postprocess()\n",
            "    def preprocess(self):",
            "        \"\"\"Adjust the command passed in in install-specific ways\"\"\"\n",
            "        pass\n",
            "    def process(self):",
            "        \"\"\"The main action of the adapter\"\"\"\n",
            "        pass\n",
            "    def postprocess(self):",
            "        \"\"\"Clean up after adapter functions\"\"\"\n",
            "        pass\n",
        ]
        file_generator.output_function(plugin_lines)

    def t_write_get_commandline(self, file_generator):
        """Write the get_commandline function of the test.py"""

        description = "Test %s plugin" % self.args.plugin_name

        get_commandline_func_lines = [
            "def get_commandline():",
            "    \"\"\"Grabs the commandline\"\"\"\n",
            "    print \"get_commandline\"\n",
            "    # Parse the commandline arguments",
            "    commandline_description = \"%s\"" % description,
            "    my_parser = argparse.ArgumentParser(description=commandline_description)\n",
            "    # A True/False flag",
            "    my_parser.add_argument(\"-q\", \"--quiet\",",
            "                           action=\"store_false\",",
            "                           dest=\"verbose\",",
            "                           help=\"Reduce output\")\n",
            "    args = my_parser.parse_args()\n",
            "    # Insert logic to check or modify args here\n",
            "    return args\n",
        ]
        file_generator.output_function(get_commandline_func_lines)

    def t_write_tests(self, file_generator):
        """Write the test functions of the test.py"""

        test_func_lines = [
            "class TestDependencies(unittest.TestCase):",
            "    \"\"\"Example test fixture WITHOUT setUp and tearDown\"\"\"\n",
            "    def test_gnuplot(self):",
            "        \"\"\"Make sure the gnuplot executable is present\"\"\"\n",
            "        test = find_executable(\"gnuplot\")",
            "        self.assertNotEqual(test, None)\n",
            "    def test_gnuplot_version(self):",
            "        \"\"\"Make sure the gnuplot executable is an acceptable version\"\"\"\n",
            "        subproc = subprocess.Popen([\"gnuplot\", \"--version\"],",
            "                                   stdout=subprocess.PIPE,",
            "                                   stderr=subprocess.PIPE)",
            "        subproc.wait()",
            "        stdout, _ = subproc.communicate()",
            "        found = False",
            "        for version in plugin.VERSIONS[\"gnuplot\"]:",
            "            if version in stdout:",
            "                found = True",
            "                break\n",
            "        assert found == True\n",
            "def get_dependencies_tests():",
            "    \"\"\"Return a suite with dependencies tests\"\"\"\n",
            "    return unittest.TestLoader().loadTestsFromTestCase(TestDependencies)\n",
            "def get_all_tests():",
            "    \"\"\"Return a suite with all tests\"\"\"\n",
            "    return unittest.TestLoader().loadTestsFromTestCase(TestDependencies)\n",
            "def compare_results(result1, result2, tprint):",
            "    \"\"\"Result comparison logic for unit testing\"\"\"\n",
            "    # A little example",
            "    tprint(\"    DISTL\", 10, \"white\")",
            "    assert result1[\"results\"][\"distl_results\"][\"good Bragg spots\"] == \ ",
            "           result2[\"results\"][\"distl_results\"][\"good Bragg spots\"] \n",
            "    return True\n",
        ]
        file_generator.output_function(test_func_lines)

    def t_write_main(self, file_generator):
        """Write the main function of the test.py"""

        main_func_lines = [
            "def main(args):",
            "    \"\"\"",
            "    The main process docstring",
            "    This function is called when this module is invoked from",
            "    the commandline",
            "    \"\"\"\n",
            "    if args.verbose:",
            "        verbosity = 2",
            "    else:",
            "        verbosity = 1\n",
            "    unittest.main(verbosity=verbosity)\n",
            "    if __name__ == \"__main__\":\n",
            "        main()\n",
        ]
        file_generator.output_function(main_func_lines)

    @classmethod
    def write_file(cls, fname, lines):
        """Write lines into a file fname"""

        with open(fname, "a") as the_file:
            for line in lines:
                the_file.write(line)

def get_commandline(args=None):
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
    parser.add_argument("-t", "--test",
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
    parser.add_argument(action="store",
                        dest="adapter_name",
                        nargs="?",
                        default="test_adapter",
                        help="Name of adapter to be generated")

    # Pull from the input list
    if isinstance(args, list):
        my_args = parser.parse_args(args)
    # Grab straight from the commandline
    else:
        my_args = parser.parse_args()

    return my_args

def main():
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    commandline_args = get_commandline()

    # print commandline_args

    file_generator = FileGenerator(commandline_args)
    file_generator.run()

if __name__ == "__main__":
    main()
