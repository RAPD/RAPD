__author__ = "Frank Murphy"
__copyright__ = "Copyright 2009,2010,2011 Cornell University"
__credits__ = ["Frank Murphy","Jon Schuermann","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3-Clause"
__version__ = "0.9"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"
__date__ = "2009/07/08"

#standard imports
import os
import sys
import threading
import time
import socket
import collections
import datetime
import exceptions

#custom RAPD imports
from rapd_beamlinespecific    import *
from rapd_database            import Database
from rapd_cluster             import PerformAction, ControllerServer
from rapd_cloud               import CloudMonitor
from rapd_agent_diffcenter    import DiffCenterAction
from rapd_agent_quickanalysis import QuickAnalysisAction

#####################################################################
# The main Model Class                                              #
#####################################################################
class Model:
    """
    Main controlling code for the CORE.
    
    This is really more than just a model, probably model+controller.
    Coordinates the monitoring of data collection and the "cloud", 
    as well as the running of processes and logging of all metadata
    
    """
    
    def __init__(self,beamline,logger):
        """
        Save variables and call InitSettings.
        
        beamline - beamline designation that syncs with rapd_site beamlines
        logger - a logger instance - required
        """
        
        logger.info('Model::__init__')
        
        #passed-in variables
        self.beamline = beamline
        self.logger   = logger 
        
        # Initialize the settings from rapd_beamlinespecific
        self.InitSettings()

    def InitSettings(self):
        """
        Initialize a number of variables and read in the settings from rapd_beamlinespecific.
        """
        
        self.logger.debug('Model::InitSettings  beamline: %s' % self.beamline)
            
        #set up the queue for keeping track of image pairs
        self.pair    = collections.deque(['',''],maxlen=2)
        self.pair_id = collections.deque(['',''],maxlen=2)
        
        #queues for managing processes - this control will be moved in the future
        #the queue for controlling simultaneous image processing
        self.indexing_queue = collections.deque()
        self.indexing_active = collections.deque()
        #the queue system for managing diffraction-based centering
        self.diffcenter_queue = collections.deque()
        self.diffcenter_active = collections.deque()
        #the queue system for managing snapshot-based analysis
        self.quickanalysis_queue = collections.deque()
        self.quickanalysis_active = collections.deque()
        
        #set the defaults
        try:
            #grab the settings from the rapd_site.py file
            if self.beamline in beamline_settings.keys():
                self.Settings = beamline_settings[self.beamline].copy()
                self.SecretSettings = secret_settings[self.beamline].copy()
            else:
                self.logger.debug('must be a test beamline')
                self.Settings                   = beamline_settings['T'].copy()
                self.Settings['beamline']       = self.beamline
                self.SecretSettings             = secret_settings['T'].copy()
                self.SecretSettings['beamline'] = self.beamline
        
            #determine the current ip address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('google.com', 0))
            self.ip_address = s.getsockname()[0]
            s.close()
            self.socket     = self.SecretSettings['controller_port']

            #save starting directory position
            self.start_dir = os.getcwd()
            
            #the current data_root_dir (The base directory for user data collection for a trip
            self.data_root_dir = None
            self.Settings['data_root_dir'] = 'DEFAULTS'
            self.Settings['setting_type'] = 'GLOBAL'
                    
            # Interfaces to more complicated actors - mainly NULL until we start
            #set up database interface 
            self.DATABASE = Database(settings=self.SecretSettings,
                                     logger=self.logger)
            #update the DEFAULTS settings based on the data in rapd_site.py
            self.DATABASE.addSettings(settings=self.Settings)
            
            #watches as runs are collected
            self.RUNWATCHERS = []
            
            #Server for receiving information from the cluster
            self.SERVER = False
            
            #watches for new collected images
            self.IMAGEMONITOR = False
            self.imagemonitor_reconnect_attempts = 0
            
            #watches the cloud requests
            self.CLOUDMONITOR = False
            
            #let them know we have success
            self.logger.debug('Model initialized')
        
        except:
            self.logger.exception('FATAL ERROR - this beamline is proably not in the default settings table - edit rapd_beamlinespecific.py to rectify before restarting')
            sys.exit()

    def Start(self):
        """
        Start monitoring the beamline.
        """
        
        self.logger.debug('Model::Start')
        
        #start the server for cluster feedback
        try:
            self.SERVER = ControllerServer( receiver = self.Receive,
                                            port = self.socket,
                                            logger = self.logger )
        except:
            self.logger.exception('CATASTROPHIC ERROR - cannot start ControllerServer to receive cluster feedback')
            exit()
         
        #monitor for new images to be collected
        self.IMAGEMONITOR = ImageMonitor(beamline=self.beamline,
                                         notify=self.Receive,
                                         logger=self.logger) 
        
        #watch the cloud for requests
        if (self.SecretSettings['cloud_interval'] > 0.0):
            self.CLOUDMONITOR = CloudMonitor(database=self.DATABASE,
                                             settings=self.SecretSettings,
                                             reply_settings=(self.ip_address,self.socket),
                                             interval=self.SecretSettings['cloud_interval'],
                                             logger=self.logger)
        else:
            self.logger.debug('CLOUDMONITOR turned off')
        
        #start the status updating
        self.STATUSHANDLER = StatusHandler( db = self.DATABASE,
                                            ip_address = self.ip_address,
                                            data_root_dir = self.data_root_dir,
                                            beamline = self.beamline,
                                            dataserver_ip = self.SecretSettings['adsc_server'].split(':')[1][2:],
                                            cluster_ip = self.SecretSettings['cluster_host'],
                                            logger = self.logger)
        
        #test the cluster - is this necessary??
        PerformAction( command = ('TEST',(self.ip_address,self.socket)),
                       settings = self.Settings,
                       secret_settings = self.SecretSettings,
                       logger = self.logger )
        
    def Stop(self):
        """
        Stop the ImageMonitor,CloudMonitor and StatusRegistrar.
        """
        
        self.logger.info('Model::Stop')
        
        #the IMAGEMONITOR    
        try:
            if self.IMAGEMONITOR:
                self.IMAGEMONITOR.Stop()
                self.IMAGEMONITOR = False
        except:
            self.IMAGEMONITOR = False    
            
        #the CLOUDMONITOR
        try:
            if self.CLOUDMONITOR:
                self.CLOUDMONITOR.Stop()
                self.CLOUDMONITOR = False
        except:
            self.CLOUDMONITOR = False    
            
        #the STATUSREGISTRAR
        try:
            if self.STATUSREGISTRAR:
                self.STATUSREGISTRAR.Stop()
                self.STATUSREGISTRAR = False
        except:
            self.STATUSREGISTRAR = False  

    #################################################################
    # Handle a new image being recorded                             #
    #################################################################
    def AddImage(self,data):
        """
        Handle an image to be added to the database.
        
        The image is NOT presumed to be new, so it is checked against the database.
        There are several classes of images that are sorted out here:
            data - snaps and runs 
            diffcenter - used for diffraction-based centering
                         tag defined in rapd_site diffcenter_tag
            beamcenter - direct beam shots (not currently used)
                         tag defined in rapd_site beamcenter_tag
            quickanalysis - used for rastering crystals and running analysis
                            tag defined in rapd_site quickanalysis_tag
            ignore - image ignored
                     tag defined in rapd_site ignore_tag
        
        """
        
        self.logger.debug('Model::AddImage')
        self.logger.debug(data)
        
        #reset the reconnect attempts to 0 since we have connected
        self.imagemonitor_reconnect_attempts = 0
        
        #get the header information from the image
        if os.path.isfile(data['image_name']):
            header = GetImageHeader(data['image_name'],self.logger)
        
            #add the full name of the image as fullname
            header['fullname'] = data['image_name']
            header['adsc_number'] = data['adsc_number']
            
            #add partial pieces of the image name for ease of access later
            header['directory'] = os.path.dirname(data['image_name'])
            header['image_prefix'] = '_'.join(os.path.basename(data['image_name']).split('_')[:-2])
            header['run_number'] = os.path.basename(data['image_name']).split('_')[-2]
            header['image_number'] = data['image_name'].split('_')[-1].split('.')[0]
            
            #add the information derived from console server if needed
            if (not len(list(set(['md2_aperture','puck','sample','ring_mode','ring_cur']) & set(header.keys()))) == 5):
                try:
                    #create an instance of the beamline monitor
                    myBEAMLINEMONITOR = BeamlineConnect(beamline=self.beamline,
                                                        reconnect=None,
                                                        logger=self.logger)
                    
                    if not header.has_key('md2_aperture'):
                        header['md2_aperture'] = myBEAMLINEMONITOR.GetMD2ApertureDiameter()
                    if not header.has_key('puck'):
                        header['puck'] = myBEAMLINEMONITOR.GetPuck()
                    if not header.has_key('sample'):
                        header['sample'] = myBEAMLINEMONITOR.GetPosition()
                    if not header.has_key('ring_mode'):    
                        header['ring_mode'] = myBEAMLINEMONITOR.GetRingMode()
                    if not header.has_key('ring_cur'):   
                        header['ring_cur'] = myBEAMLINEMONITOR.GetRingCurrent()

                    #get rid of myBEAMLINEMONITOR
                    myBEAMLINEMONITOR.Stop()
                    del myBEAMLINEMONITOR
                    
                except:
                    self.logger.exception('Error in adding missing entries to header')
            
            #determine flux and beamsize information
            header = DetermineFlux(header_in=header,
                                   beamline=self.beamline,
                                   logger=self.logger)

            result,new = self.DATABASE.addImage(header)
            if result:
                #Determine type of image
                #DetermineImageType will take the dict that goes to addImage
                image_type = DetermineImageType(data=result,            #check
                                                logger=self.logger)
                if (image_type == 'data' and new == True):
                    self.NewDataImage(data=result)
                elif (image_type == 'diffcenter'):
                    self.NewDiffcenterImage(data=result)
                elif (image_type == 'beamcenter'):                      #check
                    pass
                elif (image_type == 'quickanalysis'):
                    self.NewQuickanalysisImage(data=result,
                                               test=False)
                elif (image_type == 'quickanalysis-test'):
                    self.NewQuickanalysisImage(data=result,
                                               test=True)
                elif (image_type == 'ignore'):
                    self.logger.debug("Ignoring %s"%result['fullname'])
        else:
            self.logger.warning('%s is not an available file' % data['image_name'])
    
    def NewDiffcenterImage(self,data):
        """
        Handle the fact that we have a new image for diffraction-based centering.
        
        This is a little different in that we make a call to a server directly
        instead of farming the command out via PerformAction.
            
        """
        
        self.logger.debug('Model::NewDiffcenterImage %s' % data['fullname'])
        
        try:
            dfa = DiffCenterAction(fullname=data['fullname'],
                                   server=secret_settings_general['diffcenter_server'],
                                   port=secret_settings_general['diffcenter_port'],
                                   logger=self.logger)
            #print dfa.output
            #write the file for CONSOLE
            if (dfa.output):
                dfa_dict = dfa.output.copy()
                dfa_dict['image_id'] = data['image_id']
                dfa_dict['sample_id'] = data['sample_id']
                TransferToBeamline(results=dfa_dict,
                                   type='DIFFCENTER')
        
                #add result to database
                result_db = self.DATABASE.addDiffcenterResult(dirs=False,
                                                              info=False,
                                                              settings=False,
                                                              results=dfa_dict)
            
                self.logger.debug('Added diffraction-based centering result: %s' % str(result_db))
                del(dfa)
            else:
                del(dfa)
                raise Exception
 
        #Exception in direct method - use rapd_cluster
        except:
            self.logger.exception('Error in diffcenter distl server method')

            #acquire the settings for this image
            my_settings = self.DATABASE.getCurrentSettings(beamline=self.beamline)

            #get the data_root_dir
            my_data_root_dir = os.path.dirname(data['fullname'])
            
            #construct the working directory
            my_toplevel_dir = self.start_dir
            my_typelevel_dir = 'diffcenter'                                                                                           
            my_datelevel_dir = datetime.date.today().isoformat()                                                                  
            my_sub_dir = os.path.basename(data['fullname']).replace('.img','')                                                    
            my_work_dir_candidate = os.path.join(my_toplevel_dir,my_typelevel_dir,my_datelevel_dir,my_sub_dir)                    
            #make sure this is an original directory                                                                              
            if os.path.exists(my_work_dir_candidate):                                                                             
                #we have already                                                                                                  
                self.logger.debug('%s has already been used, will add qualifier' % my_work_dir_candidate)                         
                for i in range(1,10000):                                                                                          
                    if not os.path.exists('_'.join((my_work_dir_candidate,str(i)))):                                              
                        my_work_dir_candidate = '_'.join((my_work_dir_candidate,str(i)))                                          
                        self.logger.debug('%s will be used for this image' % my_work_dir_candidate)                               
                        break                                                                                                     
                    else:                                                                                                         
                        i += 1                                                                                                    
            #now make the candidate the used dir                                                                                  
            my_work_dir = my_work_dir_candidate                                                                                                                                                                                                           
            #now package directories into a dict for easy access by worker class                                                  
            my_dirs = { 'work' : my_work_dir,                                                                                     
                        'data_root_dir' : my_data_root_dir }                                                                         
                                                                                                                                  
            #create a representation of the process for display                                                                   
            my_repr = my_sub_dir+'.img'
            
            #add the process to the database                
            process_id = self.DATABASE.addNewProcess( type = 'diffcenter',    
                                                      rtype = 'original', 
                                                      data_root_dir = 'None', 
                                                      repr = my_repr )  
            
            #add the ID entry to the data dict
            data.update({'ID':os.path.basename(my_work_dir),
                         'process_id':process_id,
                         'repr':my_repr})    
        
            if (len(self.diffcenter_active) >= 10):
                self.logger.debug('Adding diffraction-based centering to the queue')
                self.diffcenter_queue.appendleft((('DIFF_CENTER',my_dirs,data,my_settings,(self.ip_address,self.socket)),
                                                  my_settings,                                                                                        
                                                  self.SecretSettings,                                                                                
                                                  self.logger))                                                                                       
            else:
                                                                                                                                           
                #connect to the server and autoindex the single image
                self.logger.debug('less than ten processes active - run diffraction-based centering')
                self.diffcenter_active.append('diffcenter')
            
            PerformAction(command = ('DIFF_CENTER',my_dirs,data,my_settings,(self.ip_address,self.socket)),
                          settings = my_settings,
                          secret_settings = self.SecretSettings,
                          logger = self.logger)
            
    def NewQuickanalysisImage(self,data,test=False):
        """
        Handle the fact that we have a new image for snapshot-based analysis.
        
        This is a little different in that we make a call to a server instead of 
        farming the command out via PerformAction.
            
        """
        self.logger.debug('Model::NewQuickanalysisImage %s' % data['fullname'])
        try:
            qa = QuickAnalysisAction(fullname=data['fullname'],
                                     server=secret_settings_general['quickanalysis_server'],
                                     port=secret_settings_general['quickanalysis_port'],
                                     logger=self.logger)
            #print qa.output            
            #write the file for CONSOLE
            if (qa.output):
                if (test == True):
                    qa_dict = qa.output.copy()
                    qa_dict["outfile"] = self.SecretSettings['rastersnap_test_dat']
                    TransferToBeamline(results=qa_dict,
                                       type="QUICKANALYSIS-TEST")
                    return()
                else:
                    qa_dict = qa.output.copy()
                    qa_dict['image_id'] = data['image_id']
                    qa_dict['sample_id'] = data['sample_id']
                    TransferToBeamline(results=qa_dict,
                                       type='QUICKANALYSIS')
                    #add result to database
                    result_db = self.DATABASE.addQuickanalysisResult(dirs=False,
                                                                     info=False,
                                                                     settings=False,
                                                                     results=qa_dict)
                    self.logger.debug('Added quickanalysis result: %s' % str(result_db))
                    del(qa)
            else:
                del(qa)
                """
                PerformAction(command=('RESTART_QUICKANALYSIS',None,None,None,(self.ip_address,self.socket)),
                              settings=my_settings,
                              secret_settings=self.SecretSettings,
                              logger=self.logger)
                """
                raise exceptions.NameError("QuickanalysisServerDown")
 
        #Exception in direct method - use rapd_cluster
        except:
            self.logger.exception('Error in quickanalysis distl server method')

            #acquire the settings for this image
            my_settings = self.DATABASE.getCurrentSettings(beamline=self.beamline)

            #get the data_root_dir
            my_data_root_dir = os.path.dirname(data['fullname'])
            
            #construct the working directory
            my_toplevel_dir = self.start_dir
            my_typelevel_dir = 'quickanalysis'                                                                                           
            my_datelevel_dir = datetime.date.today().isoformat()                                                                  
            my_sub_dir = os.path.basename(data['fullname']).replace('.img','')                                                    
            my_work_dir_candidate = os.path.join(my_toplevel_dir,my_typelevel_dir,my_datelevel_dir,my_sub_dir)                    
            #make sure this is an original directory                                                                              
            if os.path.exists(my_work_dir_candidate):                                                                             
                #we have already                                                                                                  
                self.logger.debug('%s has already been used, will add qualifier' % my_work_dir_candidate)                         
                for i in range(1,10000):                                                                                          
                    if not os.path.exists('_'.join((my_work_dir_candidate,str(i)))):                                              
                        my_work_dir_candidate = '_'.join((my_work_dir_candidate,str(i)))                                          
                        self.logger.debug('%s will be used for this image' % my_work_dir_candidate)                               
                        break                                                                                                     
                    else:                                                                                                         
                        i += 1                                                                                                    
            #now make the candidate the used dir                                                                                  
            my_work_dir = my_work_dir_candidate                                                                                                                                                                                                           
            #now package directories into a dict for easy access by worker class                                                  
            my_dirs = { 'work' : my_work_dir,                                                                                     
                        'data_root_dir' : my_data_root_dir }                                                                         
                                                                                                                                  
            #create a representation of the process for display                                                                   
            my_repr = my_sub_dir+'.img'
            
            #add the process to the database                
            process_id = self.DATABASE.addNewProcess( type = 'quickanalysis',    
                                                      rtype = 'original', 
                                                      data_root_dir = 'None', 
                                                      repr = my_repr )  
            
            #add the ID entry to the data dict
            data.update({'ID':os.path.basename(my_work_dir),
                         'process_id':process_id,
                         'repr':my_repr})    
        
            if (len(self.quickanalysis_active) >= 10):
                self.logger.debug('Adding quickanalysis to the queue')
                self.quickanalysis_queue.appendleft((('QUICK_ANALYSIS',my_dirs,data,my_settings,(self.ip_address,self.socket)),
                                                     my_settings,                                                                                        
                                                     self.SecretSettings,                                                                                
                                                     self.logger))                                                                                       
            else:
                                                                                                                                           
                #connect to the server and autoindex the single image
                self.logger.debug('less than ten processes active - run quickanalysis')
                self.quickanalysis_active.append('quickanalysis')
            
            PerformAction(command = ('QUICK_ANALYSIS',my_dirs,data,my_settings,(self.ip_address,self.socket)),
                          settings = my_settings,
                          secret_settings = self.SecretSettings,
                          logger = self.logger)            

    
    def NewDataImage(self,data):
        """
        Handle the information that there is a new image in the database.
        
        There are several calsses of images:
            1. The image is standalone and will be autoindexed
            2. The image is one of a pair of images for autoindexing
            3. The image is first in a wedge of data collection
            4. The image is in the middle of a wedge of data collection
            5. The image is last in a wedge of data collection
        """
        
        self.logger.debug('Model::NewDataImage %s' % data['fullname'])
        
        #make access a little easier - transitioning to ue of image_id instead of fullname
        fullname = data['fullname']
        image_id = data['image_id']
        
        #acquire the settings for this image in case they have changed via the UI
        my_settings = self.DATABASE.getCurrentSettings(beamline=self.beamline)
                        
        #now derive the data_root_dir used by the web interface for so many things
        my_data_root_dir = GetDataRootDir(fullname=fullname,
                                          logger=self.logger)
        
        #check the data_root_dir to see if it is a new one
        if my_data_root_dir != self.data_root_dir:
            #reset the pucks since we are presumably a new user
            #this works in a NO-CONSOLE version of pucks
            self.DATABASE.resetPucks(beamline=self.beamline)
            
            #we have a new drd - check for a previous setting
            self.logger.debug('Data root directory has changed to %s' % my_data_root_dir)
            check = self.DATABASE.checkNewDataRootDirSetting(data_root_dir=my_data_root_dir,
                                                             beamline=self.beamline)       #this will be True if there was a preset, False if not
            if check:
                self.logger.debug('Found and will employ settings this new data root dir')
            self.data_root_dir = my_data_root_dir
            #new settings have been returned - use them
            if check:
                my_settings = check
            
        else:
            self.logger.debug('Data root directory is unchanged %s' % my_data_root_dir)
            #Update the current table in the database
            self.DATABASE.updateCurrent(my_settings)
        
        #header beam position settings will be overridden sometimes
        if (not float(my_settings['x_beam'])):
            #beam position is not overridden in settings by user - check site settings
            if (self.Settings['use_beam_formula']):
                #we are going to use the beam formula
                #old linear formula
                #my_settings['x_beam'] = self.Settings['beam_center_x_m'] * float(data['distance']) + self.Settings['beam_center_x_b']
                #my_settings['y_beam'] = self.Settings['beam_center_y_m'] * float(data['distance']) + self.Settings['beam_center_y_b']
                #new polynomial equation
                my_settings['x_beam'] = self.Settings['beam_center_x_m6'] * float(data['distance'])**6 + \
                                        self.Settings['beam_center_x_m5'] * float(data['distance'])**5 + \
                                        self.Settings['beam_center_x_m4'] * float(data['distance'])**4 + \
                                        self.Settings['beam_center_x_m3'] * float(data['distance'])**3 + \
                                        self.Settings['beam_center_x_m2'] * float(data['distance'])**2 + \
                                        self.Settings['beam_center_x_m1'] * float(data['distance']) + self.Settings['beam_center_x_b']
                my_settings['y_beam'] = self.Settings['beam_center_y_m6'] * float(data['distance'])**6 + \
                                        self.Settings['beam_center_y_m5'] * float(data['distance'])**5 + \
                                        self.Settings['beam_center_y_m4'] * float(data['distance'])**4 + \
                                        self.Settings['beam_center_y_m3'] * float(data['distance'])**3 + \
                                        self.Settings['beam_center_y_m2'] * float(data['distance'])**2 + \
                                        self.Settings['beam_center_y_m1'] * float(data['distance']) + self.Settings['beam_center_y_b']
                self.DATABASE.updateImageCBC(data['image_id'],my_settings['x_beam'],my_settings['y_beam'])
                self.logger.debug('Using calculated beam center of X: %6.2f  Y: %6.2f' % (my_settings['x_beam'],my_settings['y_beam'])) 

        #sample identification
        #this is a hack for getting sample_id into the images
        if (my_settings.has_key('puckset_id')):
            data = self.DATABASE.setImageSampleId(image_dict=data,
                                                  puckset_id=my_settings['puckset_id'])

        #check if the image is in a run
        #not in run = AUTOINDEX   
        run_id = self.DATABASE.inRun(image_id=image_id)
        if ((not run_id) and (data['collect_mode'] == 'SNAP')):                                                                                 #AUTOINDEX
            self.logger.debug('Image is standalone - autoindex')                                                                                #AUTOINDEX
                                                                                                                                                #AUTOINDEX                                                                                                                             #AUTOINDEX
            #add the image to self.pair                                                                                                         #AUTOINDEX
            self.pair.append(fullname.lower())                                                                                                          #AUTOINDEX
            self.pair_id.append(image_id)                                                                                                       #AUTOINDEX
                                                                                                                                                #AUTOINDEX                                                                                                                             #AUTOINDEX
            # Get the correct directory to run in                                                                                               #AUTOINDEX   
            # We should end up with top_level/2010-05-10/snap_99_001/                                                                           #AUTOINDEX
            #the top level                                                                                                                      #AUTOINDEX
            if my_settings['work_dir_override'] == 'False':                                                                                     #AUTOINDEX
                my_toplevel_dir = self.start_dir                                                                                                #AUTOINDEX
            else:                                                                                                                               #AUTOINDEX
                my_toplevel_dir = my_settings['work_directory']                                                                                 #AUTOINDEX   
                                                                                                                                                #AUTOINDEX
            #the type level                                                                                                                     #AUTOINDEX
            my_typelevel_dir = 'single'                                                                                                         #AUTOINDEX
                                                                                                                                                #AUTOINDEX
            #the date level                                                                                                                     #AUTOINDEX
            my_datelevel_dir = datetime.date.today().isoformat()                                                                                #AUTOINDEX
                                                                                                                                                #AUTOINDEX
            #the lowest level                                                                                                                   #AUTOINDEX
            my_sub_dir = os.path.basename(data['fullname']).replace('.img','')                                                                  #AUTOINDEX
                                                                                                                                                #AUTOINDEX
            #now join the three levels                                                                                                          #AUTOINDEX
            my_work_dir_candidate = os.path.join(my_toplevel_dir,my_typelevel_dir,my_datelevel_dir,my_sub_dir)                                  #AUTOINDEX
                                                                                                                                                #AUTOINDEX
            #make sure this is an original directory                                                                                            #AUTOINDEX
            if os.path.exists(my_work_dir_candidate):                                                                                           #AUTOINDEX
                #we have already                                                                                                                #AUTOINDEX
                self.logger.debug('%s has already been used, will add qualifier' % my_work_dir_candidate)                                       #AUTOINDEX
                for i in range(1,10000):                                                                                                        #AUTOINDEX
                    if not os.path.exists('_'.join((my_work_dir_candidate,str(i)))):                                                            #AUTOINDEX
                        my_work_dir_candidate = '_'.join((my_work_dir_candidate,str(i)))                                                        #AUTOINDEX
                        self.logger.debug('%s will be used for this image' % my_work_dir_candidate)                                             #AUTOINDEX
                        break                                                                                                                   #AUTOINDEX
                    else:                                                                                                                       #AUTOINDEX
                        i += 1                                                                                                                  #AUTOINDEX
            #now make the candidate the used dir                                                                                                #AUTOINDEX
            my_work_dir = my_work_dir_candidate                                                                                                 #AUTOINDEX
                                                                                                                                                #AUTOINDEX
                                                                                                                                                #AUTOINDEX
            #now package directories into a dict for easy access by worker class                                                                #AUTOINDEX
            my_dirs = { 'work' : my_work_dir,                                                                                                   #AUTOINDEX
                        'data_root_dir' : my_data_root_dir }                                                                                    #AUTOINDEX   
                                                                                                                                                #AUTOINDEX
            #create a representation of the process for display                                                                                 #AUTOINDEX
            my_repr = my_sub_dir+'.img'                                                                                                         #AUTOINDEX 
                                                                                                                                                #AUTOINDEX 
            #add the process to the database to display as in-process                                                                           #AUTOINDEX
            process_id = self.DATABASE.addNewProcess( type = 'single',                                                                          #AUTOINDEX
                                                      rtype = 'original',                                                                       #AUTOINDEX
                                                      data_root_dir = my_data_root_dir,                                                         #AUTOINDEX
                                                      repr = my_repr )                                                                          #AUTOINDEX
                                                                                                                                                #AUTOINDEX
            #add the ID entry to the data dict                                                                                                  #AUTOINDEX
            #Is this used at all?                                                                                                               #AUTOINDEX
            data.update( { 'ID' : os.path.basename(my_work_dir),                                                                                #AUTOINDEX
                           'process_id' : process_id,                                                                                           #AUTOINDEX
                           'repr' : my_repr } )                                                                                                 #AUTOINDEX
                                                                                                                                                #AUTOINDEX
            #If we are throttling autoindexing jobs                                                                                             #AUTOINDEX
            if (self.SecretSettings['throttle_strategy'] == True):                                                                              #AUTOINDEX
                #too many jobs already running - put this in the queue                                                                          #AUTOINDEX
                if (len(self.indexing_active) >= self.SecretSettings['active_strategy_limit']):                                                 #AUTOINDEX
                    self.logger.debug('Adding autoindex to the queue')                                                                          #AUTOINDEX
                    self.indexing_queue.appendleft((('AUTOINDEX',my_dirs,data,my_settings,(self.ip_address,self.socket)),                       #AUTOINDEX
                                                    my_settings,                                                                                #AUTOINDEX
                                                    self.SecretSettings,                                                                        #AUTOINDEX
                                                    self.logger))                                                                               #AUTOINDEX  
                #go ahead and run, place marker in the queue                                                                                    #AUTOINDEX
                else:                                                                                                                           #AUTOINDEX
                    #connect to the server and autoindex the single image                                                                       #AUTOINDEX
                    self.logger.debug('less than %s processes active - run autoindexing' % self.SecretSettings['active_strategy_limit'])        #AUTOINDEX                                                      #AUTOINDEX
                    self.indexing_active.append('autoindex')                                                                                    #AUTOINDEX
                    PerformAction(command=('AUTOINDEX',my_dirs,data,my_settings,(self.ip_address,self.socket)),                                 #AUTOINDEX
                                  settings=my_settings,                                                                                         #AUTOINDEX
                                  secret_settings=self.SecretSettings,                                                                          #AUTOINDEX
                                  logger=self.logger )                                                                                          #AUTOINDEX  
            #No throttling - go ahead and run                                                                                                   #AUTOINDEX
            else:                                                                                                                               #AUTOINDEX
                PerformAction(command=('AUTOINDEX',my_dirs,data,my_settings,(self.ip_address,self.socket)),                                     #AUTOINDEX
                              settings=my_settings,                                                                                             #AUTOINDEX
                              secret_settings=self.SecretSettings,                                                                              #AUTOINDEX
                              logger=self.logger )                                                                                              #AUTOINDEX
            #
            # WORK ON PAIRS OF IMAGES
            #
            #if the last two images have 'pair' in their name - look closer
            if 'pair' in self.pair[0] and self.pair[1]:                                                                                             #AUTOINDEX-PAIR
                self.logger.debug('Potentially a pair of images')                                                                                   #AUTOINDEX-PAIR
                #everything matches up to the image number                                                                                          #AUTOINDEX-PAIR
                if (self.pair[0] != self.pair[1]) & (self.pair[0][:-8] == self.pair[1][:-8]):                                                       #AUTOINDEX-PAIR
                    self.logger.info('This looks like a pair to me: %s, %s' % (self.pair[1],self.pair[0]))                                          #AUTOINDEX-PAIR
                                                                                                                                                    #AUTOINDEX-PAIR
                    #get the data for the first image                                                                                               #AUTOINDEX-PAIR 
                    data1 = self.DATABASE.getImageByImageID( image_id = self.pair_id[0] )                                                           #AUTOINDEX-PAIR
                    #make a copy of the second pair to be LESS confusing                                                                            #AUTOINDEX-PAIR
                    data2 = data.copy()                                                                                                             #AUTOINDEX-PAIR
                                                                                                                                                    #AUTOINDEX-PAIR
                    #make sure we are looking at an increment of one                                                                                #AUTOINDEX-PAIR
                    if (not data1['image_number']+1 == data2['image_number']):                                                                      #AUTOINDEX-PAIR
                        return()                                                                                                                    #AUTOINDEX-PAIR
                    #make sure the puck address is the same for both image
                    """
                    This is commented out as the beamline is erroneously assigning smple numbers                                                    #AUTOINDEX-PAIR
                    if (not (data1['puck'],data1['sample']) == (data2['puck'],data2['sample'])):                                                    #AUTOINDEX-PAIR
                        return()                                                                                                                    #AUTOINDEX-PAIR
                    """                                                                                                                             #AUTOINDEX-PAIR
                    # Derive some directory names                                                                                                   #AUTOINDEX-PAIR
                    # my_toplevel_dir & my_datelevel_dir should already be current                                                                  #AUTOINDEX-PAIR
                    #the type level                                                                                                                 #AUTOINDEX-PAIR
                    my_typelevel_dir = 'pair'                                                                                                       #AUTOINDEX-PAIR
                                                                                                                                                    #AUTOINDEX-PAIR
                    #the lowest level                                                                                                               #AUTOINDEX-PAIR
                    my_sub_dir = '_'.join((data1['image_prefix'],str(data1['run_number']),'+'.join((str(data1['image_number']).lstrip('0'),str(data2['image_number']).lstrip('0')))))
                                                                                                                                                    #AUTOINDEX-PAIR
                    #now join the three levels                                                                                                      #AUTOINDEX-PAIR
                    my_work_dir_candidate = os.path.join(my_toplevel_dir,my_typelevel_dir,my_datelevel_dir,my_sub_dir)                              #AUTOINDEX-PAIR
                                                                                                                                                    #AUTOINDEX-PAIR
                    #make sure this is an original directory                                                                                        #AUTOINDEX-PAIR
                    if os.path.exists(my_work_dir_candidate):                                                                                       #AUTOINDEX-PAIR
                        #we have already                                                                                                            #AUTOINDEX-PAIR
                        self.logger.debug('%s has already been used, will add qualifier' %  my_work_dir_candidate)                                  #AUTOINDEX-PAIR
                        for i in range(1,10000):                                                                                                    #AUTOINDEX-PAIR
                            if not os.path.exists('_'.join((my_work_dir_candidate,str(i)))):                                                        #AUTOINDEX-PAIR
                                my_work_dir_candidate = '_'.join((my_work_dir_candidate,str(i)))                                                    #AUTOINDEX-PAIR
                                self.logger.debug('%s will be used for this image' % my_work_dir_candidate)                                         #AUTOINDEX-PAIR 
                                break                                                                                                               #AUTOINDEX-PAIR
                            else:                                                                                                                   #AUTOINDEX-PAIR
                                i += 1                                                                                                              #AUTOINDEX-PAIR
                    my_work_dir = my_work_dir_candidate                                                                                             #AUTOINDEX-PAIR
                                                                                                                                                    #AUTOINDEX-PAIR
                    #now package directories into a dict for easy access by worker class                                                            #AUTOINDEX-PAIR
                    my_dirs = { 'work'          : my_work_dir,                                                                                      #AUTOINDEX-PAIR
                                'data_root_dir' : my_data_root_dir }                                                                                #AUTOINDEX-PAIR
                                                                                                                                                    #AUTOINDEX-PAIR
                    #generate a representation of the process for display                                                                           #AUTOINDEX-PAIR
                    my_repr =  my_sub_dir+'.img'                                                                                                    #AUTOINDEX-PAIR
                                                                                                                                                    #AUTOINDEX-PAIR                                              
                    #add the process to the database to display as in-process                                                                       #AUTOINDEX-PAIR
                    process_id = self.DATABASE.addNewProcess( type = 'pair',                                                                        #AUTOINDEX-PAIR
                                                              rtype = 'original',                                                                   #AUTOINDEX-PAIR
                                                              data_root_dir = my_data_root_dir,                                                     #AUTOINDEX-PAIR
                                                              repr = my_repr )                                                                      #AUTOINDEX-PAIR                                      
                                                                                                                                                    #AUTOINDEX-PAIR
                    #add the ID entry to the data dict                                                                                              #AUTOINDEX-PAIR
                    data1.update( { 'ID' : os.path.basename(my_work_dir),                                                                           #AUTOINDEX-PAIR
                                    'repr' : my_repr,                                                                                               #AUTOINDEX-PAIR
                                    'process_id' : process_id } )                                                                                   #AUTOINDEX-PAIR
                    data2.update( { 'ID':os.path.basename(my_work_dir),                                                                             #AUTOINDEX-PAIR
                                    'repr' : my_repr,                                                                                               #AUTOINDEX-PAIR
                                    'process_id' : process_id } )                                                                                   #AUTOINDEX-PAIR
                                                                                                                                                    #AUTOINDEX-PAIR
                                                                                                                                                    #AUTOINDEX-PAIR
                    if (self.SecretSettings['throttle_strategy'] == True):                                                                          #AUTOINDEX-PAIR
                        #too many jobs already running - put this in the queue                                                                      #AUTOINDEX-PAIR
                        if (len(self.indexing_active) >= self.SecretSettings['active_strategy_limit']):                                             #AUTOINDEX-PAIR
                            self.logger.debug('Adding pair indexing to the indexing queue')                                                         #AUTOINDEX-PAIR
                            self.indexing_queue.appendleft((('AUTOINDEX-PAIR',my_dirs,data1,data2,my_settings,(self.ip_address,self.socket)),       #AUTOINDEX-PAIR
                                                            my_settings,                                                                            #AUTOINDEX-PAIR
                                                            self.SecretSettings,                                                                    #AUTOINDEX-PAIR
                                                            self.logger))                                                                           #AUTOINDEX-PAIR
                        #go ahead and run, place marker in the queue                                                                                #AUTOINDEX-PAIR    
                        else:                                                                                                                       #AUTOINDEX-PAIR
                            #connect to the server and autoindex the single image                                                                   #AUTOINDEX-PAIR
                            self.logger.debug('Less than two processes active - running autoindexing')                                              #AUTOINDEX-PAIR
                            self.indexing_active.appendleft('autoindex-pair')                                                                       #AUTOINDEX-PAIR
                            #connect to the server and get things done                                                                              #AUTOINDEX-PAIR
                            PerformAction(command=('AUTOINDEX-PAIR',my_dirs,data1,data2,my_settings,(self.ip_address,self.socket)),                 #AUTOINDEX-PAIR
                                          settings=my_settings,                                                                                     #AUTOINDEX-PAIR
                                          secret_settings=self.SecretSettings,                                                                      #AUTOINDEX-PAIR
                                          logger=self.logger )                                                                                      #AUTOINDEX-PAIR 
                    else:                                                                                                                           #AUTOINDEX-PAIR
                        #No throttling - go ahead and run                                                                                           #AUTOINDEX-PAIR
                        PerformAction(command=('AUTOINDEX-PAIR',my_dirs,data1,data2,my_settings,(self.ip_address,self.socket)),                     #AUTOINDEX-PAIR
                                      settings=my_settings,                                                                                         #AUTOINDEX-PAIR
                                      secret_settings=self.SecretSettings,                                                                          #AUTOINDEX-PAIR
                                      logger=self.logger)                                                                                           #AUTOINDEX-PAIR            
            

        #this is the runs portion of the data image handling
        else:
            run_position = self.DATABASE.getRunPosition(image_number=int(data['image_number']),
                                                        run_id=run_id)

            #if the image is the first in a run, start watching for an abort                                                        
            if (run_position == 1):     
                try:                                                                
                    #create a RUNWATCHER and put it in the list  
                    run_dict = self.DATABASE.getRunByRunId(run_id)                                                                       
                    RUNWATCHER = RunWatcher(beamline=self.beamline,                                                                   
                                            run_dict=run_dict,                                                                           
                                            alert=self.RunAborted,                                                                   
                                            logger=self.logger)                                                                     
                    self.RUNWATCHERS.append(RUNWATCHER)                                                                                 
                except:
                    self.logger.debug("Error starting runwatcher")                                                                                                                
            
             
            #if we are runnning the rapd integration pipeline and hit image 5 and are binned, run
            if ((my_settings['integrate'] in ('rapd','True')) and (data['binning']!='none') and (run_position%5 == 0) ):
                run_dict = False
                #check for RunWatcher that matches                                                                                  #INTEGRATE
                for position,RUNWATCHER in enumerate(self.RUNWATCHERS):                                                             #INTEGRATE                                                           
                    if RUNWATCHER.run_id == run_id:                                                                                 #INTEGRATE                                                       
                        self.logger.debug('There is a Runwatcher for this run')                                                     #INTEGRATE
                        break                                                                                                       #INTEGRATE
                else:                                                                                                               #INTEGRATE
                    self.logger.debug('There is NO Runwatcher for this run - creating one')                                         #INTEGRATE
                    run_dict = self.DATABASE.getRunByRunId(run_id)
                    RUNWATCHER = RunWatcher(beamline=self.beamline,                                                                 #INTEGRATE                                                            
                                            run_dict=run_dict,                                                                      #INTEGRATE                                                         
                                            alert=self.RunAborted,                                                                  #INTEGRATE                                                          
                                            logger=self.logger)                                                                     #INTEGRATE                                                              
                    self.RUNWATCHERS.append(RUNWATCHER)                                                                             #INTEGRATE                                                
                                                                                                                                    #INTEGRATE
                if not RUNWATCHER.INTEGRATING:                                                                                      #INTEGRATE
                                                                                                                                    #INTEGRATE
                    #get the run_dict                                                                                               #INTEGRATE 
                    if not run_dict:
                        run_dict = self.DATABASE.getRunByRunId(run_id=run_id)                                                           #INTEGRATE
                                                                                                                                        #INTEGRATE
                    #adjust the beamcenter                                                                                              #INTEGRATE
                    if (float(my_settings['x_beam'])):                                                                                  #INTEGRATE
                        data['x_beam'] = my_settings['x_beam']                                                                          #INTEGRATE
                        data['y_beam'] = my_settings['y_beam']                                                                          #INTEGRATE
                                                                                                                                        #INTEGRATE
                    #get the correct directory to run in                                                                                #INTEGRATE
                    #the top level of the work directory                                                                                #INTEGRATE
                    if self.Settings['work_dir_override'] == 'False':                                                                   #INTEGRATE
                        my_toplevel_dir = self.start_dir                                                                                #INTEGRATE
                    else:                                                                                                               #INTEGRATE
                        my_toplevel_dir = self.Settings['work_directory']                                                               #INTEGRATE
                                                                                                                                        #INTEGRATE                                   
                    #the type level                                                                                                     #INTEGRATE
                    my_typelevel_dir = 'integrate'                                                                                      #INTEGRATE
                                                                                                                                        #INTEGRATE
                    #the date level                                                                                                     #INTEGRATE
                    my_datelevel_dir = datetime.date.today().isoformat()                                                                #INTEGRATE
                                                                                                                                        #INTEGRATE                                     
                    #the lowest level                                                                                                   #INTEGRATE
                    #my_sub_dir = '_'.join((str(data['image_prefix']),str(data['run_number']),'-'.join((str(run_dict['start']),str(data['image_number']))))) #INTEGRATE
                    my_sub_dir = '_'.join((str(data['image_prefix']),str(data['run_number'])))                                          #INTEGRATE
                                                                                                                                        #INTEGRATE
                    #now construct the directory name                                                                                   #INTEGRATE
                    my_work_dir_candidate = os.path.join(my_toplevel_dir,my_typelevel_dir,my_datelevel_dir,my_sub_dir)                  #INTEGRATE  
                                                                                                                                    #INTEGRATE
                    #make sure this is an original directory                                                                            #INTEGRATE
                    if os.path.exists(my_work_dir_candidate):                                                                           #INTEGRATE
                        #we have already                                                                                                #INTEGRATE
                        self.logger.debug('%s has already been used, will add qualifier' %  my_work_dir_candidate)                      #INTEGRATE
                        for i in range(1,10000):                                                                                        #INTEGRATE
                            if not os.path.exists('_'.join((my_work_dir_candidate,str(i)))):                                            #INTEGRATE
                                my_work_dir_candidate = '_'.join((my_work_dir_candidate,str(i)))                                        #INTEGRATE
                                self.logger.debug('%s will be used for this image' % my_work_dir_candidate)                             #INTEGRATE
                                break                                                                                                   #INTEGRATE
                            else:                                                                                                       #INTEGRATE
                                i += 1                                                                                                  #INTEGRATE
                    my_work_dir = my_work_dir_candidate                                                                                 #INTEGRATE
                                                                                                                                        #INTEGRATE
                    #now package directories into a dict for easy access by worker class                                                #INTEGRATE
                    my_dirs = { 'work'          : my_work_dir,                                                                          #INTEGRATE
                                'data_root_dir' : my_data_root_dir}                                                                     #INTEGRATE
                                                                                                                                        #INTEGRATE
                    #create a represention of the process for display                                                                   #INTEGRATE
                    my_repr = my_sub_dir                                                                                                #INTEGRATE
                                                                                                                                        #INTEGRATE
                    #if we are to integrate, do it                                                                                      #INTEGRATE
                    try:                                                                                                                #INTEGRATE
                        #add the process to the database to display as in-process                                                       #INTEGRATE
                        process_id = self.DATABASE.addNewProcess(type='integrate',                                                      #INTEGRATE
                                                                 rtype='original',                                                      #INTEGRATE
                                                                 data_root_dir=my_data_root_dir,                                        #INTEGRATE
                                                                 repr=my_repr)                                                          #INTEGRATE
                        #Make a new result for the integration - should show up in the user interface?                                  #INTEGRATE
                        #integrate_result_id,result_id = self.DATABASE.makeNewResult(rtype='integrate',                                 #INTEGRATE
                        #                                                            process_id=process_id)                             #INTEGRATE
                        #add the ID entry to the data dict                                                                              #INTEGRATE
                        data.update({'ID' : os.path.basename(my_work_dir),                                                              #INTEGRATE
                                     'repr' : my_repr,                                                                                  #INTEGRATE
                                     'process_id' : process_id})                                                                        #INTEGRATE
                        #construct data for the processing                                                                              #INTEGRATE
                        out_data = {'run_data'   : run_dict,                                                                            #INTEGRATE
                                    'image_data' : data}                                                                                #INTEGRATE
                        #connect to the server and autoindex the single image                                                           #INTEGRATE  
                        PerformAction(command = ('INTEGRATE',my_dirs,out_data,my_settings,(self.ip_address,self.socket)),               #INTEGRATE
                                      settings = my_settings,                                                                           #INTEGRATE
                                      secret_settings = self.SecretSettings,                                                            #INTEGRATE
                                      logger = self.logger)                                                                             #INTEGRATE
                        #mark the RUNWATCHER as integrating                                                                             #INTEGRATE
                        RUNWATCHER.INTEGRATING = True                                                                                   #INTEGRATE
                    except:                                                                                                             #INTEGRATE
                        self.logger.exception('Exception when attempting to run RAPD integration pipeline')                             #INTEGRATE
            
        
            #if we are runnning the rapd integration pipeline and hit the last image, get rid of the runwatcher
            if ((my_settings['integrate'] in ('rapd','True')) and (self.DATABASE.lastInRun(image_number = int(data['image_number']),run_id = run_id))):
                #close the RUNWATCHER                                                                                               
                try:                                                                                                                
                    self.logger.debug('Closing the runwatcher for run_id %d' % run_id)                                                   
                    for position,RUNWATCHER in enumerate(self.RUNWATCHERS):                                                            
                        if RUNWATCHER.run_id == run_id:                                                                             
                            self.logger.debug('Stop this Runwatcher')                                                               
                            RUNWATCHER.Stop()                                                                                       
                            self.RUNWATCHERS.__delitem__(position)                                                                  
                except:                                                                                                             
                    self.logger.exception('Malfunction in closing of Runwatcher for run id %d' % run_id)      
                
                #if we are unbinned, run on the end of the run
                if (data['binning']=='none'):
                    #get the run_dict                                                                                                   #INTEGRATE 
                    run_dict = self.DATABASE.getRunByRunId(run_id=run_id)                                                               #INTEGRATE
                                                                                                                                        #INTEGRATE
                    #adjust the beamcenter                                                                                              #INTEGRATE
                    if (float(my_settings['x_beam'])):                                                                                  #INTEGRATE
                        data['x_beam'] = my_settings['x_beam']                                                                          #INTEGRATE
                        data['y_beam'] = my_settings['y_beam']                                                                          #INTEGRATE
                                                                                                                                        #INTEGRATE
                    #get the correct directory to run in                                                                                #INTEGRATE
                    #the top level of the work directory                                                                                #INTEGRATE
                    if self.Settings['work_dir_override'] == 'False':                                                                   #INTEGRATE
                        my_toplevel_dir = self.start_dir                                                                                #INTEGRATE
                    else:                                                                                                               #INTEGRATE
                        my_toplevel_dir = self.Settings['work_directory']                                                               #INTEGRATE
                                                                                                                                        #INTEGRATE                                   
                    #the type level                                                                                                     #INTEGRATE
                    my_typelevel_dir = 'integrate'                                                                                      #INTEGRATE
                                                                                                                                        #INTEGRATE
                    #the date level                                                                                                     #INTEGRATE
                    my_datelevel_dir = datetime.date.today().isoformat()                                                                #INTEGRATE
                                                                                                                                        #INTEGRATE                                     
                    #the lowest level                                                                                                   #INTEGRATE
                    my_sub_dir = '_'.join((str(data['image_prefix']),str(data['run_number']),'-'.join((str(run_dict['start']),str(data['image_number']))))) #INTEGRATE
                                                                                                                                        #INTEGRATE
                    #now construct the directory name                                                                                   #INTEGRATE
                    my_work_dir_candidate = os.path.join(my_toplevel_dir,my_typelevel_dir,my_datelevel_dir,my_sub_dir)                  #INTEGRATE  
                                                                                                                                        #INTEGRATE
                    #make sure this is an original directory                                                                            #INTEGRATE
                    if os.path.exists(my_work_dir_candidate):                                                                           #INTEGRATE
                        #we have already                                                                                                #INTEGRATE
                        self.logger.debug('%s has already been used, will add qualifier' %  my_work_dir_candidate)                      #INTEGRATE
                        for i in range(1,10000):                                                                                        #INTEGRATE
                            if not os.path.exists('_'.join((my_work_dir_candidate,str(i)))):                                            #INTEGRATE
                                my_work_dir_candidate = '_'.join((my_work_dir_candidate,str(i)))                                        #INTEGRATE
                                self.logger.debug('%s will be used for this image' % my_work_dir_candidate)                             #INTEGRATE
                                break                                                                                                   #INTEGRATE
                            else:                                                                                                       #INTEGRATE
                                i += 1                                                                                                  #INTEGRATE
                    my_work_dir = my_work_dir_candidate                                                                                 #INTEGRATE
                                                                                                                                        #INTEGRATE
                    #now package directories into a dict for easy access by worker class                                                #INTEGRATE
                    my_dirs = { 'work'          : my_work_dir,                                                                          #INTEGRATE
                                'data_root_dir' : my_data_root_dir}                                                                     #INTEGRATE
                                                                                                                                        #INTEGRATE
                    #create a represention of the process for display                                                                   #INTEGRATE
                    my_repr = my_sub_dir                                                                                                #INTEGRATE
                                                                                                                                        #INTEGRATE
                    #if we are to integrate, do it                                                                                      #INTEGRATE
                    try:                                                                                                                #INTEGRATE
                        #add the process to the database to display as in-process                                                       #INTEGRATE
                        process_id = self.DATABASE.addNewProcess(type='integrate',                                                      #INTEGRATE
                                                                 rtype='original',                                                      #INTEGRATE
                                                                 data_root_dir=my_data_root_dir,                                        #INTEGRATE
                                                                 repr=my_repr)                                                          #INTEGRATE      
                        #add the ID entry to the data dict                                                                              #INTEGRATE
                        data.update({'ID' : os.path.basename(my_work_dir),                                                              #INTEGRATE
                                     'repr' : my_repr,                                                                                  #INTEGRATE
                                     'process_id' : process_id})                                                                        #INTEGRATE
                        #construct data for the processing                                                                              #INTEGRATE
                        out_data = {'run_data'   : run_dict,                                                                            #INTEGRATE
                                    'image_data' : data}                                                                                #INTEGRATE
                        #connect to the server and autoindex the single image                                                           #INTEGRATE  
                        PerformAction(command = ('INTEGRATE',my_dirs,out_data,my_settings,(self.ip_address,self.socket)),               #INTEGRATE
                                      settings = my_settings,                                                                           #INTEGRATE
                                      secret_settings = self.SecretSettings,                                                            #INTEGRATE
                                      logger = self.logger)                                                                             #INTEGRATE
                    except:                                                                                                             #INTEGRATE
                        self.logger.exception('Exception when attempting to run RAPD integration pipeline')                             #INTEGRATE
        
        
        
        #if we are runnning the xia2 integration pipeline and hit the last image, run
        if ((my_settings['integrate'] == 'xia2') and (self.DATABASE.lastInRun(image_number = int(data['image_number']),run_id = run_id))):   
            #close the RUNWATCHER                                                                                               #INTEGRATE
            try:                                                                                                                #INTEGRATE
                self.logger.debug('Closing the runwatcher for run_id %d' % run_id)                                              #INTEGRATE     
                for position,RUNWATCHER in enumerate(self.RUNWATCHERS):                                                         #INTEGRATE   
                    if RUNWATCHER.run_id == run_id:                                                                             #INTEGRATE
                        self.logger.debug('Stop this Runwatcher')                                                               #INTEGRATE
                        RUNWATCHER.Stop()                                                                                       #INTEGRATE
                        self.RUNWATCHERS.__delitem__(position)                                                                  #INTEGRATE
            except:                                                                                                             #INTEGRATE
                self.logger.exception('Malfunction in closing of Runwatcher for run id %d' % run_id)                            #INTEGRATE
                                                                                                                                #INTEGRATE
            #get the run_dict                                                                                                   #INTEGRATE 
            run_dict = self.DATABASE.getRunByRunId( run_id = run_id)                                                            #INTEGRATE
                                                                                                                                #INTEGRATE
            #get the correct directory to run in                                                                                #INTEGRATE
            #the top level of the work directory                                                                                #INTEGRATE
            if self.Settings['work_dir_override'] == 'False':                                                                   #INTEGRATE
                my_toplevel_dir = self.start_dir                                                                                #INTEGRATE
            else:                                                                                                               #INTEGRATE
                my_toplevel_dir = self.Settings['work_directory']                                                               #INTEGRATE
                                                                                                                                #INTEGRATE                                   
            #the type level                                                                                                     #INTEGRATE
            my_typelevel_dir = 'integrate'                                                                                      #INTEGRATE
                                                                                                                                #INTEGRATE
            #the date level                                                                                                     #INTEGRATE
            my_datelevel_dir = datetime.date.today().isoformat()                                                                #INTEGRATE
                                                                                                                                #INTEGRATE                                     
            #the lowest level                                                                                                   #INTEGRATE
            my_sub_dir = '_'.join((str(data['image_prefix']),str(data['run_number']),'-'.join((str(run_dict['start']),str(data['image_number']))))) #INTEGRATE
                                                                                                                                #INTEGRATE
            #now construct the directory name                                                                                   #INTEGRATE
            my_work_dir_candidate = os.path.join(my_toplevel_dir,my_typelevel_dir,my_datelevel_dir,my_sub_dir)                  #INTEGRATE  
                                                                                                                                #INTEGRATE
            #make sure this is an original directory                                                                            #INTEGRATE
            if os.path.exists(my_work_dir_candidate):                                                                           #INTEGRATE
                #we have already                                                                                                #INTEGRATE
                self.logger.debug('%s has already been used, will add qualifier' %  my_work_dir_candidate)                      #INTEGRATE
                for i in range(1,10000):                                                                                        #INTEGRATE
                    if not os.path.exists('_'.join((my_work_dir_candidate,str(i)))):                                            #INTEGRATE
                        my_work_dir_candidate = '_'.join((my_work_dir_candidate,str(i)))                                        #INTEGRATE
                        self.logger.debug('%s will be used for this image' % my_work_dir_candidate)                             #INTEGRATE
                        break                                                                                                   #INTEGRATE
                    else:                                                                                                       #INTEGRATE
                        i += 1                                                                                                  #INTEGRATE
            my_work_dir = my_work_dir_candidate                                                                                 #INTEGRATE
                                                                                                                                #INTEGRATE
            #now package directories into a dict for easy access by worker class                                                #INTEGRATE
            my_dirs = { 'work'          : my_work_dir,                                                                          #INTEGRATE
                        'data_root_dir' : my_data_root_dir}                                                                     #INTEGRATE
                                                                                                                                #INTEGRATE
            #create a represention of the process for display                                                                   #INTEGRATE
            my_repr = my_sub_dir                                                                                                #INTEGRATE
                                                                                                                                #INTEGRATE
            #if we are to integrate, do it                                                                                      #INTEGRATE
            try:                                                                                                                #INTEGRATE
                #add the process to the database to display as in-process                                                   #INTEGRATE
                process_id = self.DATABASE.addNewProcess(type='integrate',                                                  #INTEGRATE
                                                         rtype='original',                                                  #INTEGRATE
                                                         data_root_dir=my_data_root_dir,                                    #INTEGRATE
                                                         repr=my_repr)                                                      #INTEGRATE      
                                                                                                                            #INTEGRATE
                #add the ID entry to the data dict         
                data.update({'ID' : os.path.basename(my_work_dir),                                                          #INTEGRATE
                             'repr' : my_repr,                                                                              #INTEGRATE
                             'process_id' : process_id})                                                                    #INTEGRATE
                                                                                                                            #INTEGRATE
                #construct data for the processing                                                                          #INTEGRATE
                out_data = {'run_data'   : run_dict,                                                                        #INTEGRATE
                            'image_data' : data}                                                                            #INTEGRATE
                                                                                                                            #INTEGRATE
                                                                                                                            #INTEGRATE
                #connect to the server and autoindex the single image                                                       #INTEGRATE  
                PerformAction(command = ('XIA2',my_dirs,out_data,my_settings,(self.ip_address,self.socket)),           #INTEGRATE
                              settings = my_settings,                                                                       #INTEGRATE
                              secret_settings = self.SecretSettings,                                                        #INTEGRATE
                              logger = self.logger)                                                                         #INTEGRATE
            except:                                                                                                             #INTEGRATE
                self.logger.exception('Exception when attempting to run XIA2 integration pipeline')                                    #INTEGRATE

    def RunAborted(self,run_id):
        """
        Handle a aborted run signal from RunWatcher instance.
        """
        
        self.logger.info('Model::RunAborted  run_id: %d' % run_id)
        
        while (self.RUNWATCHERS):
            RUNWATCHER = self.RUNWATCHERS.pop()
            #get the run information
            run_dict = RUNWATCHER.run_dict
            #stop the RUNWATCHER
            RUNWATCHER.Stop()
            #wait for all images to be identified
            time.sleep(10)
            #modify the run to have only the collected images included
            max_image_id = self.DATABASE.runAborted(run_dict)
            #trigger integration of the run 
            if max_image_id:
                image_dict = self.DATABASE.getImageByImageID( image_id = max_image_id )
                self.NewDataImage( data = image_dict)

    def Receive(self,message):
        """
        Receive information from ControllerServer (self.SERVER) and handle accordingly.
        
        Several return lengths are currently supported:
            2 - command, info
            3 - command, info, server
            5 - command,dirs,info,settings,results
            6 - command,dirs,info,settings,server,results
            7 - command, dirs, info1, info2, settings, server, results
        Otherwise the message will be taken as a naked command
        
        Several commands are handled:
            IMAGE STATUS CHANGED
            ADSC RUN STATUS CHANGED
            CONSOLE RUN STATUS CHANGED
            DIFF_CENTER
            QUICK_ANALYSIS
            STAC
            STAC-PAIR
            AUTOINDEX
            AUTOINDEX-PAIR
            INTEGRATE
            XDS - reintegration performed using the RAPD pipeline
            XIA2
            SMERGE
            SAD
            MR
            STATS
            DOWNLOAD
            TEST
            SPEEDTEST
        """
        
        self.logger.info('Model::Receive')
        self.logger.info('length returned %d' % len(message))
        self.logger.debug(message)

        try:
            #integrate
            if len(message) == 5:
                command,dirs,info,settings,results = message
            #autoindex,stac,diffcenter
            elif len(message) == 6:
                command,dirs,info,settings,server,results = message
            #autoindex-pair,stac-pair
            elif len(message) == 7:
                command, dirs, info1, info2, settings, server, results = message
            #download
            elif (len(message) == 3):
                command, info, server = message
            elif len(message) == 2:
            #others
                command, info = message
            else:
                command = message
        except:
            #"OLD" format
            command = message
        
        #keep track adding to the database
        result_db = False
        trip_db   = False
        
        if (command == 'IMAGE STATUS CHANGED'):
            self.logger.debug('New image')
            self.AddImage(info)
            
        elif (command == 'ADSC RUN STATUS CHANGED'):
            for key,value in info['Runs'].iteritems():
                result = self.DATABASE.addRun(run=value,
                                              beamline=self.beamline)
                
        elif (command == 'CONSOLE RUN STATUS CHANGED'):
            result = self.DATABASE.addRun(run=info,
                                          beamline=self.beamline)
                
        elif (command == 'DIFF_CENTER'):                
            #add result to database
            result_db = self.DATABASE.addDiffcenterResult( dirs = dirs,
                                                           info = info,
                                                           settings = settings,
                                                           results = results )
            
            self.logger.debug('Added diffraction-based centering result: %s' % str(result_db))
            
            #write the file for CONSOLE
            if (result_db):
                TransferToBeamline(results=result_db,
                                   type='DIFFCENTER')
            
            #mark the process as finished
            self.DATABASE.modifyProcessDisplay(process_id = info['process_id'],
                                               display_value = 'complete')
            
        
        elif (command == 'QUICK_ANALYSIS'):      
            #add result to database
            result_db = self.DATABASE.addQuickanalysisResult(dirs = dirs,
                                                             info = info,
                                                             settings = settings,
                                                             results = results)
            
            self.logger.debug('Added quick analysis result: %s' % str(result_db))
            
            #write the file for CONSOLE
            if (result_db):
                TransferToBeamline(results=result_db,
                                   type='QUICKANALYSIS')
            
            #mark the process as finished
            self.DATABASE.modifyProcessDisplay(process_id = info['process_id'],
                                               display_value = 'complete')    
            
        elif (command == 'STAC'):
            #add result to database
            result_db = self.DATABASE.addSingleResult( dirs = dirs,
                                                       info = info,
                                                       settings = settings,
                                                       results = results )
                
            self.logger.debug('Added single result: %s' % str(result_db))
            
            #mark the process as finished
            self.DATABASE.modifyProcessDisplay( process_id = info['process_id'],
                                                display_value = 'complete' )
            #move the files to the server
            if result_db:
                #now mark the cloud database if this is a reprocess request
                if result_db['type'] in ('reprocess','stac'):
                    #remove the process from cloud_current
                    self.DATABASE.removeCloudCurrent( cloud_request_id = settings['request']['cloud_request_id'])
                    #note the result in cloud_complete
                    self.DATABASE.enterCloudComplete( cloud_request_id = settings['request']['cloud_request_id'],
                                                      request_timestamp = settings['request']['timestamp'],
                                                      request_type = settings['request']['request_type'],
                                                      data_root_dir = settings['request']['data_root_dir'],
                                                      ip_address = settings['request']['ip_address'],
                                                      start_timestamp = settings['request']['timestamp'],
                                                      result_id = result_db['result_id'],
                                                      archive = False )
                    #mark in cloud_requests
                    self.DATABASE.markCloudRequest( cloud_request_id = settings['request']['cloud_request_id'],
                                                    mark = 'complete')
                
                trip_db = self.DATABASE.getTrips( data_root_dir = dirs['data_root_dir'])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.DATABASE.updateTrip( trip_id = record['trip_id'],
                                                  date = result_db['date'])
                        #now transfer the files
                        transferred = TransferToUI( type = 'single',
                                                    settings = self.SecretSettings,
                                                    result = result_db,
                                                    trip = record,
                                                    logger = self.logger )
                                        
                #this data is an "orphan"
                else:
                    self.logger.debug("Orphan result")
                    #add the orphan to the orphan database table
                    self.DATABASE.addOrphanResult( type = 'single',
                                                   root = dirs['data_root_dir'],
                                                   id = result_db['single_result_id'],
                                                   date = info['date'] )
                    #copy the files to the UI host
                    dest = os.path.join(self.SecretSettings['ui_user_dir'],'orphans/single/')
                    #now transfer the files
                    transferred = TransferToUI( type = 'single-orphan',
                                                settings = self.SecretSettings,
                                                result = result_db,
                                                trip = trip_db,
                                                logger = self.logger )
        
            #the addition of result to db has failed, but still needs removed from the cloud
            else:
                if (settings['request']['request_type'] == 'reprocess'):
                    #remove the process from cloud_current
                    self.DATABASE.removeCloudCurrent( cloud_request_id = settings['request']['cloud_request_id'])
                    #note the result in cloud_complete
                    self.DATABASE.enterCloudComplete( cloud_request_id = settings['request']['cloud_request_id'],
                                                      request_timestamp = settings['request']['timestamp'],
                                                      request_type = settings['request']['request_type'],
                                                      data_root_dir = settings['request']['data_root_dir'],
                                                      ip_address = settings['request']['ip_address'],
                                                      start_timestamp = settings['request']['timestamp'],
                                                      result_id = 0,
                                                      archive = False )
                    #mark in cloud_requests
                    self.DATABASE.markCloudRequest( cloud_request_id = settings['request']['cloud_request_id'],
                                                    mark = 'failure')

        elif (command == 'STAC-PAIR'):             
            #add result to database
            result_db = self.DATABASE.addPairResult( dirs = dirs,
                                                     info1 = info1,
                                                     info2 = info2,
                                                     settings = settings,
                                                     results = results)
            self.logger.debug('Added pair result: %s' % str(result_db))

            #mark the process as finished
            self.DATABASE.modifyProcessDisplay( process_id = info1['process_id'],
                                                display_value = 'complete' )

            #move the files to the server
            if result_db:
                #now mark the cloud database if this is a reprocess request
                if result_db['type'] in ('reprocess','stac'):
                    #remove the process from cloud_current
                    self.DATABASE.removeCloudCurrent( cloud_request_id = settings['request']['cloud_request_id'])
                    #note the result in cloud_complete
                    self.DATABASE.enterCloudComplete( cloud_request_id = settings['request']['cloud_request_id'],
                                                      request_timestamp = settings['request']['timestamp'],
                                                      request_type = settings['request']['request_type'],
                                                      data_root_dir = settings['request']['data_root_dir'],
                                                      ip_address = settings['request']['ip_address'],
                                                      start_timestamp = settings['request']['timestamp'],
                                                      result_id = result_db['result_id'],
                                                      archive = False )
                    #mark in cloud_requests
                    self.DATABASE.markCloudRequest( cloud_request_id = settings['request']['cloud_request_id'],
                                                    mark = 'complete')

                trip_db = self.DATABASE.getTrips( data_root_dir = dirs['data_root_dir'])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.DATABASE.updateTrip( trip_id = record['trip_id'],
                                                  date = result_db['date_2'])
                        #now transfer the files
                        transferred = TransferToUI( type = 'pair',
                                                    settings = self.SecretSettings,
                                                    result = result_db,
                                                    trip = record,
                                                    logger = self.logger )
                #this data is an "orphan"
                else:
                    self.logger.debug("Orphan result")
                    #add the orphan to the orphan database table
                    self.DATABASE.addOrphanResult( type = 'pair',
                                                   root = dirs['data_root_dir'],
                                                   id = result_db['pair_result_id'],
                                                   date = info1['date'] )
                    #copy the files to the UI host
                    dest = os.path.join(self.SecretSettings['ui_user_dir'],'orphans/pair/')
                    #now transfer the files
                    transferred = TransferToUI( type = 'pair-orphan',
                                                settings = self.SecretSettings,
                                                result = result_db,
                                                trip = trip_db,
                                                logger = self.logger )

            #the addition of result to db has failed, but still needs removed from the cloud
            else:
                if (settings['request']['request_type'] == 'reprocess'):
                    #remove the process from cloud_current
                    self.DATABASE.removeCloudCurrent( cloud_request_id = settings['request']['cloud_request_id'])
                    #note the result in cloud_complete
                    self.DATABASE.enterCloudComplete( cloud_request_id = settings['request']['cloud_request_id'],
                                                      request_timestamp = settings['request']['timestamp'],
                                                      request_type = settings['request']['request_type'],
                                                      data_root_dir = settings['request']['data_root_dir'],
                                                      ip_address = settings['request']['ip_address'],
                                                      start_timestamp = settings['request']['timestamp'],
                                                      result_id = 0,
                                                      archive = False )
                    #mark in cloud_requests
                    self.DATABASE.markCloudRequest( cloud_request_id = settings['request']['cloud_request_id'],
                                                    mark = 'failure')

 
        elif command == 'AUTOINDEX':
            #Handle the ongoing throttling of autoindexing jobs
            if (self.SecretSettings['throttle_strategy'] == True):
                #pop one marker off the indexing_active
                try:
                    self.indexing_active.pop()
                except:
                    pass
                if (len(self.indexing_queue)>0):
                    self.logger.debug('Running a command from the indexing_queue')
                    job = self.indexing_queue.pop()
                    self.indexing_active.appendleft('unknown')
                    #send the job to be done
                    PerformAction(command=job[0],        
                                  settings=job[1], 
                                  secret_settings=job[2],        
                                  logger=job[3])   
                                   
            #add result to database
            result_db = self.DATABASE.addSingleResult(dirs=dirs,
                                                      info=info,
                                                      settings=settings,
                                                      results=results)
            
            self.logger.debug('Added single result: %s' % str(result_db))
            
            #mark the process as finished
            self.DATABASE.modifyProcessDisplay(process_id=info['process_id'],
                                               display_value='complete')
            
            #move the files to the server
            if result_db:
                
                
                #now mark the cloud database if this is a reprocess request
                if result_db['type'] in ('reprocess','stac'):
                    #remove the process from cloud_current
                    self.DATABASE.removeCloudCurrent( cloud_request_id = settings['request']['cloud_request_id'])
                    #note the result in cloud_complete
                    self.DATABASE.enterCloudComplete( cloud_request_id = settings['request']['cloud_request_id'],
                                                      request_timestamp = settings['request']['timestamp'],
                                                      request_type = settings['request']['request_type'],
                                                      data_root_dir = settings['request']['data_root_dir'],
                                                      ip_address = settings['request']['ip_address'],
                                                      start_timestamp = settings['request']['timestamp'],
                                                      result_id = result_db['result_id'],
                                                      archive = False )
                    #mark in cloud_requests
                    self.DATABASE.markCloudRequest( cloud_request_id = settings['request']['cloud_request_id'],
                                                    mark = 'complete')
                
                trip_db = self.DATABASE.getTrips( data_root_dir = dirs['data_root_dir'])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.DATABASE.updateTrip( trip_id = record['trip_id'],
                                                  date = result_db['date'])
                        #now transfer the files
                        transferred = TransferToUI( type = 'single',
                                                    settings = self.SecretSettings,
                                                    result = result_db,
                                                    trip = record,
                                                    logger = self.logger )
                                        
                #this data is an "orphan"
                else:
                    self.logger.debug("Orphan result")
                    #add the orphan to the orphan database table
                    self.DATABASE.addOrphanResult( type = 'single',
                                                   root = dirs['data_root_dir'],
                                                   id = result_db['single_result_id'],
                                                   date = info['date'] )
                    #copy the files to the UI host
                    dest = os.path.join(self.SecretSettings['ui_user_dir'],'orphans/single/')
                    #now transfer the files
                    transferred = TransferToUI( type = 'single-orphan',
                                                settings = self.SecretSettings,
                                                result = result_db,
                                                trip = trip_db,
                                                logger = self.logger )
        
            #the addition of result to db has failed, but still needs removed from the cloud
            else:
                if (settings['request']['request_type'] == 'reprocess'):
                    #remove the process from cloud_current
                    self.DATABASE.removeCloudCurrent( cloud_request_id = settings['request']['cloud_request_id'])
                    #note the result in cloud_complete
                    self.DATABASE.enterCloudComplete( cloud_request_id = settings['request']['cloud_request_id'],
                                                      request_timestamp = settings['request']['timestamp'],
                                                      request_type = settings['request']['request_type'],
                                                      data_root_dir = settings['request']['data_root_dir'],
                                                      ip_address = settings['request']['ip_address'],
                                                      start_timestamp = settings['request']['timestamp'],
                                                      result_id = 0,
                                                      archive = False )
                    #mark in cloud_requests
                    self.DATABASE.markCloudRequest( cloud_request_id = settings['request']['cloud_request_id'],
                                                    mark = 'failure')
            
                 
        elif command == 'AUTOINDEX-PAIR':
            if (self.SecretSettings['throttle_strategy'] == True):
                #pop one off the indexing_active
                try:
                    self.indexing_active.pop()
                except:
                    self.logger.exception('Error popping from self.indexing_active')
                if (len(self.indexing_queue)>0):
                    self.logger.debug('Running a command from the indexing_queue')
                    job = self.indexing_queue.pop()
                    self.indexing_active.appendleft('unknown')
                    PerformAction(command = job[0],           
                                      settings = job[1],  
                                      secret_settings = job[2],        
                                      logger = job[3]) 

            result_db = self.DATABASE.addPairResult( dirs = dirs,
                                                     info1 = info1,
                                                     info2 = info2,
                                                     settings = settings,
                                                     results = results)
            self.logger.debug('Added pair result: %s' % str(result_db))
            
            #mark the process as finished
            self.DATABASE.modifyProcessDisplay( process_id = info1['process_id'],
                                                display_value = 'complete' )
            
            #move the files to the server
            if result_db:
                #now mark the cloud database if this is a reprocess request
                if result_db['type'] == 'reprocess':
                    #remove the process from cloud_current
                    self.DATABASE.removeCloudCurrent(cloud_request_id = settings['request']['cloud_request_id'])
                    #note the result in cloud_complete
                    self.DATABASE.enterCloudComplete( cloud_request_id = settings['request']['cloud_request_id'],
                                                      request_timestamp = settings['request']['timestamp'],
                                                      request_type = settings['request']['request_type'],
                                                      data_root_dir = settings['request']['data_root_dir'],
                                                      ip_address = settings['request']['ip_address'],
                                                      start_timestamp = settings['request']['timestamp'],
                                                      result_id = result_db['result_id'],
                                                      archive = False )
                    #mark in cloud_requests
                    self.DATABASE.markCloudRequest( cloud_request_id = settings['request']['cloud_request_id'],
                                                    mark = 'complete')
                
                trip_db = self.DATABASE.getTrips( data_root_dir = dirs['data_root_dir'])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.DATABASE.updateTrip( trip_id = record['trip_id'],
                                                  date = result_db['date_2'] )
                        #now transfer the files
                        transferred = TransferToUI( type = 'pair',
                                                    settings = self.SecretSettings,
                                                    result = result_db,
                                                    trip = record,
                                                    logger = self.logger )
                #this data is an "orphan"
                else:
                    self.logger.debug('Orphan result')
                    #add the orphan to the orphan database table
                    self.DATABASE.addOrphanResult( type = 'pair',
                                                   root = dirs['data_root_dir'],
                                                   id = result_db['pair_result_id'],
                                                   date = info['date'])
                    #now transfer the files
                    transferred = TransferToUI( type = 'pair-orphan',
                                                settings = self.SecretSettings,
                                                result = result_db,
                                                trip = trip_db,
                                                logger = self.logger )
            
            #the addition of result to db has failed, but still needs removed from the cloud
            else:
                if (settings.has_key(['request'])):
                    if (settings['request']['request_type'] == 'reprocess'):
                        #remove the process from cloud_current
                        self.DATABASE.removeCloudCurrent( cloud_request_id = settings['request']['cloud_request_id'])
                        #note the result in cloud_complete
                        self.DATABASE.enterCloudComplete( cloud_request_id = settings['request']['cloud_request_id'],
                                                          request_timestamp = settings['request']['timestamp'],
                                                          request_type = settings['request']['request_type'],
                                                          data_root_dir = settings['request']['data_root_dir'],
                                                          ip_address = settings['request']['ip_address'],
                                                          start_timestamp = settings['request']['timestamp'],
                                                          result_id = 0,
                                                          archive = False )
                        #mark in cloud_requests
                        self.DATABASE.markCloudRequest( cloud_request_id = settings['request']['cloud_request_id'],
                                                        mark = 'failure')
                               
        elif command in ('INTEGRATE'):            
            result_db = self.DATABASE.addIntegrateResult( dirs = dirs,
                                                          info = info,
                                                          settings = settings,
                                                          results = results )
            self.logger.debug('Added integration result: %s' % str(result_db))
            
            #mark the process as finished
            self.DATABASE.modifyProcessDisplay( process_id = info['image_data']['process_id'],
                                                display_value = 'complete' )
            
            #move the files to the server
            if result_db:
                trip_db = self.DATABASE.getTrips( data_root_dir = dirs['data_root_dir'])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.DATABASE.updateTrip( trip_id = record['trip_id'],
                                                  date = result_db['date'] )
                        #now transfer the files
                        transferred = TransferToUI( type = 'integrate',
                                                    settings = self.SecretSettings,
                                                    result = result_db,
                                                    trip = record,
                                                    logger = self.logger )
                #this data is an "orphan"
                else:
                    self.logger.debug('Orphan result')
                    #add the orphan to the orphan database table
                    self.DATABASE.addOrphanResult( type = 'integrate',
                                                   root = dirs['data_root_dir'],
                                                   id = result_db['integrate_result_id'],
                                                   date = result_db['date'] )
                                        
                    #now transfer the files
                    transferred = TransferToUI( type = 'integrate-orphan',
                                                settings = self.SecretSettings,
                                                result = result_db,
                                                trip = trip_db,
                                                logger = self.logger )
                    
            #now place the files in the data_root_dir for the user to have and to hold
            if (self.SecretSettings['copy_data']):
                copied = CopyToUser(root=dirs['data_root_dir'],
                                    res_type="integrate",
                                    result=result_db,
                                    logger=self.logger)
            #the addition of result to db has failed, but still needs removed from the cloud
            #this is not YET an option so pass for now
            else:
                pass
        
        # Reintegration using RAPD pipeline
        elif command in ("XDS","XIA2"):            
            result_db = self.DATABASE.addReIntegrateResult(dirs=dirs,
                                                           info=info,
                                                           settings=settings,
                                                           results=results)
            self.logger.debug('Added reintegration result: %s' % str(result_db))
            
            #mark the process as finished
            self.DATABASE.modifyProcessDisplay( process_id = settings['process_id'],
                                                display_value = 'complete' )
            
            #move the files to the server
            if result_db:
                trip_db = self.DATABASE.getTrips( data_root_dir = dirs['data_root_dir'])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.DATABASE.updateTrip( trip_id = record['trip_id'],
                                                  date = result_db['date'] )
                        #now transfer the files
                        transferred = TransferToUI( type = 'integrate',
                                                    settings = self.SecretSettings,
                                                    result = result_db,
                                                    trip = record,
                                                    logger = self.logger )
                #this data is an "orphan"
                else:
                    self.logger.debug('Orphan result')
                    #add the orphan to the orphan database table
                    self.DATABASE.addOrphanResult( type = 'integrate',
                                                   root = dirs['data_root_dir'],
                                                   id = result_db['integrate_result_id'],
                                                   date = result_db['date'] )
                                        
                    #now transfer the files
                    transferred = TransferToUI( type = 'integrate-orphan',
                                                settings = self.SecretSettings,
                                                result = result_db,
                                                trip = trip_db,
                                                logger = self.logger )
                    
            #now place the files in the data_root_dir for the user to have and to hold
            if (self.SecretSettings['copy_data']):
                copied = CopyToUser(root=dirs['data_root_dir'],
                                    res_type="integrate",
                                    result=result_db,
                                    logger=self.logger)
            #the addition of result to db has failed, but still needs removed from the cloud
            #this is not YET an option so pass for now
            else:
                pass

        # Merging two wedges
        elif (command == "SMERGE"):       
            self.logger.debug("SMERGE Received")
            self.logger.debug(dirs)
            self.logger.debug(info)
            self.logger.debug(settings)
            self.logger.debug(results)
            

            result_db = self.DATABASE.addSimpleMergeResult(dirs=dirs,
                                                           info=info,
                                                           settings=settings,
                                                           results=results)
            self.logger.debug('Added simple merge result: %s' % str(result_db))
            
            #mark the process as finished
            self.DATABASE.modifyProcessDisplay(process_id=result_db['process_id'],
                                               display_value='complete')

            #move the files to the server
            if result_db:
                trip_db = self.DATABASE.getTrips(data_root_dir=dirs['data_root_dir'])
                self.logger.debug(trip_db)
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #now transfer the files
                        transferred = TransferToUI( type = 'smerge',
                                                    settings = self.SecretSettings,
                                                    result = result_db,
                                                    trip = record,
                                                    logger = self.logger )
                #this data is an "orphan"
                else:
                    self.logger.debug('Orphan result')
                    #add the orphan to the orphan database table
                    self.DATABASE.addOrphanResult( type = 'smerge',
                                                   root = dirs['data_root_dir'],
                                                   id = result_db['integrate_result_id'],
                                                   date = result_db['date'] )
                                        
                    #now transfer the files
                    transferred = TransferToUI( type = 'smerge-orphan',
                                                settings = self.SecretSettings,
                                                result = result_db,
                                                trip = trip_db,
                                                logger = self.logger )
            """    
            #now place the files in the data_root_dir for the user to have and to hold
            if (self.SecretSettings['copy_data']):
                copied = CopyToUser(root=dirs['data_root_dir'],
                                    res_type="smerge",
                                    result=result_db,
                                    logger=self.logger)
            #the addition of result to db has failed, but still needs removed from the cloud
            #this is not YET an option so pass for now
            else:
                pass
            """
        elif command == 'SAD':
            self.logger.debug('Received SAD result')
            result_db = self.DATABASE.addSadResult(dirs=dirs,
                                                   info=info,
                                                   settings=settings,
                                                   results=results )
            self.logger.debug('Added SAD result: %s' % str(result_db))
            
            #mark the process as finished
            self.DATABASE.modifyProcessDisplay( process_id = settings['process_id'],
                                                display_value = 'complete' )
            
            #move the files to the server
            if result_db:
                trip_db = self.DATABASE.getTrips( data_root_dir = dirs['data_root_dir'])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.DATABASE.updateTrip( trip_id = record['trip_id'],
                                                  date = result_db['timestamp'] )
                        #now transfer the files
                        transferred = TransferToUI( type = 'sad',
                                                    settings = self.SecretSettings,
                                                    result = result_db,
                                                    trip = record,
                                                    logger = self.logger )
                #this data is an "orphan"
                else:
                    self.logger.debug('Orphan result')
                    #add the orphan to the orphan database table
                    self.DATABASE.addOrphanResult( type = 'sad',
                                                   root = dirs['data_root_dir'],
                                                   id = result_db['integrate_result_id'],
                                                   date = result_db['date'] )
                                        
                    #now transfer the files
                    transferred = TransferToUI( type = 'sad-orphan',
                                                settings = self.SecretSettings,
                                                result = result_db,
                                                trip = trip_db,
                                                logger = self.logger )

            #now place the files in the data_root_dir for the user to have and to hold
            if (self.SecretSettings['copy_data']):
                if (result_db['download_file'] != "None"):
                    copied = CopyToUser(root=dirs['data_root_dir'],
                                        res_type="sad",
                                        result=result_db,
                                        logger=self.logger)
            #the addition of result to db has failed, but still needs removed from the cloud
            #this is not YET an option so pass for now
            else:
                pass
        
        elif command == 'MR':
            self.logger.debug('Received MR result')
            result_db = self.DATABASE.addMrResult(dirs=dirs,
                                                  info=info,
                                                  settings=settings,
                                                  results=results)
            #some debugging output
            self.logger.debug('Added MR result: %s' % str(result_db))
            
            #If the process is complete, mark it as such
            if (result_db['mr_status'] != 'WORKING'):
                #mark the process as finished
                self.DATABASE.modifyProcessDisplay(process_id=result_db['process_id'],
                                                   display_value='complete' )
            #move the files to the server
            if result_db:
                #Get the trip for this data
                trip_db = self.DATABASE.getTrips(data_root_dir=dirs['data_root_dir'])
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.DATABASE.updateTrip( trip_id = record['trip_id'],
                                                  date = result_db['timestamp'] )
                        #now transfer the files
                        transferred = TransferToUI( type = 'mr',
                                                    settings = self.SecretSettings,
                                                    result = result_db,
                                                    trip = record,
                                                    logger = self.logger )

            #now place the files in the data_root_dir for the user to have and to hold
            if (self.SecretSettings['copy_data']):
                all_mr_results = self.DATABASE.getMrTrialResult(result_db['mr_result_id'])
                #some debugging output
                self.logger.debug('Transfer MR file: ID %s' % result_db['mr_result_id'])
                if all_mr_results:
                    for mr_result in all_mr_results:
                        result_db['download_file']=mr_result['archive']
                        copied = CopyToUser(root=dirs['data_root_dir'],
                                        res_type="mr",
                                        result=result_db,
                                        logger=self.logger)

            #the addition of result to db has failed, but still needs removed from the cloud
            #this is not YET an option so pass for now
            else:
                pass
            
            
        elif command == 'DOWNLOAD':            
            #get the trip info
            trip_db = self.DATABASE.getTrips( data_root_dir = info['data_root_dir'])
            
            success = False
            if trip_db:
                for record in trip_db:
                    #move files to the server
                    transferred = TransferToUI( type = 'download',
                                                settings = self.SecretSettings,
                                                result = info,
                                                trip = record,
                                                logger = self.logger )
                    if transferred:
                        success = True
                        
            #update the database
            if success:
                #note the result in cloud_complete
                self.DATABASE.enterCloudComplete( cloud_request_id = info['cloud_request_id'],
                                                  request_timestamp = info['timestamp'],
                                                  request_type = info['request_type'],
                                                  data_root_dir = info['data_root_dir'],
                                                  ip_address = info['ip_address'],
                                                  start_timestamp = 0,
                                                  result_id = 0,
                                                  archive = os.path.basename(info['archive']) )

                #mark in cloud_requests
                self.DATABASE.markCloudRequest( cloud_request_id = info['cloud_request_id'],
                                                mark = 'complete')
            
            #the transfer was not successful
            else:
                #note the result in cloud_complete
                self.DATABASE.enterCloudComplete( cloud_request_id = info['cloud_request_id'],
                                                  request_timestamp = info['timestamp'],
                                                  request_type = info['request_type'],
                                                  data_root_dir = info['data_root_dir'],
                                                  ip_address = info['ip_address'],
                                                  start_timestamp = 0,
                                                  result_id = 0,
                                                  archive = os.path.basename(info['archive']) )

                #mark in cloud_requests
                self.DATABASE.markCloudRequest( cloud_request_id = info['cloud_request_id'],
                                                mark = 'failure')
        elif command == "STATS":
            self.logger.debug("Received STATS result")
            
            #rearrange results
            results = server.copy()
            
            #self.logger.debug(info)
            #self.logger.debug(results)
            result_db = self.DATABASE.addStatsResults(info=info,
                                                      results=results)
            self.logger.debug('Added STATS result: %s' % str(result_db))
            
            #mark the process as finished
            self.DATABASE.modifyProcessDisplay(process_id=info['process_id'],
                                               display_value='complete')
        
            #move the files to the server
            if result_db:
                #Get the trip for this data
                trip_db = self.DATABASE.getTrips(result_id=result_db['result_id'])
                #print trip_db
                #this data has an associated trip
                if trip_db:
                    for record in trip_db:
                        #update the dates for the trip
                        self.DATABASE.updateTrip( trip_id = record['trip_id'],
                                                  date = result_db['timestamp'] )
                        #now transfer the files
                        transferred = TransferToUI(type="stats",
                                                   settings=self.SecretSettings,
                                                   result=result_db,
                                                   trip=record,
                                                   logger=self.logger )
                #this data is an "orphan"
                else:
                    self.logger.debug('Orphan result')
                    #now transfer the files
                    transferred = TransferToUI(type='stats-orphan',
                                               settings=self.SecretSettings,
                                               result=result_db,
                                               trip=trip_db,
                                               logger=self.logger )
            
        elif command == 'TEST':
            self.logger.debug('Cluster connection test successful')
            
        elif command == 'SPEEDTEST':
            self.logger.debug('Cluster connection test successful')
            
        else:
            self.logger.debug('Take no action for message')
            self.logger.debug(message)
            
class StatusHandler(threading.Thread):
    """
    Handles logging of life for the RAPD Core process.
    """
    
    def __init__(self,db,ip_address,data_root_dir,beamline,dataserver_ip,cluster_ip,logger):
        """
        Initialize the instance by saving variables.
        
        db - a connection to the rapd database instance
        ip_address - ip address of this model
        data_root_dir - the current data root directory
        beamline - the beamline desgnation for this rapd_model
        dataserver_ip - ip address of the computer hosting the process watching data collection
        cluster_ip - the ip address of the cluster which this rapd_model is sending jobs to
        logger - logger instance
        
        """
        
        logger.info('StatusHandler::__init__')
        
        #initialize the thread
        threading.Thread.__init__(self)

        #store passed-in variables
        self.DATABASE      = db
        self.ip_address    = ip_address
        self.data_root_dir = data_root_dir
        self.beamline      = beamline
        self.dataserver_ip = dataserver_ip
        self.cluster_ip    = cluster_ip
        self.logger        = logger
                
        #start the thread
        self.start() 

    def run(self):
        """
        Starts the thread going.
        """
        
        self.logger.debug('StatusHandler::run')
        while (1):
             #log the status of this Thread (the controller process)
             self.DATABASE.updateControllerStatus( controller_ip = self.ip_address,
                                                   data_root_dir = self.data_root_dir,
                                                   beamline      = self.beamline,
                                                   dataserver_ip = self.dataserver_ip,
                                                   cluster_ip    = self.cluster_ip)
             #now wait before next update
             time.sleep(30)

        

        
