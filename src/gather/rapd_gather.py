"""
Wraps the gatherers and allows calling by site specification
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2009-2018, Cornell University
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

__created__ = "2016-02-29"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

# Standard imports
import argparse
import importlib
import os
import subprocess
import sys
import time

# RAPD imports
import utils.commandline
import utils.site
from utils.lock import lock_file, close_lock_file
import utils.text as text

def get_commandline():
    """Get the commandline variables and handle them"""

    # Get the raw commandline args
    raw_args = sys.argv[1:]

    # Parse the commandline arguments
    commandline_description = """Data gatherer"""
    parser = argparse.ArgumentParser(description="""Data gatherer""",
                                     add_help=False)
    # Help
    parser.add_argument("--help", "-h",
                        action="store_true",
                        dest="help")
    
    parser.add_argument("--python", "-p",
                        action="store",
                        default="rapd.python",
                        dest="python",
                        help="Which python to launch managed file")
    
    parser.add_argument("-s", "--site",
                        action="store",
                        dest="site",
                        help="Define the site (ie. NECAT)")
    
    #parsed_args, unknownargs = parser.parse_known_args()

    #if parsed_args.help:
    #    parser.print_help()

    #return parsed_args, unknownargs
    
    return raw_args, parser.parse_args()

def main():
    """
    The main process
    Search for and instantiate the gatherer
    """

    # Get the commandline args
    raw_args, commandline_args = get_commandline()

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()

    # Assign site from commandline
    site = commandline_args.site

    # If no commandline site, look to environmental args
    if site == None:
        if "RAPD_SITE" in environmental_vars:
            site = environmental_vars["RAPD_SITE"]

    # Determine the site
    site_file = utils.site.determine_site(site_arg=site)
    if site_file == False:
        print(text.error+"Could not determine a site file. Exiting."+text.stop)
        sys.exit(9)


    # Import the site settings
    SITE = importlib.import_module(site_file)

    # Have a GATHERER file
    if hasattr(SITE, "GATHERER"):

        # The environmental_vars
        path = os.environ.copy()

        # Compose the command
        #command = raw_args[:]
        #command.insert(0, "%s/src/sites/gatherers/" % environmental_vars["RAPD_HOME"] + SITE.GATHERER)
        #command.insert(0, "rapd.python")
        
        command = raw_args[:]
        command.insert(0, "%s/src/sites/gatherers/" % environmental_vars["RAPD_HOME"] + SITE.GATHERER)
        command.insert(0, "--managed_file")
        command.insert(0, "%s/src/utils/overwatch.py" %environmental_vars["RAPD_HOME"])
        command.insert(0, commandline_args.python)

        # Run it
        #print command
        
        gatherer_process = subprocess.Popen(command, env=path)

        # Make sure the managed process actually ran
        time.sleep(0.5)
        exit_code = gatherer_process.poll()
        if not exit_code == None:
            print(text.error+"Gatherer exited on start. Exiting."+text.stop)
            sys.exit(9)

    # Unable to find a gatherer for this site
    else:
        print(text.error+"Could not find a gatherer for this site %s. Exiting." % site +text.stop)
        sys.exit(9)

if __name__ == '__main__':

    main()
