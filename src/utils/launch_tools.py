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

import tempfile

def write_command_file(target_directory, command, message):
    """
    Write the message to a command file in the target directory
    """

    out_file = tempfile.NamedTemporaryFile(mode="w",
                                           dir=target_directory,
                                           prefix=command+"_",
                                           suffix='.rapd',
                                           delete=False)
    out_file.write(message)
    out_file.close()

    return out_file.name
