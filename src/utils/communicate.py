"""
Interprocess communication methods for RAPD
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

__created__ = "2016-03-02"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

# Standard imports
import json
import socket

def rapd_send(controller_address, message, logger=False):
    """
    Use standard socket-based message used in RAPD

    The address for the controller must be set to self.controller_address
    as a tuple or list ex. ("164.54.212.165", 50001)
    """

    # Connect
    _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        _socket.connect(tuple(controller_address))
    except socket.error:
        if logger:
            logger.error("Connection refused to %s", controller_address)
        return False

    # Encode message as JSON
    message_encoded = json.dumps(message)

    # Give the message start and end tags
    message_encoded = "<rapd_start>" + message_encoded + "<rapd_end>"

    # Send
    # try:
    message_length = len(message_encoded)
    total_sent = 0
    while total_sent < message_length:
        sent = _socket.send(message_encoded)
        total_sent += sent

    # Close the socket connection
    _socket.close()

    # Return
    return True
    # except:
    #     self.logger.exception('Error in sending data to controller')
    #     return(False)


if __name__ == "__main__":

    rapd_send(("10.0.0.83", 50000), ("echo", "hello", ("10.0.0.83", 50000)))
