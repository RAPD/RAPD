"""Generate a UI Component for a plugin"""

"""
This file is part of RAPD

Copyright (C) 2018, Cornell University
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

__created__ = "2018-06-06"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
import importlib
import os
import string
import subprocess
import sys
import time

# RAPD imports
import utils.text as text

_NOW = time.localtime()
_LICENSE = """This file is part of RAPD

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
    return lines

HELP_TEXT = text.light_cyan + " <options> " + text.stop \
            + text.yellow + " <output file name>\n" + text.stop \
            + "  Generate UI Component for a RAPD plugin\n" \
            + text.light_cyan + "  --force (Boolean) (Default: False)\n" + text.stop \
            + text.light_gray + "    aliases: -f\n" + text.stop \
            + text.light_cyan + "  --help (Boolean) (Default: False)\n" + text.stop \
            + text.light_gray + "    aliases: -h\n" + text.stop \
            + text.light_cyan + "  --test (Boolean) (Default: False)\n" + text.stop \
            + text.light_gray + "    aliases: -t\n" + text.stop \
            + text.light_cyan + "  --verbose (Boolean) (Default: False)\n" + text.stop \
            + text.light_gray + "    aliases: -v\n" + text.stop \

# The rapd file generating parser - to be used by commandline RAPD processes
parser = argparse.ArgumentParser(add_help=False)

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



class FileGenerator(object):

    args = False

    def __init__(self, args=False):
        """Initialize the BaseFileGenerator instance"""

        print args

        self.args = args

    def run(self):
        """The main actions of the module"""

        self.preprocess()
        self.create_component()
        # self.write_file_docstring()
        # self.write_license()
        # self.write_docstrings()
        # self.write_imports()

    def preprocess(self):
        """Do pre-write checks"""

        # print "BaseFileGenerator.preprocess"

        # Determine what plugin is getting a UI Component
        plugin_error = False
        # Pointing to a plugin
        if self.args.plugin:
            self.plugin_file = self.find_plugin(self.args.plugin)
            if self.args.verbose:
                print "Creating UI component for %s" % self.plugin_file

        # No plugin specified
        else:
            plugin_error = True

        if plugin_error:
            print text.red + "You must enter a plugin or plugin directory to create a UI component for" + text.stop

        # Get the data type, plugin type, ID, and version for the plugin
        self.data_type, self.plugin_type, self.plugin_id, self.plugin_version = self.get_plugin_details(self.plugin_file)

        # Get the root of the src tree
        split_plugin_file = self.plugin_file.split(os.path.sep)
        self.src_root = os.path.join(*["/"] + split_plugin_file[:split_plugin_file.index("src")+1])

    def find_plugin(self, input_plugin):
        """
        Determine if the input_plugin is the plugin or its directory. Return the full path location of the plugin
        """

        # File
        if os.path.isfile(input_plugin):
            plugin = os.path.abspath(input_plugin)
        # Directory
        elif os.path.isdir(input_plugin):
            plugin = os.path.abspath(os.path.join(input_plugin, "plugin.py"))
        # Neither
        else:
            raise IOError("Cannot find plugin %s" % input_plugin)

        # Make sure the plugin exists before returning it
        if os.path.exists(plugin):
            return plugin
        else:
            raise IOError("Cannot find plugin %s" % input_plugin)

    def get_plugin_details(self, plugin_file):
        """
        Get details from a plugin file and return  (data_type, plugin_type, plugin_id, plugin_version)
        """
        # Transform plugin file to importable version
        split_plugin_file = plugin_file.split(os.path.sep)
        plugin_module_path = ".".join(split_plugin_file[split_plugin_file.index("src")+1:]).replace(".py", "")
        
        # Load the module
        pm = importlib.import_module(plugin_module_path)

        return (pm.DATA_TYPE, pm.PLUGIN_TYPE, pm.ID, pm.VERSION)

    def create_component(self):
        """
        Create the Angular component
        """

        # Save the current directory
        start_dir = os.getcwd()

        # Make sure we are in the correct directory
        component_dir = os.path.join(self.src_root, "ui/src/app/plugin_components", self.data_type.lower())
        os.chdir(component_dir)
        if self.args.verbose:
            print "  Changing directory to %s" % component_dir

        # Generate the component
        component_name = string.capwords((self.plugin_type + self.plugin_id + self.plugin_version).replace(".", ""))
        command = "ng generate component %s --skip-import --dry-run" % component_name
        if self.args.verbose:
            print "  Running %s" % command
        p1 = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        output = p1.communicate()[0]
        print output
        
        # Make sure the component was properly created

        # Add it to app.module.ts

        # Add it to index.ts

        # Move back to original directory
        os.chdir(start_dir)

    def write_file_docstring(self):
        """Write the docstring for file"""
        self.output_function(["\"\"\"This is a docstring for this container file\"\"\"\n"])

    def write_license(self):
        """Write the license"""
        self.output_function(["\"\"\"",] + split_text_blob(_LICENSE) + ["\"\"\"\n"])

    def write_docstrings(self):
        """Write file author docstrings"""
        self.output_function(["__created__ = \"%d-%02d-%02d\"" % (_NOW.tm_year, _NOW.tm_mon, _NOW.tm_mday),
                              "__maintainer__ = \"%s\"" % self.args.maintainer,
                              "__email__ = \"%s\"" % self.args.email,
                              "__status__ = \"Development\"\n"])

    def write_imports(self, write_list=(), added_normal_imports=(), added_rapd_imports=()):
        """Write the import sections"""
        standard_imports = ("argparse",
                            "from collections import OrderedDict",
                            "datetime",
                            "glob",
                            "json",
                            "logging",
                            "multiprocessing",
                            "os",
                            "pprint",
                            "pymongo",
                            "re",
                            "redis",
                            "shutil",
                            "subprocess",
                            "sys",
                            "time",
                            "unittest")

        rapd_imports = ("commandline_utils",
                        "detectors.detector_utils as detector_utils",
                        "utils")

        self.output_function(["# Standard imports"])
        for value in standard_imports:
            if value not in write_list:
                value = "# import " + value
            else:
                value = "import " + value
            self.output_function([value])

        for value in added_normal_imports:
            if (value not in write_list) or (value not in added_rapd_imports):
                self.output_function([value])

        self.output_function(["\n# RAPD imports"])
        for value in rapd_imports:
            if (value not in write_list) or (value not in added_rapd_imports):
                value = "# import " + value
            else:
                value = "import " + value
            self.output_function([value])

        # Special RAPD imports
        # print added_rapd_imports
        for value in added_rapd_imports:
            if (value not in standard_imports) or (value not in rapd_imports):
                self.output_function(["import " + value])

        # Blank line to keep it readable
        self.output_function([""])

def get_commandline(args=None):
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """Generate a UI Component for a RAPD plugin"""

    my_parser = argparse.ArgumentParser(parents=[parser],
                                        description=commandline_description)

    my_parser.add_argument("-c", "--commandline",
                           action="store_true",
                           dest="commandline",
                           help="Generate commandline argument parsing")

    # File name to be generated
    my_parser.add_argument(action="store",
                           dest="plugin",
                           nargs="?",
                           default=False,
                           help="Plugin to generate UI for")

    # Pull from the input list
    if isinstance(args, list):
        return my_parser.parse_args(args)
    # Grab straight from the commandline
    else:
        return my_parser.parse_args()

def main():

    # Get the commandline args
    commandline_args = get_commandline()

    print commandline_args

    filename = False 

    # file_generator = ModuleGenerator(commandline_args)

    # print file_generator
    # file_generator.run()

if __name__ == "__main__":

    print "rapd_generate_rapd_file.py"

    main()
