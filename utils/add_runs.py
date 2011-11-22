__author__ = "Frank Murphy"
__copyright__ = "Copyright 2011 Cornell University"
__credits__ = ["Frank Murphy","Jon Schuermann","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3-Clause"
__version__ = "0.9"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"
__date__ = "2011/01/01"

import os
import sys
import re
import paramiko
from rapd_database import Database
import random
import time

"""
Manipulate marcollect and xf_status files to hack a data run into the RAPD
system.
"""


def ReadHeader(image,logger=False):
    """
    Given a full file name for an ADSC image (as a string), read the header and
    return a dict with all the header info 
    """
    if logger:
        logger.debug('ReadHeader %s' % image)
    else:
        pass
        #print 'ReadHeader %s' % image
        
    header_items = ['HEADER_BYTES',
                    'DIM',
                    'BYTE_ORDER',
                    'TYPE',
                    'SIZE1',
                    'SIZE2',
                    'PIXEL_SIZE',
                    'BIN',
                    'ADC',
                    'DETECTOR_SN',
                    'COLLECT_MODE',
                    'BEAMLINE',
                    'DATE',
                    'TIME',
                    'DISTANCE',
                    'OSC_RANGE',
                    'PHI',
                    'OSC_START',
                    'TWOTHETA',
                    'THETADISTANCE',
                    'TWOTHETADIST',
                    'AXIS',
                    'WAVELENGTH',
                    'BEAM_CENTER_X',
                    'BEAM_CENTER_Y',
                    'TRANSMISSION',
                    'PUCK',
                    'SAMPLE',
                    'RING_CUR',
                    'RING_MODE',
                    'MD2_APERTURE',
                    'MD2_PRG_EXP',
                    'MD2_NET_EXP',
                    'CREV',
                    'CCD',
                    'ACC_TIME',
                    'UNIF_PED',
                    'IMAGE_PEDESTAL',
                    'CCD_IMAGE_SATURATION',
                    'COLLECT_MODE']
    try:
        rawdata = open(image,"rb").read()
        headeropen = rawdata.index("{")
        headerclose= rawdata.index("}")
        header = rawdata[headeropen+1:headerclose-headeropen]
    except:
        if logger:
            logger.exception('Error opening %s' % image)
        else:
            print 'Error opening %s' % image
    
    try:    
        #give zeroed values for items that may be in some headers but not others
        parameters = { 'transmission': 0,
                       'beamline'    : 0,
                       'puck'        : 0,
                       'sample'      : 0,
                       'ring_cur'    : 0,
                       'ring_mode'   : 0,
                       'md2_aperture': 0,
                       'md2_prg_exp' : 0,
                       'md2_net_exp' : 0,
                       'acc_time'    : 0,
                       'flux'        : 0,
                       'beam_size_x' : 0,
                       'beam_size_y' : 0,
                       'gauss_x'     : 0,
                       'gauss_y'     : 0,
                       'thetadistance': 0 }
        
        for item in header_items:
            pattern = re.compile('^'+item+'='+r'(.*);', re.MULTILINE)
            matches = pattern.findall(header)
            if len(matches) > 0:
                parameters[item.lower()] = str(matches[-1])
            else:
                parameters[item.lower()] = '0'
                
        #Transform the adsc date to mysql
        #parameters['date'] = date_adsc_to_sql(parameters['date'])
        
        #if twotheta is in use, distance = twothetadist
        try:
            if ( float(parameters['twotheta']) > 0.0 and float(parameters['thetadistance']) > 100.0):
                parameters['distance'] = parameters['thetadistance']
            if ( float(parameters['twotheta']) > 0.0 and float(parameters['twothetadist']) > 100.0):
                parameters['distance'] = parameters['twothetadist']
        except:
            if logger:
                logger.exception('Error handling twotheta for image %s' % image) 
        
        #return the parameters fro the header
        return(parameters)
    
    except:
        if logger:
            logger.exception('Error reading the header for image %s' % image) 


if __name__ == "__main__":
    print "Add runs to RAPD by manipulating the marcollect & xf_status files" 
    
    from rapd_beamlinespecific import secret_settings
    import logging, logging.handlers
    
    try:
        dir_root = sys.argv[1]
        mode = sys.argv[2]
        if mode in ("marcollect","xf_status","both"):
            pass
        else:
            "Error - mode must be xf_status, marcollect or both"
            sys.exit()
    except:
        print "Error - you must give a directory and a mode on the calling line"
        sys.exit()
    
    #set up logging
    LOG_FILENAME = '/tmp/addruns.log'
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
    
    db = Database(secret_settings['C'],logger)


    
    #compile a list of all image files
    image_files = []
    for root,dirs,files in os.walk(dir_root):
        for file in files:
            if file.endswith(".img"):
                image_files.append(os.path.abspath(os.path.join(root,file)))
                #print os.path.join(root,file)  
    #compile list of all run files
    run_files = []    
    headers = {}
    for image_file in image_files:
        #print image_file
        header = ReadHeader(image_file)
        #print header
        if header["collect_mode"] == "RUN":
            basename = os.path.basename(image_file)
            header["directory"] = os.path.dirname(image_file)
            header["image_prefix"] = "_".join(basename.split("_")[:-2])
            header["run_number"] = basename.split("_")[-2]
            header["image_number"] = int(basename.split("_")[-1].split(".")[0])
            run_files.append(image_file)
            headers[image_file] = header
            
    #now isolate runs - they all have the same directory and image_prefix
    runs = {}
    for run_file in run_files:
        header = headers[run_file]
        if ((header["directory"],header["image_prefix"],header["run_number"]) not in runs.keys()):
            runs[(header["directory"],header["image_prefix"],header["run_number"])] = [run_file]
        else:
            runs[(header["directory"],header["image_prefix"],header["run_number"])].append(run_file)
    
    #generate the information for entering a run into the database by rapd
    keys = runs.keys()
    for key in keys:
        print key,len(runs[key])
        if len(runs[key]) > 5:
            #find the first and last images
            first = 100000
            first_image = ""
            last = -100000
            last_image = ""
            for run_file in runs[key]:
                if headers[run_file]["image_number"] < first:
                    first = headers[run_file]["image_number"]
                    first_image = run_file
                elif headers[run_file]["image_number"] > last:
                    last = headers[run_file]["image_number"]
                    last_image = run_file
            print first_image,last_image
            #now create a dict in the correct format for adding to the database
            header = headers[first_image]
            run = {"file_source":"adsc",
                   "Directory":header["directory"], 
                   "Image_Prefix":header["image_prefix"], 
                   "Run":header["run_number"], 
                   "Start":first, 
                   "Total":last-first+1, 
                   "Distance":header["distance"],
                   "2-Theta":header["twotheta"], 
                   "Phi":header["phi"], 
                   "Kappa":0, 
                   "Omega":0, 
                   "Axis":"phi",
                   "Width":header["osc_range"], 
                   "Time":header["time"], 
                   "De-Zngr":0,
                   "Anomalous":"No",
                   "Beamline":header["beamline"][-1]}
            #add the run to the database
            if mode in ("marcollect","both"):
                db.addRun(run,run["Beamline"])
            #change the xf_status so that all the images are "seen" by rapd
            if mode in ("xf_status","both"):
                print "simulating data collection"
                image_index = random.randrange(1,1000)
                #set up paramiko session
                if run["Beamline"] == "C":
                    host = "nec-pid"
                    port = 22
                    username = "data_collection_computer"
                    password = "mypass"
                    xf_status = "/usr/local/ccd_dist_md2b_rpc/tmp/xf_status"
                #create the log file
                paramiko.util.log_to_file('/tmp/paramiko.log')
                #create the Transport instance
                transport = paramiko.Transport((host, port))
                #connect with username and password
                transport.connect(username = username, password = password)
                #establish sftp client
                sftp = paramiko.SFTPClient.from_transport(transport)
                #get the origninal xf_status
                sftp.get(xf_status,"xf_status.orig")
                #Now update the xf_status to simulate collection
                image_files = runs[key]
                image_files.sort()
                for image_file in image_files:
                    outfile = open("xf_status","w")
                    outfile.write("%d %s"%(image_index,image_file))
                    outfile.close()
                    time.sleep(0.1)
                    sftp.put("./xf_status",xf_status)
                    print "%d %s"%(image_index,image_file)
                    image_index += 1
                    time.sleep(1)
                #put the original back
                sftp.put("./xf_status.orig",xf_status)
                sys.exit()

