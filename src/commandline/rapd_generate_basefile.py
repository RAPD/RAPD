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



class BaseFileGenerator(object):

    args = False

    def __init__(self, args=False):
        """Initialize the BaseFileGenerator instance"""

        print args

        self.args = args

        if args:
            if args.file:
                def write_function(lines):
                    """Function for writing strings to file"""
                    out_file = open(args.file, "a+")
                    for line in lines:
                        out_file.write(line+"\n")
                    out_file.close()

            else:
                def write_function(lines):
                    """Function for writing strings to file"""
                    for line in lines:
                        sys.stdout.write(line+"\n")
        else:

            self.args = type('args', (object,), {})
            self.args.file = False
            self.args.maintainer = "Your name"
            self.args.email = "Your email"

            def write_function(lines):
                """Function for writing strings to file"""
                for line in lines:
                    sys.stdout.write(line+"\n")

        self.output_function = write_function

    def preprocess(self):
        """Do pre-write checks"""

        print "BaseFileGenerator.preprocess"

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
        self.output_function(["\"\"\"This is a docstring for this file\"\"\"\n"])

    def write_license(self):
        """Write the license"""
        self.output_function(["\"\"\"",] + split_text_blob(_LICENSE) + ["\"\"\"\n"])

    def write_docstrings(self):
        """Write file author docstrings"""
        self.output_function(["__created__ = \"%d-%d-%d\"" % (_NOW.tm_year, _NOW.tm_mon, _NOW.tm_mday),
                              "_maintainer__ = \"%s\"" % self.args.maintainer,
                              "__email__ = \"%s\"" % self.args.email,
                              "__status__ = \"Development\"\n"])

    def write_imports(self, write_list=()):
        """Write the import sections"""
        standard_imports = ("argparse",
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
                            "time")

        rapd_imports = ("commandline_utils",
                        "detectors.detector_utils as detector_utils",
                        "utils")

        self.output_function(["# Standard imports"])
        for value in standard_imports:
            if value not in write_list:
                value = "# " + value
            self.output_function([value + ""])

        self.output_function(["\n# RAPD imports"])
        for value in rapd_imports:
            if value not in write_list:
                value = "# " + value
            self.output_function([value + ""])
        self.output_function([""])

    def write_main_func(self, main_func_lines=False):
        """Write the main function"""
        if  not main_func_lines:
            main_func_lines = ["def main():",
                                  "    \"\"\"",
                                  "    The main process docstring",
                                  "    This function is called when this module is invoked from",
                                  "    the commandline",
                                  "    \"\"\"\n",
                                  "    print \"main\"\n"]


            if self.args.commandline:
                main_func_lines.replace("def main():", "def main(args):")

        # Output the lines
        self.output_function(main_func_lines)


    def write_main(self, main_lines=False):
        """Write the main function"""
        if not main_lines:
            if self.args.commandline:
                main_lines = ["if __name__ == \"__main__\":\n",
                              "    # Get the commandline args",
                              "    commandline_args = get_commandline()\n",
                              "    # Execute code",
                              "    main(args=commandline_args)\n",]
            else:
                main_lines = ["if __name__ == \"__main__\":\n",
                              "    # Execute code",
                              "    main()"]

        self.output_function(main_lines)

class CommandlineFileGenerator(BaseFileGenerator):

    def run(self):
        """The main actions of the module"""

        self.preprocess()

        self.write_file_docstring()
        self.write_license()
        self.write_docstrings()
        self.write_imports()
        self.write_main_func()
        self.write_commandline()
        self.write_main()

    def preprocess(self):
        """Do pre-write checks"""

        print "CommandlineFileGenerator.preprocess"

        self.args.commandline = True

        super(CommandlineFileGenerator, self).preprocess()

    def write_commandline(self):
        """Write commanling handling into the file"""

        commandline_lines = ["def get_commandline():",
                              "    \"\"\"",
                              "    Grabs the commandline",
                              "    \"\"\"\n",
                              "    print \"get_commandline\"\n",
                              "    # Parse the commandline arguments",
                              "    commandline_description = \"Generate a generic RAPD file\"",
                              "    parser = argparse.ArgumentParser(description=commandline_description)\n",
                              "    # A True/False flag",
                              "    parser.add_argument(\"-c\", \"--commandline\",",
                              "                        action=\"store_true\",",
                              "                        dest=\"commandline\",",
                              "                        help=\"Generate commandline argument parsing\")\n",
                              "    # File name to be generated",
                              "    parser.add_argument(action=\"store\",",
                              "                        dest=\"file\",",
                              "                        nargs=\"?\",",
                              "                        default=False,",
                              "                        help=\"Name of file to be generated\")\n",
                              "    return parser.parse_args()\n"]

        self.output_function(commandline_lines)


def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """Generate a generic RAPD file"""

    my_parser = argparse.ArgumentParser(parents=[parser],
                                        description=commandline_description)

    my_parser.add_argument("-c", "--commandline",
                           action="store_true",
                           dest="commandline",
                           help="Generate commandline argument parsing")

    # File name to be generated
    my_parser.add_argument(action="store",
                           dest="file",
                           nargs="?",
                           default=False,
                           help="Name of file to be generated")

    return my_parser.parse_args()

def main():

    # Get the commandline args
    commandline_args = get_commandline()

    print commandline_args

    filename = False #"foo.py"

    if commandline_args.commandline:
        file_generator = CommandlineFileGenerator(commandline_args) #BaseFileGenerator(commandline_args)
    else:
        file_generator = BaseFileGenerator(commandline_args)

    print file_generator
    file_generator.run()

if __name__ == "__main__":

    print "rapd_generate_rapd_file.py"

    main()