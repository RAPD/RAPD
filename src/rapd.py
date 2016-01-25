"""
RAPD - Automated data analysis for macromolecular crystallography

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

__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"


"""
rapd.py is the main process for RAPD. 
"""

import getopt,sys, logging, logging.handlers
import fcntl
import time
import os 
from rapd_model import Model


file_handle = None

def file_is_locked(file_path):
    global file_handle 
    file_handle= open(file_path, 'w')
    try:
        fcntl.lockf(file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return False
    except IOError:
        return True

def get_command_line():
    """
    Handle the command line and pass back variables to main

    RAPD v1.8.0
    ===========
    
    Synopsis: Rapid Automated Processing of Data
    ++++++++      
    
    Proper use: >[python2.6] rapd.py beamline_identifier
    ++++++++++
                beamline_identifier are keys to beamline_settings and secret_settings, 
                which are imported through rapd_beamlinespecific.py
                For the case of NE-CAT, beamline_identifiers are C and E
                
                log file is created in /tmp/rapd.log[.1-5]
    +++++
    """

    file_path = '/tmp/lock/rapd_core.lock'

    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs((os.path.dirname(file_path)))


    if file_is_locked(file_path):
        print 'another instance is running exiting now'
        sys.exit(0)
    else:
        print 'no other instance is running'

        verbose = False        
        try:
            opts,args = getopt.getopt(sys.argv[1:],"v")
        except getopt.GetoptError, err:
            # print help information and exit:
            print str(err) # will print something like "option -a not recognized"
            sys.exit(2)
        if len(args) != 1:
            print 'Please indicate the beamline'
            exit(3)
        return(args[0],verbose)

def main(beamline_in=None):
        #set up logging
        LOG_FILENAME = '/tmp/rapd.log'
        # Set up a specific logger with our desired output level
        logger = logging.getLogger('RAPDLogger')
        logger.setLevel(logging.DEBUG)
        # Add the log message handler to the logger
        handler = logging.handlers.RotatingFileHandler(
                  LOG_FILENAME, maxBytes=5000000, backupCount=5)
        #add a formatter
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
        #get the command line
        try:
            beamline,verbose = get_command_line()
        except:
            if beamline_in:
                beamline = beamline_in
            else:
                return(False)
        
        #instantiate the model
        try:
            MODEL = Model(beamline=beamline,
                          logger=logger)
            MODEL.Start()
        except:
            logger.critical("SOME ERROR in starting the model")  


if __name__ == '__main__':
    
    main()
    
    
    
    
