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
import shutil
import string
import subprocess
import sys
import tempfile
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

        # Generate the component
        component_name = string.capwords((self.plugin_type + self.plugin_id + self.plugin_version).replace(".", ""))
        command = "ng generate component %s --skip-import " % component_name
        if self.args.test:
            command += "--dry-run"
        if self.args.verbose:
            print "Running %s" % command
        p1 = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        output = p1.communicate()[0]
        # print output
        # Look for ERROR in output
        if "ERROR" in output:
            if self.args.test:
                print  "Error generating component", "\n"+output+"\n"
            else:
                raise IOError("Error generating component", "\n"+output)
            
        """
        The Schematic workflow failed. See above.
        ERROR! src/app/plugin_components/mx/index3b34200/index3b34200.component.css already exists.
        ERROR! src/app/plugin_components/mx/index3b34200/index3b34200.component.html already exists.
        ERROR! src/app/plugin_components/mx/index3b34200/index3b34200.component.spec.ts already exists.
        ERROR! src/app/plugin_components/mx/index3b34200/index3b34200.component.ts already exists.
        """

        # Make sure the component was properly created
        if not os.path.isdir(component_name.lower()):
            if not self.args.test:
                raise IOError("Component directory %s not created" % component_name.lower())

        # Edit the component to the initial state
        # TS
        ts_file = os.path.join(component_dir, component_name.lower(), component_name.lower()+'.component.ts')
        self.write_ts_file(ts_file)

        # HTTP
        html_file = os.path.join(component_dir, component_name.lower(), component_name.lower()+'.component.html')
        self.write_html_file(ts_file[:-2]+"html")

        # Add it to app.module.ts
        self.add_to_app(component_name, ts_file)

        # Add it to index.ts
        self.add_to_index(ts_file)

        # Move back to original directory
        os.chdir(start_dir)

    def write_ts_file(self, ts_file):
        """
        Update generated TS file to a rudimentary state for a new plugin component
        """

        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file_name = tmp_file.name
        in_lines = open(ts_file, "r").readlines()

        for line in in_lines:

            tmp_file.write(line)

            # Insert some lines
            if line.startswith("export class"):
                tmp_file.write("\n")
                tmp_file.write("  // Put some initial test data into the component\n")
                tmp_file.write("  result: any = {'status':'This is the initial data'};\n")
                tmp_file.write("\n")
                tmp_file.write("  // A helper method\n")
                tmp_file.write("  objectKeys = Object.keys;\n")

        # Close the temp file
        tmp_file.close()

        # Print file for edification
        if self.args.verbose:
            print "\nNew file %s" % ts_file
            for line in open(tmp_file_name, "r").readlines():
                print "  ", line.rstrip()

        # Move the new file to replace the naked file
        if not self.args.test:
            shutil.move(tmp_file_name, ts_file)

    def write_html_file(self, html_file):
        """
        Update generated HTML file to a rudimentary state for a new plugin component
        """

        html_lines = """
<div class="result-panel child">
    <mat-tab-group>
        <mat-tab label="Raw">
                <div fxLayout="row" fxLayoutGap="10px">
                    <div fxFlex="none">
                        <div>
                            <pre>{{result | json}}</pre>
                        </div>
                    </div>
                </div>
            </mat-tab>
    </mat-tab-group>
</div>
        """

        # Write the file
        if not self.args.test:
            with open(html_file, "w") as out_file:
                out_file.write(html_lines)

        # Print file for edification
        if self.args.verbose:
            print "\nNew file %s" % html_file
            print html_lines

    def add_to_app(self, component_name, ts_file):
        """
        Add a plugin component to the app.module.ts
        """

        component_name += "Component"

        # Derive the imported file name
        import_file = ts_file[:-3][ts_file.index("/app")+5:]
        import_line = "import { %s } from '%s';" % (component_name, import_file)
        # print import_line

        # Derive the app.module.ts location
        app_module_ts = ts_file[:ts_file.index("/app/")+5]+"app.module.ts"
        # print app_module_ts

        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file_name = tmp_file.name
        in_lines = open(app_module_ts, "r").readlines()

        # Go through app.module.ts and create new file
        for line in in_lines:

            # Insert some lines
            if line.startswith("// INSERT POINT FOR PLUGIN COMPONENTS IMPORT"):
                tmp_file.write("%s\n" % import_line)
            elif line.startswith("    // INSERT POINT FOR PLUGIN COMPONENTS DECLARATION"):
                tmp_file.write("    %s,\n" % component_name)
            elif line.startswith("    // INSERT POINT FOR PLUGIN COMPONENTS ENTRYCOMPONENTS"):
                tmp_file.write("    %s,\n" % component_name)

            tmp_file.write(line)

        # Close the temp file
        tmp_file.close()

        # Print file for edification
        if self.args.verbose:
            print "\napp.module.ts"
            for line in open(tmp_file_name, "r").readlines():
                print "  ", line.rstrip()

        # Move the new file to replace the naked file
        if not self.args.test:
            shutil.move(tmp_file_name, app_module_ts)
        else:
            os.unlink(tmp_file_name)

    def add_to_index(self, ts_file):
        """
        Add a plugin component to the appropriate index.ts
        """

        # Derive the imported file name
        export_file = ts_file[:-3][ts_file.index("/app")+5:]
        export_line = "export * from '%s';" % export_file
        # print export_line

        # Derive the index.ts file
        ts_file_split = ts_file.split(os.path.sep)
        index_ts =  os.path.join(*[os.path.sep]+ts_file_split[:ts_file_split.index("plugin_components")+2]+["index.ts"])
        # print index_ts

        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file_name = tmp_file.name
        in_lines = open(index_ts, "r").readlines()

        # Go through app.module.ts and create new file
        for line in in_lines:

            tmp_file.write(line)

            # Insert some lines
            if line.startswith("// INSERT POINT FOR PLUGIN COMPONENTS"):
                tmp_file.write("%s\n" % export_line)

        # Close the temp file
        tmp_file.close()

        # Print file for edification
        if self.args.verbose:
            print "\n%s" % index_ts
            for line in open(tmp_file_name, "r").readlines():
                print "  ", line.rstrip()

        # Move the new file to replace the naked file
        if not self.args.test:
            shutil.move(tmp_file_name, index_ts)
        else:
            os.unlink(tmp_file_name)

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
