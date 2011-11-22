__author__ = "Jon Schuermann, Frank Murphy"
__copyright__ = "Copyright 2009,2010,2011 Cornell University"
__credits__ = ["Frank Murphy","Jon Schuermann","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3-Clause"
__version__ = "0.9"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"
__date__ = "2009/07/14"

import threading
import multiprocessing
import os
import sys
import subprocess
import time
import shutil
import logging, logging.handlers

from rapd_communicate import Communicate
from phenix.multipart_encoder import post_multipart

class QuickAnalysisAction:
    """
    Not the typical remote-called agent.
    Connects to remote distl server and then parses results
    """
    def __init__(self,fullname,server,port,logger):
        logger.info('QuickAnalysisAction::__init__')
        logger.debug('fullname: %s server: %s port: %d \n' % (fullname,server,port))
        
        self.fullname = fullname
        self.server = server
        self.port = port
        self.logger = logger
        self.run()
    
    def run(self):
        try:
            self.logger.debug('QuickAnalysisAction::run')
            self.queryServer()
            self.parseResults()
            #print self.output
        except:
            self.output = False
        
    def queryServer(self):
        """
        Submit image to server and get response
        Raw response placed in self.raw
        """
        #print self.server+':'+str(self.port)
        server_response = post_multipart(host=self.server+':'+str(self.port),selector="/spotfinder",fields=[("filename",self.fullname),("bin",1),], files = [])
        self.raw = server_response.read()
        #print self.raw
        
    def parseResults(self):
        """
        Parse self.raw into a dict for return to the caller
        """
        lookup = { 0 : 'fullname',
                   1 : 'total_spots',
                   2 : 'in_res_spots',
                   3 : 'good_b_spots',
                   4 : 'total_signal',
                   5 : 'ice_rings',
                   6 : 'distl_res',
                   7 : 'labelit_res',
                   8 : 'max_cell',
                   9 : 'saturation_50',
                   10: 'overloads',
                   11: None }
        
        self.output = {'max_signal_str' : 0,
                       'mean_int_signal': 0,
                       'min_signal_str' : 0}
        
        lines = self.raw.split('\n')
        for i,line in enumerate(lines):
            print i,line
            sline = line.split(':')
            try:
                if (i == 9):
                    value = float(sline[-1].replace('%','').strip())
                elif (i in [1,2,3,4,5,10]):
                    value = int(sline[-1].strip())
                elif (i in [6,7,8]):
                    value = float(sline[-1].strip())
                elif (i == 11):
                    break
                else:
                    value = sline[-1].strip()
            except:
                value = 0
            self.output[lookup[i]] = value
            """
            0 Image: /gpfs2/users/necat/FM_Jul10/images/screen/thaum_pair_1_001.img
            1                                                      Spot Total :     263
            2                                       Method-2 Resolution Total :     233
            3                                           Good Bragg Candidates :     219
            4 Total integrated signal, pixel-ADC units above local background : 4653500
            5                                                       Ice Rings :       1
            6                                             Method 1 Resolution :    7.14
            7                                             Method 2 Resolution :    4.00
            8                                               Maximum unit cell :   231.5
            9                                        Saturation, Top 50 Peaks :  28.4 %
            10                                  In-resolution overloaded spots :       3
            11 
            """
        
    

class QuickAnalysis(multiprocessing.Process,Communicate):
    """    
    __init__ is merely used to stow variables passed in,
    to initialize the process, and to start the process 
    
    run is used to orchestrate events
    """

    def __init__(self,input,logger=None,verbose=True):       
        """
        Initialize the QuickAnalysis process
        
        input   is whatever is passed in
        pipe    is the communication back to the calling process
        verbose is to set the level of output
        logger  is logging for debugging.
        """

        logger.info('QuickAnalysis.__init__')
     
        self.input                              = input
        self.verbose                            = verbose
        self.logger                             = logger
        
        #Setting up data input
        self.setup                              = self.input[1]
        self.header                             = self.input[2]
        self.header2                            = False
        if self.input[3].get('distance'):
            self.header2                            = self.input[3]
            self.preferences                        = self.input[4]
        else:
            self.preferences                        = self.input[3]        
        self.controller_address                 = self.input[-1]
        #print self.controller_address
        #For testing individual modules
        self.test                               = False         
        self.distl_timer                        = 5        
        #This is where I place my overall folder settings.
        self.working_dir                        = False    
        self.pixel_log                          = False
        self.distl_log                          = False
        self.distl_results                      = False
        self.distl_summary                      = False
        self.output_files                       = False
        self.results                            = False

        #******BEAMLINE SPECIFIC*****
        host = os.uname()[1]
        if host == 'vertigo.nec.aps.anl.gov':    
            self.beamline_use                   = False        
        else:
            self.beamline_use                   = True        
        #******BEAMLINE SPECIFIC*****
        
        multiprocessing.Process.__init__(self,name='QuickAnalysis')        
        #starts the new process
        self.start()
        
    def run(self):
        """
        Convoluted path of modules to run.
        """
        self.logger.debug('QuickAnalysis::run')                    
        self.preprocess()
        self.preprocessLabelit()
        self.preprocessMultiDistl()                                
        self.multiDistl()                            
        self.postprocess()                                                   
                                       
    def preprocess(self):
        """
        Things to do before the main process runs
        1. Change to the correct directory
        2. Print out the reference for labelit
        """       
        self.logger.debug('QuickAnalysis::preprocess')
        #change directory to the one specified in the incoming dict
        self.working_dir = self.setup.get('work')
        try:     
            os.makedirs(self.working_dir)    
        except:
            self.logger.exception('Could not make working dir.')            
        os.chdir(self.working_dir)
        #print out recognition of the program being used
        self.PrintInfo()
    
    def preprocessLabelit(self):
        """
        Setup extra parameters for Labelit if turned on. Will always set beam center from image header. 
        Creates dataset_preferences.py file for editing later in the Labelit error iterations if needed. Only place
        where self.labelit_settings1 are set if True. 
        """
        try:
            index_hi_res   = str(self.preferences.get('index_hi_res'))
            self.beamline  = self.header.get('beamline')
            flip           = self.preferences.get('beam_flip')  
            if str(self.preferences.get('x_beam')):
                if str(self.preferences.get('x_beam')) != '0':
                    x_beam         = str(self.preferences.get('x_beam'))
                else:
                    x_beam         = str(self.header.get('beam_center_x'))
            if str(self.preferences.get('y_beam')):
                if str(self.preferences.get('y_beam')) != '0':
                    y_beam         = str(self.preferences.get('y_beam'))
                else:
                    y_beam         = str(self.header.get('beam_center_y'))                                               
            preferences    = open('dataset_preferences.py','w')            
            #If user wants to change the res limit for autoindexing.
            """
            if index_hi_res != '0.0':
                preferences.write('distl_highres_limit=' + index_hi_res + '\n')            
            """
            preferences.write('distl_highres_limit=4.0\n')   
            #If Malcolm flips the beam center in the image header.
            if flip == 'True':
                preferences.write('autoindex_override_beam=(' + y_beam + ',' + x_beam + ')\n')              
            else:
                preferences.write('autoindex_override_beam=(' + x_beam + ',' + y_beam + ')\n')                        
            preferences.close()  
         
        except:
            self.logger.exception('**Could not set extra Labelit preferences.**')
    
    def preprocessMultiDistl(self):
        """
        Setup Distl for multiprocessing if enabled.
        """
        self.logger.debug('QuickAnalysis::preprocessMultiDistl')
        try:            
            distl_input  = []
            distl_input.append(self.header.get('fullname'))                
            self.distl_output     = multiprocessing.Queue()
            self.DISTLPROCESS = multiprocessing.Process(target=multiDistlAction(input=distl_input, output=self.distl_output, logger=self.logger)).start()
            
        except:
            self.logger.exception('**Error in multipreprocessDistl.**')
        
    def multiDistl(self):
        """
        Error checking Distl multiprocessing.
        """
        self.logger.debug('QuickAnalysis::multiDistl')
        if self.pixel_log == False:
            self.pixel_log = []             
        
        try:                         
            timer = 0
            pid = self.distl_output.get()            
            while self.still_running(pid):
                time.sleep(1)
                timer += 1
                print 'Waiting for Distl to finish ' + str(timer) + ' seconds'
                self.logger.debug('Waiting for Distl to finish '+str(timer)+' seconds')
                if self.distl_timer:
                    if timer >= self.distl_timer:
                        self.kill_children(pid)
                        print 'Distl timed out.'   
                        self.logger.debug('Distl timed out.')                   
                        self.pixel_log.append('Distl timed out\n')
                        break                                   
                       
            readlog = open('distl.txt','r')
            for line in readlog:
                self.pixel_log.append(line)
                self.logger.debug(line.rstrip())
            readlog.close()                    
        
        except:
            self.logger.exception('**Error in multiDistl.**')
                                               
        distl = self.ParseOutputDistl(self.pixel_log)        
        self.distl_results = { 'Distl results'     : distl    }
        if self.distl_results['Distl results'] == None:
            self.distl_results = { 'Distl results'     : 'FAILED'}
                
    def postprocess(self):
        """
        Things to do after the main process runs
        1. Return the data through the pipe
        """
        self.logger.debug('QuickAnalysis::postprocess')
        #Run summary files for each program to print to screen                
        output           = {}                           
        #Put all the result dicts from all the programs run into one resultant dict and pass it along the pipe.
        try:
            #Results with missing stats set to 0
            results = {'saturation_50' : [0],
                       'total_signal' : [0]} 
            if self.distl_results:
                self.distl_results.update(results)
                self.input.append(self.distl_results)
            
            self.sendBack2(self.input)    
        
        except:
            self.logger.exception('**Could not send results to caller.**')

        #Say strategy is complete.
        self.logger.debug('-------------------------------------')
        self.logger.debug('RAPD Distl complete.')
        self.logger.debug('Total elapsed time: ' + str(os.times()[2]) + ' seconds')#Don't know if that is correct time?
        self.logger.debug('-------------------------------------')
        #Say strategy is complete.
        print '\n-------------------------------------'
        print 'RAPD Distl complete.'
        print 'Total elapsed time: ' + str(os.times()[2]) + ' seconds'#Don't know if that is correct time?
        print '-------------------------------------'
        
        #sys.exit(0) #did not appear to end script with some programs continuing on for some reason.
        os._exit(0)

    def PrintInfo(self):
        """
        Print information regarding programs utilized by RAPD
        """
        self.logger.debug('DiffractionCenter::PrintInfo')
        try:
            print '\nRAPD now using LABELIT'
            print '======================='
            print 'RAPD developed using Labelit version 1.1.7'
            print 'Reference:  J. Appl. Cryst. 39, 158-168 (2006)'
            print 'Website:    http://adder.lbl.gov/labelit/ \n'                       
            self.logger.debug('RAPD now using LABELIT')
            self.logger.debug('=======================')
            self.logger.debug('RAPD developed using Labelit version 1.1.7')
            self.logger.debug('Reference:  J. Appl. Cryst. 39, 158-168 (2006)')
            self.logger.debug('Website:    http://adder.lbl.gov/labelit/ \n')            
                        
        except:
            self.logger.exception('**Error in PrintInfo**')
    
    def still_running(self, pid):
        """
        Check to see if process and/or its children and/or children's children are still running.
        """
        parent = False
        child1 = False
        child2 = False
        c1 = []
        c2 = []            
        try:
            ppid = 'ps -F -A | grep ' + str(pid)        
            output = subprocess.Popen(ppid, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)        
            for line in output.stdout:
                junk = line.split()
                if junk[1] == str(pid):
                    parent = True
                if junk[2] == str(pid):
                    child1 = True
                    pid1 = junk[:][1]                
                    c1.append(pid1)
                    ppid2 = 'ps -F -A | grep ' + str(pid1)
                    output2 = subprocess.Popen(ppid2, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)        
                    for line in output2.stdout:
                        junk2 = line.split()
                        if junk2[2] == str(pid1):
                            child2 = True
                            pid2 = junk2[:][1]
                            c2.append(pid2)            
            if parent or child1 or child2:
                return(True)
            else:
                return(False)                            
        
        except:
            self.logger.exception('**Could not check if job was still running**')
    
    def kill_children(self, pid):
        """
        Kills the parent process, the children, and the children's children.
        """        
        parent = False
        child1 = False
        child2 = False
        c1 = []
        c2 = []            
        try:
            if self.test:
                os.chdir('/home/schuerjp/Data_processing/Frank/Output/')            
            ppid = 'ps -F -A | grep ' + str(pid)        
            output = subprocess.Popen(ppid, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)        
            for line in output.stdout:
                junk = line.split()
                if junk[1] == str(pid):
                    parent = True
                if junk[2] == str(pid):
                    child1 = True
                    pid1 = junk[:][1]                
                    c1.append(pid1)
                    ppid2 = 'ps -F -A | grep ' + str(pid1)
                    output2 = subprocess.Popen(ppid2, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)        
                    for line in output2.stdout:
                        junk2 = line.split()
                        if junk2[2] == str(pid1):
                            child2 = True
                            pid2 = junk2[:][1]
                            c2.append(pid2)                           
            if parent:  
                kill = 'kill -9 ' + str(pid)
                self.logger.debug(kill)
                os.system(kill)                
            if child1:
                for line in c1:
                    kill1 = 'kill -9 ' + line
                    self.logger.debug(kill1)                     
                    os.system(kill1)                
            if child2:
                for line in c2:
                    kill2 = 'kill -9 ' + line
                    self.logger.debug(kill2)            
                    os.system(kill2)
                
        except:
            self.logger.exception('Could not kill the children?!?')
        
    def ParseOutputDistl(self, input):     
        """
        parse distl.signal_strength
        """            
        try:    
            spot_total   = []
            spot_inres   = []
            good_spots   = []
            labelit_res  = []
            distl_res    = []
            max_cell     = []
            ice_rings    = []
            overloads    = []
            min          = []            
            max          = []            
            mean         = []                        
            signal_strength = False
            time_out = False
            for line in input:
                strip = line.strip()
                if strip.startswith('Distl timed out'):
                    time_out = True
                if strip.startswith('Spot Total'):
                    #spot_total = (strip.split())[3]
                    spot_total.append((strip.split())[3])
                if strip.startswith('In-Resolution Total'):
                    #spot_inres = (strip.split())[3]
                    spot_inres.append((strip.split())[3])
                if strip.startswith('Good Bragg'):
                    #good_spots = (strip.split())[4]
                    good_spots.append((strip.split())[4])
                if strip.startswith('Method 1'):
                    #labelit_res = (strip.split())[4]
                    labelit_res.append((strip.split())[4])
                if strip.startswith('Method 2'):
                    #distl_res = (strip.split())[4]
                    distl_res.append((strip.split())[4])
                if strip.startswith('Maximum unit cell'):
                    #max_cell = (strip.split())[4]
                    max_cell.append((strip.split())[4])
                if strip.startswith('Ice Rings'):
                    #ice_rings = (strip.split())[3] 
                    ice_rings.append((strip.split())[3])
                if strip.startswith('In-Resolution Ovrld Spots'):
                    #overloads = (strip.split())[4]
                    overloads.append((strip.split())[4])                                   
                if strip.startswith('Signals range'):
                    signal_strength = True
                    min.append(str(int(float((strip.split())[3]))))
                    max.append(str(int(float((strip.split())[5]))))
                    mean.append(str(int(float((strip.split())[10]))))                                
            if signal_strength == False:
                min.append('0')
                max.append('0')
                mean.append('0')  
            if time_out:
                distl = { 'total_spots'             : '0.0',
                          'in_res_spots'            : '0.0',
                          'good_b_spots'            : '0.0',
                          'distl_res'               : '0.0',
                          'labelit_res'             : '0.0',
                          'max_cell'                : '0.0',
                          'ice_rings'               : '0.0',
                          'overloads'               : '0.0',
                          'min_signal_str'          : '0.0',
                          'max_signal_str'          : '0.0',
                          'mean_int_signal'         : '0.0'      }
            else:
                #replace original code with MySQL db naes
                distl = { 'total_spots'             : spot_total,
                          'in_res_spots'            : spot_inres,
                          'good_b_spots'            : good_spots,
                          'distl_res'               : distl_res,
                          'labelit_res'             : labelit_res,
                          'max_cell'                : max_cell,
                          'ice_rings'               : ice_rings,
                          'overloads'               : overloads,
                          'min_signal_str'          : min,
                          'max_signal_str'          : max,
                          'mean_int_signal'         : mean      }                    
                #print distl        
            return ((distl))  
                            
        except:
            self.logger.exception('**Parsing distl.image_strength failed.**')
            return ((None))
                
def multiDistlAction(input, output, logger):
    """
    Get Distl stats for all images used to index at same time. Puts results in 'distl.txt' because of bug in 
    subprocess and stdout.
    """
    logger.debug('multiLabelitAction')
    try:
        log = []
        rm_file = 'rm -f distl.txt'
        logger.debug(rm_file)
        os.system(rm_file)
        junk = open('distl.txt','a')           
        command = 'distl.signal_strength ' + input[0]  
        logger.debug(command)                   
        myoutput = subprocess.Popen(command, shell=True, stdout=junk, stderr=junk)  
        junk.close()
        output.put(myoutput.pid)
        
    except:
        logger.exception('**Error in multiDistlAction**')


if __name__ == '__main__':
    #tag for log file
    #tag = os.path.basename(command).replace('rapdtmp','').replace('.json','')
    #start logging
    #LOG_FILENAME = '/home/schuerjp/Data_processing/Frank/Output/rapd_jon.log'
    LOG_FILENAME = '/tmp/rapd_agent_quickanalysis.log'
    # Set up a specific logger with our desired output level
    logger = logging.getLogger('RAPDLogger')
    logger.setLevel(logging.DEBUG)
    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=100000, backupCount=5)
    #add a formatter
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info('QuickAnalysis.__init__')    
    #construct test input    

    #call the handler
    #T = TestHandler(input, logger=logger)
    D = QuickAnalysisAction('./test_data/raster_snap_test_1_001.img','my_server',8125,logger)
    print D.output 
    
