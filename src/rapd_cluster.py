__author__ = "Frank Murphy"
__copyright__ = "Copyright 2009,2010,2011 Cornell University"
__credits__ = ["Frank Murphy","Jon Schuermann","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3-Clause"
__version__ = "0.9"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"
__date__ = "2009/07/10"

import socket
import threading
import multiprocessing
import subprocess
import json
import os
import time
import sys
import logging, logging.handlers
import getopt
import tempfile
#agents for performing actions
from rapd_site import secret_settings_general as secrets
from rapd_database import Database
from rapd_communicate import Communicate

buffer_size = 8192

#
# CLUSTER-SIDE CLASSES
#
class TestCase(multiprocessing.Process):
    """
    This is an example class for RAPD's data processing
    functions.
    
    __init__ is merely used to stow variables passed in,
    to initialize the process, and to start the process 
    
    run is used to orchestrate events
    """

    def __init__(self,command,pipe,logger):
        """
        Initialize the TestCase process
        
        input   is whatever is passed in
        pipe    is the communication back to the calling process
        """
        logger.debug('TestCase::__init__')
            
        self.command = command
        self.pipe    = pipe
        self.logger  = logger
        
        #this is where I have chosen to place my results
        self.results = False
        
        multiprocessing.Process.__init__(self,name='TestCase')
        
        #starts the new process
        self.start()
        
    def run(self):
        self.logger.debug('TestCase::run')

        self.preprocess()
        self.process()
        self.postprocess()
        
    def preprocess(self):
        """
        Things to do before the main process runs
        1. Change to the correct directory
        2. Print out the reference for labelit
        """
        self.logger.debug('TestCase::preprocess')
            
        #change directory to the one specified in the incoming dict
        os.chdir(self.command[1])
        self.PrintInfo()
            
    def process(self):
        """
        The main process
        1. Construct the labelit command
        2. Run labelit, grabbing the outout
        3. Parse the labelit output
        """
        self.logger.debug('TestCase::process')
            
        #put together the command for labelit.index
        command = 'labelit.index ' + self.command[3]['FULLNAME']
        
        #run Labelit and capture the log file
        try:
            self.logger.debug(command)
            output = os.popen(command).readlines()
            for line in output:
                self.logger.debug(line.rstrip())
        except IOError:
            #Try up to 5 times in total
            self.logger.exception('Labelit exception')

        #now parse the output
        output,solution,data = self.ParseOutput(output)
        
        #put the gathered data into a dict for return
        self.results = { 'fullname' : self.command[3]['FULLNAME'],       #for potential error checking
                         'output'   : output,
                         'solution' : solution,
                         'data'     : data }
    
    def postprocess(self):
        """
        Things to do after the main process runs
        1. Return the data throught the pipe
        """
        self.logger.debug('TestCase::postprocess')

        #send the results back to the TestHandler via the passed-in pipe
        self.pipe.send(self.results)
        
        
    def PrintInfo(self):
        """
        Print information regarding programs utilized by RAPD
        """
        self.logger.debug('\nRAPD now using LABELIT')
        self.logger.debug('=======================')
        self.logger.debug('RAPD developed using labelit version 1.000rc8')
        self.logger.debug('Reference:  J. Appl. Cryst. 39, 158-168 (2006)')
        self.logger.debug('Website:    http://adder.lbl.gov/labelit/ \n')
        
    def ParseOutput(self, input):
        """
        cleans up the output AND looks for best solution
        passes info back to caller
        """
        self.logger.debug('TestCase::ParseOutput')
            
        tmp = []
        correct_pos = -1
        results_pos = -1
        self.max_cell = 0
        #Root out extra carrige returns
        for line in input:
            line.rstrip()
            if len(line) >1:
                tmp.append(line[:-1])
                #grab out the unit cell dimension maximum (for DENZO use)
                if line.startswith(':)'):
                    split_line = line.split()
                    if len(split_line) == 15:
                        for i in [8,9,10]:
                            if float(split_line[i]) > self.max_cell:
                                self.max_cell = float(split_line[i])
                                
        tmp = []
        #find special points
        for i in range(len(input)):
            if input[i].startswith('Correcting'): correct_pos = i
            if input[i].find('Indexing results') != -1:
                results_pos = i
                break
        if correct_pos != -1:
            tmp.append('LABELIT has adjusted the direct beam position')
            tmp.append(input[correct_pos][:-1])
        if results_pos != -1:
            for i in input[results_pos:]:
                if len(i) > 1:
                    tmp.append(i[:-1])
        else:
            for i in input:
                if len(i) > 1:
                    tmp.append(i[:-1])

        #find the 'best' solution somewhat blindly
        solution = -1
        solution1_pos = -1
        for i in range(len(tmp)):
            if tmp[i].find('Solution') != -1:
                if solution1_pos != -1:
                    solution = i + 1    
                    break
                else:
                    solution1_pos = i + 1
                    solution = i + 1
        try:
            pieces = tmp[solution][2:].split()
            self.space_group = str(pieces[1])
            self.x_beam       = float(pieces[2])
            self.y_beam       = float(pieces[3])
            self.distance    = float(pieces[4])
            self.resolution  = float(pieces[5])
            self.mosaicity   = float(pieces[6])
            self.output      = tmp[:]
            data = { 'space_group' : self.space_group,
                     'x_beam'       : self.x_beam,
                     'y_beam'       : self.y_beam,
                     'distance'    : self.distance,
                     'resolution'  : self.resolution,
                     'mosaicity'   : self.mosaicity,
                     'max_cell'    : self.max_cell }
            return((tmp,solution,data))
        except:
            self.logger.exception('Labelit finds no reasonable solution')
            return((tmp, None, None))
        
        
class EchoCase(multiprocessing.Process):
    """
    An action class which only echos the input data back
    """

    def __init__(self,command,pipe,logger):
        """
        Initialize the TestCase process
        
        input   is whatever is passed in
        pipe    is the communication back to the calling process
        """
        logger.info('EchoCase::__init__')
            
        self.command = command
        self.pipe    = pipe
        self.logger  = logger
        
        #this is where I have chosen to place my results
        self.results = False
        
        multiprocessing.Process.__init__(self,name='TestCase')
        
        #starts the new process
        self.start()
        
    def run(self):
        self.logger.debug('EchoCase::run')

        self.preprocess()
        self.process()
        self.postprocess()
        
    def preprocess(self):
        """
        Things to do before the main process runs
        1. Change to the correct directory
        2. Print out the reference for labelit
        """
        self.logger.debug('EchoCase::preprocess')
            
    
    def process(self):
        """
        The main process
        1. Construct the labelit command
        2. Run labelit, grabbing the outout
        3. Parse the labelit output
        """
        self.logger.debug('EchoCase::process')
            
        #put the gathered data into a dict for return
        self.results = self.command
        self.results.append('EchoCase')
    
    def postprocess(self):
        """
        Things to do after the main process runs
        1. Return the data throught the pipe
        """
        self.logger.debug('EchoCase::postprocess')
        self.logger.debug(self.results)

        #send the results back to the TestHandler via the passed-in pipe
        self.pipe.send(self.results)


class ClusterServer:
    """
    Runs the socket server and spawns new threads when connections are received
    """
    def __init__(self,mode='server'):
        """
        The main server thread
        """
        #set up logging
        if os.path.exists(secrets['cluster_logfile_dir']):
            LOG_FILENAME = os.path.join(secrets['cluster_logfile_dir'],'rapd_cluster.log')
        else:
            LOG_FILENAME = '/tmp/rapd_cluster.log'
            
        # Set up a specific logger with our desired output level
        logger = logging.getLogger('RAPDLogger')
        logger.setLevel(logging.DEBUG)
        # Add the log message handler to the logger
        handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=100000, backupCount=5)
        #add a formatter
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.info('RAPD_CLUSTER.__init__')

        #store logging and verbosity
        self.logger  = logger
        
        #save the mode
        self.mode = mode
        
        #create databse connection
        self.DATABASE = Database(settings=secrets,
                                 logger=self.logger)

        #tell the database we are alive
        self.StatusHandler = StatusHandler(db=self.DATABASE,
                                           logger=self.logger)

        HOST = ''                 # Symbolic name meaning all available interfaces
        PORT = secrets['cluster_port']         # Arbitrary non-privileged port
        
        self.logger.debug('ClusterServer running in mode %s on port %d' % (self.mode,PORT))
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST,PORT)) 
    
        #This is the "server"
        while(1):
            s.listen(5)
            try:
                conn, addr = s.accept()
                tmp = Handler(conn=conn,
                              addr=addr,
                              db=self.DATABASE,
                              mode = self.mode,
                              logger=self.logger)
            except:
                self.logger.exception('Error in cluster server')
    
        #if we exit...
        s.close()
        
class StatusHandler(threading.Thread):
    """
    Handles logging of life for the cluster
    """
    def __init__(self,db=None,logger=None):
        logger.info('StatusHandler::__init__')
        
        #initialize the thread
        threading.Thread.__init__(self)

        self.DATABASE   = db
        self.logger     = logger
        
        #obtain self ip address
        self.ip_address = socket.gethostbyaddr(socket.gethostname())[-1][0]
        
        #start the thread
        self.start() 

    def run(self):
        self.logger.debug('StatusHandler::run')
        while (1):
            self.DATABASE.updateClusterStatus(self.ip_address)
            time.sleep(30)

class Handler(threading.Thread,Communicate):
    """
    Handles the data that is received from the incoming clientsocket on the cluster
    
    Creates a new process by instantiating a subclassed multiprocessing.Process
    instance which will act on the information which is passed to it upon
    instantiation. That class will then send back results on the pipe 
    which it is passed and Handler will send that up the clientsocket.
    """
    def __init__(self,conn,addr,db=None,mode='server',command=None,queue=None,logger=None):
        logger.info('Handler::__init__')
        
        #initialize the thread
        threading.Thread.__init__(self)

        #store the connection variable
        self.conn     = conn
        self.addr     = addr
        self.DATABASE = db
        self.mode     = mode        #server,qsub or file
        self.command  = command
        self.queue    = queue       #the SGE queue to be submitted to
        self.logger   = logger
        
        
        #start the thread
        self.start() 

    def run(self):
        self.logger.debug('Handler::run')

        #if we are looking at a socket connection for the incoming message
        if not (self.mode=='file'):
            #read the message from the socket
            message = ''
            while not (message.endswith('<rapd_end>')):
                data = self.conn.recv(buffer_size)
                message += data
                time.sleep(0.001)
            #close the connection
            self.conn.close()
            #strip the message of its delivery tags
            message = message.rstrip().replace('<rapd_start>','').replace('<rapd_end>','')
            
        #The ClusterServer is spawning processes on a central node
        if (self.mode == 'server'):
            #strip out extra spaces and decode json
            command = json.loads(message)
            self.controller_address = tuple(command[-1])
            #feedback
            self.logger.debug(command)
            #assign the command
            self.Assign(command)
        
        #qsub is being used to spawn commands
        elif (self.mode == 'qsub'):
            self.logger.debug('Creating files for qsub submission')
            #The type of command
            b = message[:]
            command = json.loads(b)[0]
            if (len(command)>3):
                tag = command[:4]
            else:
                tag = command
            
            #write the command to a file
            tmp = tempfile.NamedTemporaryFile(mode='w',
                                              dir='./',
                                              prefix='rapd_'+tag+'-',
                                              suffix='.json',
                                              delete=False)
            tmp.write(message)
            tmp.close()
            
            #now prep the qsub command
            qsub_name = os.path.basename(tmp.name).replace('rapd_','').replace('.json','')
            #handle a queueing system
            if (self.queue):
                self.logger.debug('Submit %s to qsub %s'%(tmp.name,self.queue))
                p = subprocess.Popen("qsub -cwd -V -P "+self.queue+" -b y -l h_rt=3:00:00 -N "+qsub_name+" python2.6 rapd_cluster.py "+tmp.name,shell=True)
            else:
                self.logger.debug('Submit %s to qsub'%tmp.name)
                p = subprocess.Popen("qsub -cwd -V -b y -l h_rt=3:00:00 -N "+qsub_name+" python2.6 rapd_cluster.py "+tmp.name,shell=True)
            sts = os.waitpid(p.pid, 0)[1]
        
        #A command is being received from a file
        elif (self.mode == 'file'):
            self.logger.debug('File has been submitted to run')
            #feedback
            self.logger.debug(self.command)
            #store the reply to server's address
            self.controller_address = tuple(self.command[-1])
            #assign the command
            self.Assign(self.command)
                
    def Assign(self,command,mode='server'):
        """
        Decides what should be done based on the data and then:
        1. creates pipes
        2. starts the class which performs the proper task
        3. sends the resulting data back over the socket
        """
        self.logger.debug('Handler::Assign command = %s' %command)        
        
        #launch the new process
        try:
            if command[0] == 'AUTOINDEX':
                self.logger.debug('command = AUTOINDEX')
                from rapd_agent_strategy import AutoindexingStrategy as Autoindex
                tries = 0
                while(tries<5):
                    try:
                        tmp = Autoindex(input=command[:],
                                        logger=self.logger)
                        break
                    except:
                        tries += 1
                        if (tries == 5):
                            self.logger.exception('Failure to create a new process')
                            self.sendBack2(reply='ERROR')
                            return()
                            
            elif command[0] == 'AUTOINDEX-PAIR':
                self.logger.debug('command = AUTOINDEX-PAIR')
                from rapd_agent_strategy import AutoindexingStrategy as Autoindex
                tries = 0
                while(tries<5):
                    try:
                        tmp = Autoindex(input=command[:],
                                        logger=self.logger)
                        break
                    except:
                        tries += 1
                        if (tries == 5):
                            self.logger.exception('Failure to create a new process')
                            self.sendBack2(reply='ERROR')
                            return()
                        
            elif command[0] == 'STAC':
                self.logger.debug('command = STAC')
                from rapd_agent_strategy import AutoindexingStrategy as Autoindex
                tries = 0
                while(tries<5):
                    try:
                        tmp = Autoindex(input=command[:],
                                        logger=self.logger)
                        break
                    except:
                        tries += 1
                        if (tries == 5):
                            self.logger.exception('Failure to create a new process')
                            self.sendBack2(reply='ERROR')
                            return()
                            
            elif command[0] == 'STAC-PAIR':
                self.logger.debug('command = STAC-PAIR')
                from rapd_agent_strategy import AutoindexingStrategy as Autoindex
                tries = 0
                while(tries<5):
                    try:
                        tmp = Autoindex(input=command[:],
                                        logger=self.logger)
                        break
                    except:
                        tries += 1
                        if (tries == 5):
                            self.logger.exception('Failure to create a new process')
                            self.sendBack2(reply='ERROR')
                            return()

            elif command[0] in ('XDS','XIA2'):
                self.logger.debug('command = REINTEGRATE')
                from rapd_agent_reintegrate import ReIntegration
                tries = 0
                while(tries<5):
                    try:
                        tmp = ReIntegration(input=command[:],
                                            logger=self.logger)
                        break
                    except:
                        tries += 1
                        if (tries == 5):
                            self.logger.exception('Failure to create a new process')
                            self.sendBack2(reply='ERROR')
                            return()
                        
            elif command[0] == 'INTEGRATE':
                self.logger.debug('command = INTEGRATE')
                from rapd_agent_fast_integration import FastIntegration as Integrate
                tries = 0
                while(tries<5):
                    try:
                        tmp = Integrate(input=command[:],
                                        logger=self.logger)
                        break
                    except:
                        tries += 1
                        if (tries == 5):
                            self.logger.exception('Failure to create a new process')
                            self.sendBack2(reply='ERROR')
                            return()
                        
            #SAD Structure Solution
            elif command[0] == 'SAD':
                self.logger.debug('command = SAD')
                from rapd_agent_sad import AutoSolve as Sad
                tries = 0
                while(tries<5):
                    try:
                        tmp = Sad(input=command[:],
                                  logger=self.logger)
                        break
                    except:
                        tries += 1
                        if (tries == 5):
                            self.logger.exception('Failure to create a new process')
                            self.sendBack2(reply='ERROR')
                            return()
                        
            #Molecular Replacement
            elif command[0] == 'MR':
                self.logger.debug('command = MR')
                from rapd_agent_mr import AutoMolRep as MR
                tries = 0
                while(tries<5):
                    try:
                        tmp = MR(input=command[:],
                                 logger=self.logger)
                        break
                    except:
                        tries += 1
                        if (tries == 5):
                            self.logger.exception('Failure to create a new process')
                            self.sendBack2(reply='ERROR')
                            return()
                        
            #simple pair-wise dataset merging
            elif command[0] == 'SMERGE':
                self.logger.debug('command = SMERGE')
                from rapd_agent_simplemerge import SimpleMerge
                tries = 0
                while(tries<5):
                    try:
                        tmp = SimpleMerge(input=command[:],
                                          logger=self.logger)
                        break
                    except:
                        tries += 1
                        if (tries == 5):
                            self.logger.exception('Failure to create a new process')
                            self.sendBack2(reply='ERROR')
                            return()
            
            #Diffraction-based centering agent           
            elif command[0] == 'DIFF_CENTER':
                self.logger.debug('command = DIFF_CENTER')
                from rapd_agent_diffcenter import DiffractionCenter
                tries = 0
                while(tries<5):
                    try:
                        tmp = DiffractionCenter(input=command[:],
                                                logger=self.logger)
                        break
                    except:
                        tries += 1
                        if (tries == 5):
                            self.logger.exception('Failure to create a new DiffractionCenter process')
                            self.sendBack2(reply='ERROR')
                            return()

            #Snapshot-based quick analysis agent           
            elif command[0] == 'QUICK_ANALYSIS':
                self.logger.debug('command = QUICK_ANALYSIS')
                from rapd_agent_quickanalysis import QuickAnalysis
                tries = 0
                while(tries<5):
                    try:
                        tmp = QuickAnalysis(input=command[:],
                                            logger=self.logger)
                        break
                    except:
                        tries += 1
                        if (tries == 5):
                            self.logger.exception('Failure to create a new QuickAnalysis process')
                            self.sendBack2(reply='ERROR')
                            return()

            elif command[0] == 'TEST':
                self.logger.debug('TEST')
                self.sendBack2(reply='TEST')
                return()

            elif command[0] == 'DOWNLOAD':
                self.logger.debug('DOWNLOAD')
                from rapd_agent_download import Download
                tries = 0
                while(tries<5):
                    try:
                        tmp = Download(input=command[:],
                                       logger=self.logger)
                        break
                    except:
                        tries += 1
                        if (tries == 5):
                            self.logger.exception('Failure to create a new process')
                            self.sendBack2(reply='ERROR')
                            return()

            else:
                self.logger.debug('UNKNOWN COMMAND %s' % command)
                self.sendBack2('ERROR')
                return()
        
        except:
            self.logger.exception('Exception in Handler::Assign command = %s' %command)
            self.sendBack2(reply='ERROR')
            return()

    def sendBack(self,reply):
        """
        Send stuff back over the socket
        """
        self.logger.debug('Handler::sendBack')
        
        #connect
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(self.controller_address)
        except:
            self.logger.exception('Failed to initialize socket to controller')
            sys.exit()
        
        #bulk out the command
        message = '<rapd_start>' + reply + '<rapd_end>'
        #now send
        total_sent = 0
        while (total_sent < len(message)):
            sent = s.send(message)
            total_sent += sent
        
        self.logger.debug('Total sent: %d' % total_sent)
           
        #close the socket connection 
        s.close()
           
class ControllerHandler(threading.Thread):  
    """
    Handles the data that is received from the cluster via incoming client socket
    """
    def __init__(self,conn,addr,receiver,logger=None):
        logger.info('ControllerHandler::__init__')
        
        #initialize the thread
        threading.Thread.__init__(self)
        #store the connection variable
        self.conn     = conn
        self.addr     = addr
        self.receiver = receiver
        self.logger   = logger
        #start the thread
        self.start() 

    def run(self):
        self.logger.debug('ControllerHandler::run')

        #Receive the output back from the cluster
        message = '' 
        while not (message.endswith('<rapd_end>')):
            data = self.conn.recv(buffer_size)
            message += data
            time.sleep(0.001)
        self.conn.close()
        #strip off the start and end markers
        stripped = message.rstrip().replace('<rapd_start>','').replace('<rapd_end>','')
        #load the JSON 
        decoded_received = json.loads(stripped)
        #feedback
        #self.logger.debug(decoded_received)
        #assign the command
        self.receiver(decoded_received)

###############################################################################
# CLIENT-SIDE CLASSES
###############################################################################
class ControllerServer(threading.Thread):
    """
    Runs the socket server and spawns new threads when connections are received
    """
    def __init__(self,receiver,port,logger):
        """
        The main server thread
        """
        logger.info('Controller_Server::__init__')

        #initialize the thred
        threading.Thread.__init__(self)

        #store passed-in variables
        self.receiver  = receiver
        self.port      = port
        self.logger    = logger
        
        self.Go = True

        #start it up
        self.start()

    def run(self):

        HOST = ''                 # Symbolic name meaning all available interfaces
    
        #create the socket listener
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST,self.port)) 
    
        #This is the "server"
        while(self.Go):
            #print 'listening'
            s.listen(5)
            conn, addr = s.accept()
            tmp = ControllerHandler(conn=conn,addr=addr,receiver=self.receiver,logger=self.logger)
    
        #if we exit...
        s.close()
           
    def Stop(self):
        self.Go = False


class PerformAction(threading.Thread):
    """
    Manages the dispatch of jobs to the cluster process
    NB that the cluster can be on the localhost or a remote host
    """
    def __init__(self,command,settings,secret_settings,logger):
        logger.info('PerformAction::__init__  command:%s' % str(command))
        
        #initialize the thread
        threading.Thread.__init__(self)
        
        #store passed-in variable
        self.command = command
        
        #Decide on what cluster to use
        if (secret_settings['cluster_strategy'] and (command[0] in ('AUTOINDEX','AUTOINDEX-PAIR'))):
            self.HOST = secret_settings['cluster_strategy']
        elif ((secret_settings['cluster_stac']) and (command[0] in ('STAC','STAC-PAIR'))):
             self.HOST = secret_settings['cluster_stac']
        elif ((secret_settings['cluster_integrate']) and (command[0] in ('INTEGRATE','XIA2'))):
            self.HOST = secret_settings['cluster_integrate']
        else:
            self.HOST    = secret_settings['cluster_host']

        self.PORT    = secret_settings['cluster_port']
        self.logger  = logger
        self.logger.debug('Connecting to: %s:%d' %(self.HOST,self.PORT)) 
        self.start()
        
    def run(self):
        self.logger.debug('PerformAction::run')
        
        attempts = 0
        
        while(attempts < 100):
            attempts += 1
            self.logger.debug('Cluster connection attempt %d' % attempts)
            #connect
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((self.HOST, self.PORT))
                break
            except:
                self.logger.exception('Failed to initialize socket to cluster')
                time.sleep(15)
        else:
            sys.exit()
                
        #encode the command
        message = json.dumps(self.command)
        message = '<rapd_start>' + message + '<rapd_end>'
        #print message
        #now send
        total_sent = 0
        while (total_sent < len(message)):
            sent = s.send(message)
            total_sent += sent
        
        self.logger.debug('total_sent: %d' % total_sent)
            
        s.close()

def get_command_line():
    """
    Get command line for runs
    """ 
    queue = False
       
    try:
        opts,args = getopt.getopt(sys.argv[1:],"vq:",)
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        sys.exit(2)
        
    for o,a in opts:
        if (o == '-q'):
            queue = a
    if (len(args) == 0):
        return('server',queue)
    else:
        return(args[0],queue)


def main():
    
    command,queue = get_command_line()
    
    #spawn processes on this node
    if (command == 'server'):
        Server = ClusterServer(mode='server')
    #spawn qsub commands
    elif (command == 'qsub'):
        Server = ClusterServer(mode='qsub')
    #run command file
    else:
        #tag for log file
        tag = os.path.basename(command).replace('rapd_','').replace('.json','')
        #start logging
        if os.path.exists(secrets['cluster_logfile_dir']):
            LOG_FILENAME = os.path.join(secrets['cluster_logfile_dir'],'rapd_cluster_'+tag+'.log')
        else:
            LOG_FILENAME = '/tmp/rapd_cluster_'+tag+'.log'
        # Set up a specific logger with our desired output level
        logger = logging.getLogger('RAPDLogger')
        logger.setLevel(logging.DEBUG)
        # Add the log message handler to the logger
        handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=10000000, backupCount=5)
        #add a formatter
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.info('RAPD_CLUSTER.main')
        logger.debug('Starting in directory %s' % os.getcwd())
        
        command_file = open(command,'r')
        my_command = json.load(command_file)
        
        my_handler = Handler(conn=None,addr=None,db=None,mode='file',command=my_command,queue=queue,logger=logger)   
         

if __name__ == '__main__':
    
    main()

