"""
Provides tools for loading modules
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2016-2017 Cornell University
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
__created__ = "2016-03-08"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import glob
import importlib

def load_module(seek_module, directories=False, logger=False):
    """
    Load the module file for the input specifications

    Keyword arguments
    seek_module -- the module to find and import
    directories -- iterable or string of directories to query (default = False)
                   Should be in dot format relative to the src directory
                   (ex. launch.launcher_adapters)
    """
    # print "load_module", seek_module, directories

    if logger:
        logger.debug("seek_module %s", seek_module)
        logger.debug("directories %s", directories)

    # # Agent we are looking for
    module = None

    # Wrap the directories as a string into an iterable
    if directories:
        if isinstance(directories, str):
            directories = (directories,)

    # Look for rapd plugins in the specified directories
    if directories:
        for directory in directories:
            try:
                if logger:
                    logger.debug("Attempting to load module %s", directory+"."+seek_module)
                module = importlib.import_module(directory+"."+seek_module)
                break
            except ImportError as e:
                # print e
                if logger:
                    logger.error(e)
                    logger.debug("FAILED to load module %s", directory+"."+seek_module)
                # raise

    else:
        try:
            # module = importlib.import_module(directory+"."+seek_module)
            module = importlib.import_module(seek_module)
        except ImportError as e:
            print e

    if module == None:
        raise Exception("No module found for: '%s'" % seek_module)
    else:
        return module


if __name__ == "__main__":
    load_module("credit")
