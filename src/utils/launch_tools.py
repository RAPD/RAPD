"""
Tools for launch and launcher
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2016-2018 Cornell University
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

__created__ = "2016-03-02"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import os
import stat
import tempfile

from utils.text import json
from bson.objectid import ObjectId

def write_command_file(target_directory, command, message):
    """
    Write the message to a command file in the target directory

    Keyword arguments
    target_directory -- directory to write the command file in
    command -- command type
    message -- contents of the command file

    message will be the content of the file:
    target_directory/command_{random chars}.rapd
    """

    # Make sure the target directory exists
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)

    out_file = tempfile.NamedTemporaryFile(mode="w",
                                           dir=target_directory,
                                           prefix=command+"_",
                                           suffix=".rapd",
                                           delete=False)
    out_file.write(json.dumps(message))
    out_file.close()

    return out_file.name


def write_command_script(target_file, command_line, shell="/bin/tcsh"):
    """
    Write a command script. This method was written to generate executable
    files as demanded by the cluster setup at SERCAT

    Keyword arguments
    target_file -- full path location of the command script file
    command_line -- line to be executed
    shell -- shell of choice (Default = "/bin/tcsh")
    """

    target_directory = os.path.dirname(target_file)

    # Make sure the target directory exists
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)

    out_file = open(target_file, "w")
    out_file.write(shell+"\n")
    out_file.write(command_line)
    out_file.close()
    st = os.stat(target_file)
    os.chmod(target_file, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return target_file

def get_site_tag(message, default_site=False):
    """Find and return the site_tag from the image header"""
    # Find site_tag from SNAP
    site_tag = False
    if message.get('image1', False):
        site_tag = message['image1'].get('site_tag')
    # Find site_tag from INTEGRATE
    elif message.get('data', False):
        site_tag = message['data']['image_data'].get('site_tag')
    # Fall back on default if present
    elif default_site:
        site_tag = default_site

    return site_tag

def fix_command(message):
    """
    Adjust the command passed in in install-specific ways
    """
    # Adjust the working directory for the launch computer
    work_dir_candidate = os.path.join(
        message["directories"]["launch_dir"],
        message["directories"]["work"])

    # Make sure this is an original directory
    if os.path.exists(work_dir_candidate):
        # Already exists
        for i in range(1, 1000):
            if not os.path.exists("_".join((work_dir_candidate, str(i)))):
                work_dir_candidate = "_".join((work_dir_candidate, str(i)))
                break
            else:
                i += 1
    # Now make the directory
    if os.path.exists(work_dir_candidate) == False:
        os.makedirs(work_dir_candidate)

    # Modify command
    message["directories"]["work"] = work_dir_candidate

    return message
