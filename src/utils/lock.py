"""
Helper for keeping processes singletons
"""

import fcntl
import os

def file_is_locked(file_path):
    """Method to make sure only one instance is running on this machine"""
    global file_handle

	# Create the directory for file_path if it does not exist
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))

    file_handle = open(file_path, "w")
    try:
        fcntl.lockf(file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return False
    except IOError:
        return True
