__author__ = "Frank Murphy"
__copyright__ = "Copyright 2009,2010,2011 Cornell University"
__credits__ = ["Frank Murphy","Jon Schuermann","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3-Clause"
__version__ = "0.9"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"
__date__ = "2009/07/08"

"""
rapd.py is the main process for RAPD. 
"""

import getopt,sys, logging, logging.handlers
from rapd_model import Model

def get_command_line():
    """
    Handle the command line and pass back variables to main

    RAPD v0.9
    ==========
    
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
                  LOG_FILENAME, maxBytes=1000000, backupCount=5)
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
    
    
    
    
