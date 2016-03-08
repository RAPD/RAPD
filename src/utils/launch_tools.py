"""
This file is part of RAPD

Copyright (C) 2016, Cornell University
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

"""
Provides tools for launch and launcher
"""

import os
import stat
import tempfile

def write_command_file(target_directory, command, message):
    """
    Write the message to a command file in the target directory
    """

    # Make sure the target directory exists
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)

    out_file = tempfile.NamedTemporaryFile(mode="w",
                                           dir=target_directory,
                                           prefix=command+"_",
                                           suffix='.rapd',
                                           delete=False)
    out_file.write(message)
    out_file.close()

    return out_file.name


def write_command_script(target_file, command_line, shell="/bin/tcsh"):
    """
    Write a command script
    """

    target_directory = os.path.dirname(target_file)

    # Make sure the target directory exists
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)

    out_file = open(target_file, "w")
    out_file.write(shell+"\n")
    out_file.write(command_line)
    out_file.close()
    os.chmod(target_file, stat.S_IXGRP)

    return out_file
