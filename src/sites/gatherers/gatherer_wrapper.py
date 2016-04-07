"""
Wraps the gatherers and allows calling by site specification
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2009-2016, Cornell University
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
import subprocess
import sys

# RAPD imports
import utils.commandline
import utils.site
import utils.text as text

def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """Data gatherer"""
    parser = argparse.ArgumentParser(parents=[utils.commandline.base_parser],
                                     description=commandline_description)

    return parser.parse_args()

def main():
    """
    The main process
    Search for and instantiate the gatherer
    """

    # Get the commandline args
    commandline_args = get_commandline()

    print dir(commandline_args)

    sys.exit(0)

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()

    # Assign site from commandline
    site = commandline_args.site

    # If no commandline site, look to environmental args
    if site == False:
        if environmental_vars["RAPD_SITE"]:
            site = environmental_vars["RAPD_SITE"]

    # Determine the site
    site_file = utils.site.determine_site(site_arg=commandline_args.site)
    if site_file == False:
        print text.error+"Could not determine a site file. Exiting."+text.stop
        sys.exit(9)

    # Import the site settings
    SITE = importlib.import_module(site_file)

    # Have a GATHERER file
    if hasattr(SITE, "GATHERER"):

        # Run it
        subprocess.call("$RAPD_HOME/bin/rapd.python $RAPD_HOME/src/sites/gatherers/"+SITE.GATHERER+" -vs %s" % SITE.ID, shell=True)

if __name__ == '__main__':

    main()
