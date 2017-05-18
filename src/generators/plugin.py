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
        self.create_directory()
        self.create_init()
        self.create_readme()
        self.create_info()
        self.create_commandline()
        self.create_plugin()
        self.create_test()
        self.create_ui()
        sys.exit()

    def preprocess(self):
        """Set up the plugin generation"""

        # Check to make sure that the directory we want to create does not exist
        if os.path.exists(self.args.plugin_name):
            if self.args.force:
                shutil.rmtree(self.args.plugin_name)
            else:
                raise Exception("%s already exists - use -f option to force overwrite. Exiting." %
                                self.args.plugin_name)

    def create_directory(self):
        """Create the plugin directory and move to it"""

        os.mkdir(self.args.plugin_name)
        os.chdir(self.args.plugin_name)

    def create_init(self):
        """Create the __init__.py"""

        with open("__init__.py", "a"):
            os.utime("__init__.py", None)

    def create_readme(self):
        """Create the README.md"""

        self.write_file("README.md", info.README_TEXT)

    def create_info(self):
        """Create the info.py"""

        # Load the module
        module = importlib.import_module("generators.container")

        # Add the filename to the args
        self.args.file = "info.py"

        # Instantiate the FileGenerator
        file_generator = module.FileGenerator(self.args)

        # Run
        file_generator.run()

    def create_commandline(self):
        """Create the commandline.py"""

        # Load the module
        module = importlib.import_module("generators.base")

        # Add the filename to the args
        self.args.file = "commandline.py"

        # Instantiate the FileGenerator
        file_generator = module.FileGenerator(self.args)

        # Go through the steps of writing the file
        file_generator.preprocess()
        file_generator.write_file_docstring("Wrapper for launching %s" % self.args.plugin_name)
        file_generator.write_license()
        file_generator.write_docstrings()
        file_generator.write_imports(write_list=("argparse",
                                                 "importlib",
                                                 "os",
                                                 "sys",
                                                 "uuid"),
                                     added_rapd_imports=(
                                         "utils.credits as credits",
                                         "utils.global_vars as rglobals",
                                         "utils.log",
                                         "utils.modules as modules",
                                         "utils.text as text",
                                         "utils.commandline_utils as commandline_utils",
                                         "detectors.detector_utils as detector_utils")
                                    )
        self.cl_write_construct_command(file_generator)
        self.cl_write_get_commandline(file_generator)
        self.cl_write_print_welcome_message(file_generator)
        self.cl_write_main(file_generator)
        file_generator.write_main()

    def create_plugin(self):
        """Create the plugin.py"""

        # Load the module
        module = importlib.import_module("generators.base")

        # Add the filename to the args
        self.args.file = "plugin.py"

        # Instantiate the FileGenerator
        file_generator = module.FileGenerator(self.args)

        # Go through the steps of writing the file
        file_generator.preprocess()
        file_generator.write_file_docstring("%s RAPD plugin" % self.args.plugin_name)
        file_generator.write_license()
        file_generator.write_docstrings()
        self.p_write_tags(file_generator)
        file_generator.write_imports(write_list=("collections import OrderedDict",
                                                 "glob",
                                                 "json",
                                                 "logging",
                                                 "multiprocessing",
                                                 "os",
                                                 "pprint import pprint",
                                                 "shutil",
                                                 "subprocess",
                                                 "sys",
                                                 "time",
                                                 "uuid"),
                                     added_rapd_imports=(("info",))
                                    )
        self.p_write_versions(file_generator)
        self.p_write_plugin(file_generator)
        self.t_write_get_commandline(file_generator)
        # self.cl_write_construct_command(file_generator)
        # self.cl_write_get_commandline(file_generator)
        # self.cl_write_print_welcome_message(file_generator)
        # self.cl_write_main(file_generator)
        self.t_write_main(file_generator)

    def create_test(self):
        """Create the test.py"""

        # Load the module
        module = importlib.import_module("generators.base")

        # Add the filename to the args
        self.args.file = "test.py"

        # Instantiate the FileGenerator
        file_generator = module.FileGenerator(self.args)

        # Go through the steps of writing the file
        file_generator.preprocess()
        file_generator.write_file_docstring("Test code for %s RAPD plugin" % self.args.plugin_name)
        file_generator.write_license()
        file_generator.write_docstrings()
        file_generator.write_imports(write_list=("argparse",
                                                 "subprocess",
                                                 "sys",
                                                 "time",
                                                 "unittest"),
                                     added_normal_imports=(
                                         ("from distutils.spawn import find_executable",)),
                                     added_rapd_imports=(("plugin",))
                                    )
        # self.p_write_plugin(file_generator)
        # self.cl_write_construct_command(file_generator)
        # self.cl_write_get_commandline(file_generator)
        # self.cl_write_print_welcome_message(file_generator)
        self.t_write_tests(file_generator)
        self.t_write_main(file_generator)

    def create_ui(self):
        """Coordinate the creation of the UI"""

        os.mkdir("ui")

    def cl_write_construct_command(self, file_generator):
        """Write the construct command function of the commandline.py"""

        construct_command_func_lines = [
            "def construct_command(commandline_args):",
            "    \"\"\"Put together the command for the plugin\"\"\"\n",
            "    # The task to be carried out",
            "    command = {",
            "        \"command\": \"%s\"," % self.args.plugin_name.upper(),
            "        \"process_id\": uuid.uuid1().get_hex(),",
            "        \"status\": 0,",
            "        }\n",
            "    # Work directory",
            "    work_dir = commandline_utils.check_work_dir(",
            "        os.path.join(os.path.abspath(os.path.curdir), run_repr),",
            "        active=True,",
            "        up=commandline_args.dir_up)\n",
            "    command[\"directories\"] = {",
            "        \"work\": work_dir",
            "        }\n",
            "    # Check the work directory",
            "    commandline_utils.check_work_dir(command[\"directories\"][\"work\"], True)\n",
            "    # Information on input",
            "    command[\"input_data\"] = {",
            "        \"datafile\": os.path.abspath(commandline_args.datafile)",
            "    }\n",
            "    # Plugin settings",
            "    command[\"preferences\"] = {",
            "        \"json\": commandline_args.json,",
            "        \"nproc\": commandline_args.nproc,",
            "        \"test\": commandline_args.test,",
            "    }\n",
            "    return command\n",
        ]
        file_generator.output_function(construct_command_func_lines)

    def cl_write_get_commandline(self, file_generator):
        """Write the get_commandline function of the commandline.py"""

        description = "Launch %s plugin" % self.args.plugin_name

        get_commandline_func_lines = [
            "def get_commandline():",
            "    \"\"\"Grabs the commandline\"\"\"\n",
            "    print \"get_commandline\"\n",
            "    # Parse the commandline arguments",
            "    commandline_description = \"%s\"" % description,
            "    my_parser = argparse.ArgumentParser(description=commandline_description)\n",
            "    # Run in test mode",
            "    my_parser.add_argument(\"-t\", \"--test\",",
            "                           action=\"store_true\",",
            "                           dest=\"test\",",
            "                           help=\"Run in test mode\")\n",
            "    # Verbose/Quiet are a pair of opposites",
            "    # Recommend defaulting to verbose during development and to",
            "    # quiet during production",
            "    # Verbose",
            "    #my_parser.add_argument(\"-v\", \"--verbose\",",
            "    #                       action=\"store_true\",",
            "    #                       dest=\"verbose\",",
            "    #                       help=\"More output\")\n",
            "    # Quiet",
            "    my_parser.add_argument(\"-q\", \"--quiet\",",
            "                           action=\"store_false\",",
            "                           dest=\"verbose\",",
            "                           help=\"More output\")\n",
            "    # Messy/Clean are a pair of opposites.",
            "    # Recommend defaulting to messy during development and to",
            "    # clean during production",
            "    # Messy",
            "    #my_parser.add_argument(\"--messy\",",
            "    #                       action=\"store_false\",",
            "    #                       dest=\"clean\",",
            "    #                       help=\"Keep intermediate files\")\n",
            "    # Clean",
            "    my_parser.add_argument(\"--clean\",",
            "                           action=\"store_true\",",
            "                           dest=\"clean\",",
            "                           help=\"Clean up intermediate files\")\n",
            "    # Color",
            "    #my_parser.add_argument(\"--color\",",
            "    #                       action=\"store_false\",",
            "    #                       dest=\"no_color\",",
            "    #                       help=\"Color the terminal output\")\n",
            "    # No color",
            "    my_parser.add_argument(\"--nocolor\",",
            "                           action=\"store_true\",",
            "                           dest=\"no_color\",",
            "                           help=\"Do not color the terminal output\")\n",
            "    # JSON Output",
            "    my_parser.add_argument(\"-j\", \"--json\",",
            "                           action=\"store_true\",",
            "                           dest=\"json\",",
            "                           help=\"Output JSON format string\")\n",
            "    # Output progress",
            "    my_parser.add_argument(\"--progress\",",
            "                           action=\"store_true\",",
            "                           dest=\"progress\",",
            "                           help=\"Output progess to terminal\")\n",
            "    # Multiprocessing",
            "    my_parser.add_argument(\"--nproc\",",
            "                           dest=\"nproc\",",
            "                           type=int,",
            "                           default=1,",
            "                           help=\"Number of processors to employ\")\n",
            "    # Positional argument",
            "    my_parser.add_argument(action=\"store\",",
            "                           dest=\"datafile\",",
            "                           nargs=\"?\",",
            "                           default=False,",
            "                           help=\"Name of file to be analyzed\")\n",
            "    # Print help message if no arguments",
            "    if len(sys.argv[1:]) == 0:",
            "        my_parser.print_help()",
            "        my_parser.exit()\n",
            "    args = my_parser.parse_args()\n",
            "    # Insert logic to check or modify args here\n",
            "    return args\n",
        ]
        file_generator.output_function(get_commandline_func_lines)

    def cl_write_print_welcome_message(self, file_generator):
        """Write the print_welcome_message function of commandline.py"""

        print_welcome_func_lines = [
            "def print_welcome_message(printer):",
            "    \"\"\"Print a welcome message to the terminal\"\"\"",
            "    message = \"\"\"",
            "------------",
            "RAPD Example",
            "------------\"\"\"\n"
            "    printer(message, 50, color=\"blue\")\n",
        ]
        file_generator.output_function(print_welcome_func_lines)

    def cl_write_main(self, file_generator):
        """Write the print_welcome_message function of commandline.py"""

        main_func_lines = [
            "def main():",
            "    \"\"\"",
            "    The main process",
            "    Setup logging and instantiate the model\"\"\"\n",
            "    # Get the commandline args",
            "    commandline_args = get_commandline()\n",
            "    # Output log file is always verbose",
            "    log_level = 10\n",
            "    # Set up logging",
            # "    if commandline_args.logging:",
            "    logger = utils.log.get_logger(logfile_dir=\"./\",",
            "                                  logfile_id=\"rapd_%s\"," % self.args.plugin_name,
            "                                  level=log_level,",
            "                                  console=commandline_args.test)\n",
            "    # Set up terminal printer",
            "    # tprint prints to the terminal, taking the arguments",
            "    #     arg - the string to be printed (if using level of \"progress\" this needs to\
 be an int)",
            "    #     level - value 0 to 99 or \"progress\". Do NOT use a value of 100 or above",
            "    #             50 - alert",
            "    #             40 - error",
            "    #             30 - warning",
            "    #             20 - info",
            "    #             10 - debug",
            "    #     color - color to print (\"red\" and so forth. See list in utils/text)",
            "    #     newline - put in False if you don't want a newline at the end of your print",
            "    #     ",
            "    # Verbosity",
            "    if commandline_args.verbose:",
            "        terminal_log_level = 10",
            "    elif commandline_args.json:",
            "        terminal_log_level = 100",
            "    else:",
            "        terminal_log_level = 50\n",
            "    tprint = utils.log.get_terminal_printer(verbosity=terminal_log_level,",
            "                                            no_color=commandline_args.no_color,",
            "                                            progress=commandline_args.progress)\n",
            "    print_welcome_message(tprint)\n",
            "    logger.debug(\"Commandline arguments:\")",
            "    tprint(arg=\"\\nCommandline arguments:\", level=10, color=\"blue\")",
            "    for pair in commandline_args._get_kwargs():",
            "        logger.debug(\"  arg:%s  val:%s\", pair[0], pair[1])",
            "        tprint(arg=\"  arg:%-20s  val:%s\" % (pair[0], pair[1]), level=10, \
            color=\"white\")\n",
            "    # Get the environmental variables",
            "    environmental_vars = utils.site.get_environmental_variables()",
            "    logger.debug(\"\" + text.info + \"Environmental variables\" + text.stop)",
            "    tprint(\"\\nEnvironmental variables\", level=10, color=\"blue\")",
            "    for key, val in environmental_vars.iteritems():",
            "        logger.debug(\"  \" + key + \" : \" + val)",
            "        tprint(arg=\"  arg:%-20s  val:%s\" % (key, val), level=10, color=\"white\")\n",
            "    # Should working directory go up or down?",
            "    if environmental_vars.get(\"RAPD_DIR_INCREMENT\") == \"up\":",
            "        commandline_args.dir_up = True",
            "    else:",
            "        commandline_args.dir_up = False\n",
            "    # Construct the command",
            "    command = construct_command(commandline_args=commandline_args,",
            "                                logger=logger)\n",
            "    # Load the plugin",
            "    plugin = modules.load_module(seek_module=\"plugin\",",
            "                                 directories=[\"plugins.%s\"]," % \
            self.args.plugin_name,
            "                                 logger=logger)\n",
            "    # Print plugin info",
            "    tprint(arg=\"\\nPlugin information\", level=10, color=\"blue\")",
            "    tprint(arg=\"  Plugin type:    %s\" % plugin.PLUGIN_TYPE, level=10, \
            color=\"white\")",
            "    tprint(arg=\"  Plugin subtype: %s\" % plugin.PLUGIN_SUBTYPE, level=10, \
            color=\"white\")",
            "    tprint(arg=\"  Plugin version: %s\" % plugin.VERSION, level=10, color=\"white\")",
            "    tprint(arg=\"  Plugin id:      %s\" % plugin.ID, level=10, color=\"white\")\n",
            "    # Run the plugin",
            "    plugin.RapdPlugin(command, tprint, logger)\n",
        ]
        file_generator.output_function(main_func_lines)

    def p_write_tags(self, file_generator):
        """Write RAPD informations tags for the plugin.py"""

        tags_lines = [
            "# This is an active RAPD plugin",
            "RAPD_PLUGIN = True\n",
            "# This plugin's type",
            "PLUGIN_TYPE = \"%s\"" % self.args.plugin_name.upper(),
            "PLUGIN_SUBTYPE = \"EXPERIMENTAL\"\n",
            "# A unique UUID for this handler (uuid.uuid1().hex)",
            "ID = \"%s\"" % uuid.uuid1().hex,
            "VERSION = \"1.0.0\"\n"
        ]
        file_generator.output_function(tags_lines)

    def p_write_versions(self, file_generator):
        """Write the versions information function of the plugin.py"""

        versions_lines = [
            "# Software dependencies",
            "VERSIONS = {",
            "    \"gnuplot\": (",
            "        \"gnuplot 4.2\",",
            "        \"gnuplot 5.0\",",
            "    )",
            "}\n"
        ]
        file_generator.output_function(versions_lines)

    def p_write_plugin(self, file_generator):
        """Write the RapdPlugin class"""

        plugin_lines = [
            "class RapdPlugin(multiprocessing.Process):",
            "    \"\"\"",
            "    RAPD plugin class\n",
            "    Command format:",
            "    {",
            "       \"command\":\"%s\"," % self.args.plugin_name,
            "       \"directories\":",
            "           {",
            "               \"work\": \"\"                          # Where to perform the work",
            "           },",
            "       \"site_parameters\": {}                       # Site data",
            "       \"preferences\": {}                           # Settings for calculations",
            "       \"return_address\":(\"127.0.0.1\", 50000)       # Location of control process",
            "    }",
            "    \"\"\"\n",
            "    results = {}\n",
            "    def __init__(self, command, tprint=False, logger=False):",
            "        \"\"\"Initialize the plugin\"\"\"\n",
            "        # If the logging instance is passed in...",
            "        if logger:",
            "            self.logger = logger",
            "        else:",
            "            # Otherwise get the logger Instance",
            "            self.logger = logging.getLogger(\"RAPDLogger\")",
            "            self.logger.debug(\"__init__\")\n",
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
            "    def clean_up(self):",
            "        \"\"\"Clean up after plugin action\"\"\"\n",
            "        self.tprint(\"clean_up\")\n",
            "    def handle_return(self):",
            "        \"\"\"Output data to consumer - still under construction\"\"\"\n",
            "        self.tprint(\"handle_return\")\n",
            "        run_mode = self.command[\"preferences\"][\"run_mode\"]\n",
            "        # Print results to the terminal",
            "        if run_mode == \"interactive\":",
            "            self.print_results()",
            "        # Prints JSON of results to the terminal",
            "        elif run_mode == \"json\":",
            "            self.print_json()",
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
                        dest="plugin_name",
                        nargs="?",
                        default="test_plugin",
                        help="Name of plugin to be generated")

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
