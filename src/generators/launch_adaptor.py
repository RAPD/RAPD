"""Generate a RAPD launch adaptor scaffold file"""

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
        self.create_adaptor()
        sys.exit()

    def preprocess(self):
        """Set up the plugin generation"""

        # Check to make sure that the directory we want to create does not exist
        if os.path.exists(self.args.adaptor_name):
            if self.args.force:
                shutil.rmtree(self.args.adaptor_name)
            else:
                raise Exception("%s already exists - use -f option to force overwrite. Exiting." %
                                self.args.adaptor_name)


    def create_adaptor(self):
        """Create the adaptor"""

        # Load the module
        module = importlib.import_module("generators.base")

        # Add the filename to the args
        self.args.file = self.args.adaptor_name

        # Instantiate the FileGenerator
        file_generator = module.FileGenerator(self.args)

        # Go through the steps of writing the file
        file_generator.preprocess()
        file_generator.write_file_docstring("%s RAPD plugin" % self.args.plugin_name)
        file_generator.write_license()
        file_generator.write_docstrings()
        self.p_write_tags(file_generator)
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
        # self.p_write_versions(file_generator)
        self.p_write_adaptor(file_generator)
        # self.t_write_get_commandline(file_generator)
        # self.cl_write_construct_command(file_generator)
        # self.cl_write_get_commandline(file_generator)
        # self.cl_write_print_welcome_message(file_generator)
        # self.cl_write_main(file_generator)
        # self.t_write_main(file_generator)

    def p_write_adaptor(self, file_generator):
        """Write the LauncherAdapter class"""

        plugin_lines = [
            "class LauncherAdapter(object):",
            "    \"\"\"",
            "    RAPD adapter for launcher process",
            "    \"\"\"\n",
            # "    # Holders for passed-in info",
            # "    command = None",
            # "    preferences = None\n",
            # "    # Holders for results"
            # "    results = {}\n",
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
            "        # Keep track of start time",
            "        self.start_time = time.time()",
            "        # Store tprint for use throughout",
            "        if tprint:",
            "            self.tprint = tprint",
            "        # Dead end if no tprint passed",
            "        else:",
            "            def func(arg=False, level=False, verbosity=False, color=False):",
            "                pass",
            "            self.tprint = func\n",
            "        # Some logging",
            "        self.logger.info(command)\n",
            "        # Store passed-in variables",
            "        self.command = command",
            "        self.preferences = self.command.get(\"preferences\", {})\n",
            "        # Set up the results with command and process data",
            "        self.results[\"command\"] = command\n",
            "        # Create a process section of results with the id and a starting status of 1",
            "        self.results[\"process\"] = {",
            "            \"process_id\": self.command.get(\"process_id\"),",
            "            \"status\": 1}\n",
            # "        self.reply_address = self.command[\"return_address\"]",
            "        multiprocessing.Process.__init__(self, name=\"%s\")" % self.args.plugin_name,
            "        self.start()\n",
            "    def run(self):",
            "        \"\"\"Execution path of the plugin\"\"\"\n",
            "        self.preprocess()",
            "        self.process()",
            "        self.postprocess()",
            "        self.print_credits()\n",
            "    def preprocess(self):",
            "        \"\"\"Set up for plugin action\"\"\"\n",
            "        self.tprint(arg=0, level=\"progress\")",
            "        self.tprint(\"preprocess\")\n",
            "        # Check for dependency problems",
            "        self.check_dependencies()\n",
            "    def process(self):",
            "        \"\"\"Run plugin action\"\"\"\n",
            "        self.tprint(\"process\")\n",
            "    def postprocess(self):",
            "        \"\"\"Events after plugin action\"\"\"\n",
            "        self.tprint(\"postprocess\")\n",
            "        self.tprint(arg=99, level=\"progress\")",
            "        # Clean up mess",
            "        self.clean_up()\n",
            "        # Send back results",
            "        self.handle_return()\n",
            "    def check_dependencies(self):",
            "        \"\"\"Make sure dependencies are all available\"\"\"\n",
            "        # A couple examples from index plugin",
            "        # Can avoid using best in the plugin b"
            "        # If no best, switch to mosflm for strategy",
            "        # if self.strategy == \"best\":",
            "        #     if not find_executable(\"best\"):",
            "        #         self.tprint(\"Executable for best is not present, using Mosflm for s\
trategy\",",
            "        #                     level=30,",
            "        #                     color=\"red\")",
            "        #         self.strategy = \"mosflm\"\n",
            "        # If no gnuplot turn off printing",
            "        # if self.preferences.get(\"show_plots\", True) and (not self.preferences.get(\
\"json\", False)):",
            "        #     if not find_executable(\"gnuplot\"):",
            "        #         self.tprint(\"\\nExecutable for gnuplot is not present, turning off p\
lotting\",",
            "        #                     level=30,",
            "        #                     color=\"red\")",
            "        #         self.preferences[\"show_plots\"] = False\n",
            "        # If no labelit.index, dead in the water",
            "        # if not find_executable(\"labelit.index\"):",
            "        #     self.tprint(\"Executable for labelit.index is not present, exiting\",",
            "        #                 level=30,",
            "        #                 color=\"red\")",
            "        #     self.results[\"process\"][\"status\"] = -1",
            "        #     self.results[\"error\"] = \"Executable for labelit.index is not present\
\"",
            "        #     self.write_json(self.results)",
            "        #     raise exceptions.MissingExecutableException(\"labelit.index\")\n",
            "        # If no raddose, should be OK",
            "        # if not find_executable(\"raddose\"):",
            "        #     self.tprint(\"\\nExecutable for raddose is not present - will continue\
\",",
            "        #                 level=30,",
            "        #                 color=\"red\")\n",
            "    def clean_up(self):",
            "        \"\"\"Clean up after plugin action\"\"\"\n",
            "        self.tprint(\"clean_up\")\n",
            "    def handle_return(self):",
            "        \"\"\"Output data to consumer - still under construction\"\"\"\n",
            "        self.tprint(\"handle_return\")\n",
            "        run_mode = self.command[\"preferences\"][\"run_mode\"]\n",
            "        # Handle JSON At least write to file"
            "        self.write_json()\n",
            "        # Print results to the terminal",
            "        if run_mode == \"interactive\":",
            "            self.print_results()",
            "        # Traditional mode as at the beamline",
            "        elif run_mode == \"server\":",
            "            pass",
            "        # Run and return results to launcher",
            "        elif run_mode == \"subprocess\":",
            "            return self.results",
            "        # A subprocess with terminal printing",
            "        elif run_mode == \"subprocess-interactive\":",
            "            self.print_results()",
            "            return self.results\n",
            "        def write_json(self):",
            "            \"\"\"Print out JSON-formatted result\"\"\"\n",
            "            json_string = json.dumps(self.results)\n",
            "            # Output to terminal?",
            "            if self.preferences.get(\"json\", False):",
            "                print json_string\n",
            "            # Always write a file",
            "            os.chdir(self.working_dir)",
            "            with open(\"result.json\", \"w\") as outfile:",
            "                outfile.writelines(json_string)",
            "    def print_credits(self):",
            "        \"\"\"Print credits for programs utilized by this plugin\"\"\"\n",
            "        self.tprint(\"print_credits\")\n",
            "        self.tprint(credits.HEADER, level=99, color=\"blue\")\n",
            "        programs = [\"CCTBX\"]",
            "        info_string = credits.get_credits_text(programs, \"    \")",
            "        self.tprint(info_string, level=99, color=\"white\")\n",
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
                        dest="adaptor_name",
                        nargs="?",
                        default="test_adaptor",
                        help="Name of adaptor to be generated")

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
