"""
This file is part of RAPD

Copyright (C) 2016 Cornell University
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

__created__ = "2016-01-27"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

import functools
import glob
import importlib
import os
import socket
import sys

def copy_attrs(source, target):
    """Copy all the public attrs from one object to local scope"""

    # Get the attributes
    keys = source.__dict__.keys()
    # Run through the attributes
    for key in keys:
        # Ignore private
        if not key.startswith("_"):
            setattr(target, key, getattr(source, key))

def read_secrets(secrets_file, target):
    """Read in secrets file and put attrs in target context"""
    secrets = importlib.import_module(secrets_file)
    copy_attrs(secrets, target)

def get_ip_address():
    """Returns the IP address for the host of the requesting process"""

    # Create socket
    s_tmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Connect
    s_tmp.connect(("google.com", 80))

    # Grab the IP address for this computer
    ip_address = s_tmp.getsockname()[0]

    # Close the socket
    s_tmp.close()

    return ip_address

def get_site_files():
    """Returns a list of site files

    Uses the PYTHONPATH to find the sites directory for this rapd install and then
    walks it to find all files that have names that match "*.py" and do not start with
    "_" or have the word "secret"
    """
    print "get_site_files"

    def look_for_sites_files(directory):
        potential_files = []
        for filename in glob.glob(directory+"/*.py"):
            # No secret-containing files
            if "secret" in filename:
                continue
            # No files that start with _
            if filename.startswith("_"):
                continue
            # Filename OK
            potential_files.append(os.path.join(path, filename))

        return potential_files

    # Look for site file in local directory first
    # possible_files = look_for_sites_files(os.getcwd())
    possible_files = []

    # Looking for the rapd src directory
    sites_dir = False
    for path in sys.path:
        if path.endswith("src") and os.path.exists(os.path.join(path, "sites")):
            sites_dir = os.path.join(path, "sites")
            break

    print sites_dir
    if sites_dir:
        possible_files += look_for_sites_files(sites_dir)

    if len(possible_files) == 0:
        raise Exception("No potential site files found")
    else:
        return possible_files

def check_site_against_known(site_str):
    """Check a site string against known sites in the sites directory

    Keyword arguments:
    site_str -- user-specified site string
    """
    pass

def determine_site(site_arg=False):
    """Determine the site for a run instance

    Keyword arguments:
    site_arg -- user-specified site arguments (default None)
    """
    print "determine_site"

    # Get possible site files
    site_files = get_site_files()
    print site_files

    # Transform site files to a more palatable form
    safe_sites = {}
    for site_file in site_files:
        safe_site = os.path.basename(site_file).split(".")[0].lower()
        safe_sites[safe_site] = site_file

    # No site_arg, look to environmental variable
    # if site_arg == None:
    #     site_arg = os.getenv('RAPD_SITE', None)

    # Still no site_arg, look to the path for the site
    safe_site_args = []
    if site_arg == False:
        cwd = os.getcwd()
        path_elems = cwd.split(os.path.sep)
        for path_elem in reversed(path_elems):
            safe_path_elem = path_elem.lower()
            if len(safe_path_elem) > 0:
                safe_site_args.append(safe_path_elem)

    # Have a site_arg or environmental variable
    else:
        # Transform the input site_arg to lowercase string
        safe_site_args.append(str(site_arg).lower())

    # Now search safe_sites for safe_site_args
    sites = []
    for safe_site_arg in safe_site_args:
        if safe_site_arg in safe_sites:
            print "Have one! %s %s" % (safe_site_arg, safe_sites[safe_site_arg])
            sites.append(safe_site_arg)

    # Need only one site
    if len(sites) == 0:
        return False
    elif len(sites) > 1:
        raise Exception("More than one site found")
    else:
        site_file = "sites."+os.path.basename(safe_sites[sites[0]]).replace(".py", "")
        return site_file

def verbose_print(arg, level, verbosity=1):
    if level <= verbosity:
        print arg


def get_environmental_variables(pre="RAPD"):
    """
    Return a dict of environmental variables

    Keyword arguments:
    pre -- prefix to select for
    """

    environmental_variables = {}

    for key, value in os.environ.iteritems():
        if key.startswith(pre):
            environmental_variables[key] = value

    return environmental_variables

if __name__ == "__main__":

    print "sites.py"
    print "============="

    terminal_print = functools.partial(verbose_print, verbosity=2)
    determine_site()
    determine_site("necat_C")
