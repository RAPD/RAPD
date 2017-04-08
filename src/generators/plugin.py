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
            "def construct_command(image_headers, commandline_args, detector_module, logger):",
            "    \"\"\"Put together the command for the plugin\"\"\"\n",
            "    # The task to be carried out",
            "    command = {",
            "        \"command\": \"INDEX\",",
            "        \"process_id\": uuid.uuid1().get_hex(),",
            "        }\n",
            "    # Working directory",
            "    # image_numbers = []",
            "    # image_template = """,
            "    # for _, header in image_headers.iteritems():",
            "    #     image_numbers.append(str(header[\"image_number\"]))",
            "    #     image_template = header[\"image_template\"]",
            "    # image_numbers.sort()",
            "    # run_repr = \"rapd_index_\" + image_template.replace(detector_module.DETECTOR_SUFFIX, \"\").replace(\"?\", \"\")",
            "    # run_repr += \"+\".join(image_numbers)\n",
            "    command[\"directories\"] = {",
            "        \"work\": os.path.join(os.path.abspath(os.path.curdir), \"%s\")# run_repr)" % self.args.plugin_name,
            "        }\n",
            "    # Handle work directory",
            "    commandline_utils.check_work_dir(command[\"directories\"][\"work\"], True)\n",
            "    # Image data",
            "    images = image_headers.keys()",
            "    images.sort()",
            "    counter = 0",
            "    for image in images:",
            "        counter += 1",
            "        command[\"header%d\" % counter] = image_headers[image]",
            "    if counter == 1:",
            "        command[\"header2\"] = None\n",
            "    # Plugin settings",
            "    command[\"preferences\"] = {}\n",
            "    # JSON output?",
            "    command[\"preferences\"][\"json_output\"] = commandline_args.json\n",
            "    # Show plots",
            "    command[\"preferences\"][\"show_plots\"] = commandline_args.plotting\n",
            #     "# Strategy type",
            # "    command["preferences"]["strategy_type"] = commandline_args.strategy_type",
            # "",
            #     "# Best",
            # "    command["preferences"]["best_complexity"] = commandline_args.best_complexity",
            # "    command["preferences"]["shape"] = "2.0"",
            # "    command["preferences"]["susceptibility"] = "1.0"",
            # "    command["preferences"]["aimed_res"] = 0.0",
            # "",
            #     "# Best & Labelit",
            # "    command["preferences"]["sample_type"] = commandline_args.sample_type",
            # "    command["preferences"]["spacegroup"] = commandline_args.spacegroup",
            # "",
            #     "# Labelit",
            # "    command["preferences"]["a"] = 0.0",
            # "    command["preferences"]["b"] = 0.0",
            # "    command["preferences"]["c"] = 0.0",
            # "    command["preferences"]["alpha"] = 0.0",
            # "    command["preferences"]["beta"] = 0.0",
            # "    command["preferences"]["gamma"] = 0.0",
            # "    command["preferences"]["index_hi_res"] = str(commandline_args.hires)",
            # "    command["preferences"]["x_beam"] = commandline_args.beamcenter[0]",
            # "    command["preferences"]["y_beam"] = commandline_args.beamcenter[1]",
            # "    command["preferences"]["beam_search"] = commandline_args.beam_search",
            # "",
            #     "# Mosflm",
            # "    command["preferences"]["mosflm_rot"] = float(commandline_args.mosflm_range)",
            # "    command["preferences"]["mosflm_seg"] = int(commandline_args.mosflm_segments)",
            # "    command["preferences"]["mosflm_start"] = float(commandline_args.mosflm_start)",
            # "    command["preferences"]["mosflm_end"] = float(commandline_args.mosflm_end)",
            # "    command["preferences"]["reference_data"] = None",
            # "    command["preferences"]["reference_data_id"] = None",
            # "    # Change these if user wants to continue dataset with other crystal(s).",
            # "    # "reference_data_id": None, #MOSFLM",
            # "    # #"reference_data_id": 1,#MOSFLM",
            # "    # #"reference_data": [['/gpfs6/users/necat/Jon/RAPD_test/index09.mat', 0.0, 30.0, 'junk_1_1-30',",
            # "    #                      'P41212']],#MOSFLM",
            # "    # 'reference_data': [['/gpfs6/users/necat/Jon/RAPD_test/Output/junk/5/index12.mat',",
            # "    #                     0.0,",
            # "    #                     20.0,",
            # "    #                     'junk',",
            # "    #                     'P3'],",
            # "    #                    ['/gpfs6/users/necat/Jon/RAPD_test/Output/junk/5/index12.mat',",
            # "    #                     40.0,",
            # "    #                     50.0,",
            # "    #                     'junk2',",
            # "    #                     'P3']",
            # "    #                   ],#MOSFLM",
            # "",
            #     "# Raddose",
            # "    command["preferences"]["crystal_size_x"] = "100"",
            # "    command["preferences"]["crystal_size_y"] = "100"",
            # "    command["preferences"]["crystal_size_z"] = "100"",
            # "    command["preferences"]["solvent_content"] = 0.55",
            # "",
            #     "# Unknown",
            # "    command["preferences"]["beam_flip"] = False",
            # "    command["preferences"]["multiprocessing"] = False",
            # "",
            #     "# Site parameters",
            # "    command["preferences"]["site_parameters"] = {}",
            # "    command["preferences"]["site_parameters"]["DETECTOR_DISTANCE_MAX"] = \",
            # "        commandline_args.site_det_dist_max",
            # "    command["preferences"]["site_parameters"]["DETECTOR_DISTANCE_MIN"] = \",
            # "        commandline_args.site_det_dist_min",
            # "    command["preferences"]["site_parameters"]["DIFFRACTOMETER_OSC_MIN"] = \",
            # "        commandline_args.site_osc_min",
            # "    command["preferences"]["site_parameters"]["DETECTOR_TIME_MIN"] = \",
            # "        commandline_args.site_det_time_min",
            # "",
            #     "# Return address",
            # "    command["return_address"] = None",
            # "",
            "    logger.debug(\"Command for index plugin: %s\", command)\n",
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
            "    # Test mode  -  a true/false flag",
            "    my_parser.add_argument(\"-t\", \"--test\",",
            "                           action=\"store_true\",",
            "                           dest=\"test\",",
            "                           help=\"Run in test mode\")\n",
            "    # Quiet  -  a true/false flag",
            "    my_parser.add_argument(\"-q\", \"--quiet\",",
            "                           action=\"store_false\",",
            "                           dest=\"verbose\",",
            "                           help=\"Reduce output\")\n",
            "    # Color  -  a true/false flag",
            "    my_parser.add_argument(\"-c\", \"--color\",",
            "                           action=\"store_false\",",
            "                           dest=\"no_color\",",
            "                           help=\"Colorize terminal output\")\n",
            "    # Positional argument",
            "    my_parser.add_argument(action=\"store\",",
            "                           dest=\"file\",",
            "                           nargs=\"?\",",
            "                           default=False,",
            "                           help=\"Name of file to be generated\")\n",
            "    # Print help message if no arguments",
            "    if len(sys.argv[1:])==0:",
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
            "    if commandline_args.logging:",
            "        logger = utils.log.get_logger(logfile_dir=\"./\",",
            "                                      logfile_id=\"rapd_index\",",
            "                                      level=log_level,",
            "                                      console=commandline_args.test)\n",
            "    # Set up terminal printer",
            "    # Verbosity",
            "    if commandline_args.verbose:",
            "        terminal_log_level = 30",
            "    elif commandline_args.json:",
            "        terminal_log_level = 100",
            "    else:",
            "        terminal_log_level = 50\n",
            "    tprint = utils.log.get_terminal_printer(verbosity=terminal_log_level,",
            "                                            no_color=commandline_args.no_color)\n",
            "    print_welcome_message(tprint)\n",
            "    logger.debug(\"Commandline arguments:\")",
            "    tprint(arg=\"\\nCommandline arguments:\", level=10, color=\"blue\")",
            "    for pair in commandline_args._get_kwargs():",
            "        logger.debug(\"  arg:%s  val:%s\", pair[0], pair[1])",
            "        tprint(arg=\"  arg:%-20s  val:%s\" % (pair[0], pair[1]), level=10, color=\"white\")\n",
            "    # Get the environmental variables",
            "    environmental_vars = utils.site.get_environmental_variables()",
            "    logger.debug(\"\" + text.info + \"Environmental variables\" + text.stop)",
            "    tprint(\"\\nEnvironmental variables\", level=10, color=\"blue\")",
            "    for key, val in environmental_vars.iteritems():",
            "        logger.debug(\"  \" + key + \" : \" + val)",
            "        tprint(arg=\"  arg:%-20s  val:%s\" % (key, val), level=10, color=\"white\")\n",
            "    # List sites?",
            "    if commandline_args.listsites:",
            "        tprint(arg=\"\\nAvailable sites\", level=99, color=\"blue\")",
            "        commandline_utils.print_sites(left_buffer=\"  \")",
            "        if not commandline_args.listdetectors:",
            "            sys.exit()\n",
            "    # List detectors?",
            "    if commandline_args.listdetectors:",
            "        tprint(arg=\"Available detectors\", level=99, color=\"blue\")",
            "        commandline_utils.print_detectors(left_buffer=\"  \")",
            "        sys.exit()\n",
            "    # Get the data files",
            "    data_files = commandline_utils.analyze_data_sources(sources=commandline_args.sources,",
            "                                                        mode=\"index\")\n",
            "    if \"hdf5_files\" in data_files:",
            "        logger.debug(\"HDF5 source file(s)\")",
            "        tprint(arg=\"\\nHDF5 source file(s)\", level=99, color=\"blue\")",
            "        logger.debug(data_files[\"hdf5_files\"])",
            "        for data_file in data_files[\"hdf5_files\"]:",
            "            tprint(arg=\"  \" + data_file, level=99, color=\"white\")",
            "        logger.debug(\"CBF file(s) from HDF5 file(s)\")",
            "        tprint(arg=\"\\nData files\", level=99, color=\"blue\")",
            "    else:",
            "        logger.debug(\"Data file(s)\")",
            "        tprint(arg=\"\\nData file(s)\", level=99, color=\"blue\")\n",
            "    if len(data_files) == 0:",
            "        tprint(arg=\"  None\", level=99, color=\"white\")",
            "    else:",
            "        logger.debug(data_files[\"files\"])",
            "        for data_file in data_files[\"files\"]:",
            "            tprint(arg=\"  \" + data_file, level=99, color=\"white\")\n",
            "    # Need data",
            "    if len(data_files) == 0 and commandline_args.test == False:",
            "        if logger:",
            "            logger.exception(\"No files input for indexing.\")",
            "        raise Exception, \"No files input for indexing.\"\n",
            "    # Too much data?",
            "    if len(data_files) > 2:",
            "        if logger:",
            "            logger.exception(\"Too many files for indexing. 1 or 2 images accepted\")",
            "        raise Exception, \"Too many files for indexing. 1 or 2 images accepted\"\n",
            "    # Get site - commandline wins over the environmental variable",
            "    site = False",
            "    site_module = False",
            "    detector = {}",
            "    detector_module = False",
            "    if commandline_args.site:",
            "        site = commandline_args.site",
            "    elif environmental_vars.has_key(\"RAPD_SITE\"):",
            "        site = environmental_vars[\"RAPD_SITE\"]\n",
            "    # Detector is defined by the user",
            "    if commandline_args.detector:",
            "        detector = commandline_args.detector",
            "        detector_module = detector_utils.load_detector(detector)\n",
            "    # If no site or detector, try to figure out the detector",
            "    if not (site or detector):",
            "        detector = detector_utils.get_detector_file(data_files[\"files\"][0])",
            "        if isinstance(detector, dict):",
            "            if detector.has_key(\"site\"):",
            "                site_target = detector.get(\"site\")",
            "                site_file = utils.site.determine_site(site_arg=site_target)",
            "                # print site_file",
            "                site_module = importlib.import_module(site_file)",
            "                detector_target = site_module.DETECTOR.lower()",
            "                detector_module = detector_utils.load_detector(detector_target)",
            "            elif detector.has_key(\"detector\"):",
            "                site_module = False",
            "                detector_target = detector.get(\"detector\")",
            "                detector_module = detector_utils.load_detector(detector_target)\n",
            "    # Have a detector - read in file data",
            "    if detector_module:",
            "        image_headers = {}",
            "        for data_file in data_files[\"files\"]:",
            "            if site_module:",
            "                image_headers[data_file] = detector_module.read_header(data_file,",
            "                                                                       site_module.BEAM_SETTINGS)",
            "            else:",
            "                image_headers[data_file] = detector_module.read_header(data_file)\n",
            "        logger.debug(\"Image headers: %s\", image_headers)",
            "        print_headers(tprint, image_headers)\n",
            "        command = construct_command(image_headers=image_headers,",
            "                                    commandline_args=commandline_args,",
            "                                    detector_module=detector_module,",
            "                                    logger=logger)",
            "    else:",
            "        if logger:",
            "            logger.exception(\"No detector module found\")",
            "        raise Exception(\"No detector module found\")\n",
            "    plugin = modules.load_module(seek_module=\"plugin\",",
            "                                 directories=[\"plugins.%s\"]," % self.args.plugin_name,
            "                                 logger=logger)\n",
            "    tprint(arg=\"\\nPlugin information\", level=10, color=\"blue\")",
            "    tprint(arg=\"  Plugin type:    %s\" % plugin.PLUGIN_TYPE, level=10, color=\"white\")",
            "    tprint(arg=\"  Plugin subtype: %s\" % plugin.PLUGIN_SUBTYPE, level=10, color=\"white\")",
            "    tprint(arg=\"  Plugin version: %s\" % plugin.VERSION, level=10, color=\"white\")",
            "    tprint(arg=\"  Plugin id:      %s\" % plugin.ID, level=10, color=\"white\")\n",
            "    plugin.RapdPlugin(None, command, tprint, logger)\n",
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
            "        self.reply_address = self.command[\"return_address\"]",
            "        multiprocessing.Process.__init__(self, name=\"%s\")" % self.args.plugin_name,
            "        self.start()\n",
            "    def run(self):",
            "        \"\"\"Execution path of the plugin\"\"\"\n",
            "        self.preprocess()",
            "        self.process()",
            "        self.postprocess()\n",
            "    def preprocess(self):",
            "        \"\"\"Set up for plugin action\"\"\"\n",
            "        self.tprint(\"preprocess\")\n",
            "    def process(self):",
            "        \"\"\"Run plugin action\"\"\"\n",
            "        self.tprint(\"process\")\n",
            "    def postprocess(self):",
            "        \"\"\"Clean up after plugin action\"\"\"\n",
            "        self.tprint(\"postprocess\")\n",


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
            "        commandline_args = get_commandline()\n",
            "        main(args=commandline_args)\n",
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
