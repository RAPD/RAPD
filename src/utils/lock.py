"""
Helper for keeping processes singletons
"""

import fcntl
import os

def file_lock(file_path):
    """Method to make sure only one instance is running on this machine"""
    # global file_handle

    # If file_path is a path, try to lock
    if file_path:
    	# Create the directory for file_path if it does not exist
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))

        file_handle = open(file_path, "w")
        try:
            fcntl.lockf(file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return False
        except IOError:
            #return True
            raise Exception("%s is already locked, unable to run" % file_path)

    # If file_path is False, always return False
    else:
        return False
