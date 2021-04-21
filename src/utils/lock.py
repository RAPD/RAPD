"""
Helper for keeping processes singletons
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
import fcntl
import os

def lock_file(file_path):
    """
    Method to make sure only one instance is running on this machine.

    If file_path is False, no locking will occur
    If file_path is not False and is already locked, an error will be thrown
    If file_path is not False and can be locked, a False will be returned

    Keyword arguments
    file_path -- potential file for maintaining lock
    """

    # If file_path is a path, try to lock
    if file_path:

        # Create the directory for file_path if it does not exist
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))

        global _file_handle
        _file_handle = open(file_path, "w")
        try:
            fcntl.lockf(_file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return False
        except IOError:
            #raise Exception("%s is already locked, unable to run" % file_path)
            return True

    # If file_path is False, always return False
    else:
        return True

def close_lock_file():
    """Close the _file_handle handle."""
    _file_handle.close()

