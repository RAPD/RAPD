__author__ = "Frank Murphy"
__copyright__ = "Copyright 2009,2010,2011 Cornell University"
__credits__ = ["Frank Murphy","Jon Schuermann","David Neau","Kay Perry","Surajit Banerjee"]
__license__ = "BSD-3-Clause"
__version__ = "0.9"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"
__date__ = "2009/07/08"

import os
import shutil
import paramiko
import time

secret_settings_general = { #database information
                            'db_host'         : 'rapd.nec.aps.anl.gov',         #location of mysql database
                            'db_user'         : 'rapd1',                        #internal username
                            'db_password'     : 'my_password',                  #use base64 encoding for fun here
                            'db_data_name'    : 'rapd_data',                    #database names
                            'db_users_name'   : 'rapd_users',                   #
                            'db_cloud_name'   : 'rapd_cloud',                   #
                            #ui server information
                            'ui_host'         : 'rapd.nec.aps.anl.gov',         #server of the ui
                            'ui_user_dir'     : '/var/www/html/rapd/users/',    #location of the users
                            'ui_upload_dir'   : '/var/www/html/rapd/uploads/',  #location of uploaded files
                            'ui_port'         : 22,                             #
                            'ui_user'         : 'apache',                       #username on the ui host for ssh
                            'ui_password'     : '',                             #use base64 encoding for fun here
                            #controller settings                                
                            'controller_port' : 50001,                          #the post for the core process to listen on for communications
                            #cluster server settings
                            'cluster_port'    : 50000,
                            'process_port_init': 50002,                         #the port number to start at when making a listener 
                            'cluster_logfile_dir' : '/share/apps/necat/tmp',        #the location to put the tempfile - could be local or shared 
                            
                            #image tags for special images
                            'beamcenter_tag'  : 'beamcenter',
                            #diffraction-based centering settings
                            'diffcenter_tag'  : '_dfa_',
                            'diffcenter_server' : '000.000.000.000',  #gadolinium
                            'diffcenter_port' : 8125,
                            #snapshot-based quality analysis settings
                            'quickanalysis_tag' : 'raster_snap',
                            'quickanalysis_server' : '000.000.000.000',  #gadolinium
                            'quickanalysis_port' : 8126,
                            'quickanalysis_test_tag' : 'raster_snap_test',
                            #tag for ignoring the image
                            'ignore_tag' : 'delete',
                            #Controlling the number of processes running concurrently
                            'throttle_strategy' : False,
                            'active_strategy_limit' : 2,
                            #A delay between existence and moving a file from fs to webserver
                            'filesystem_delay' : 0.5,
                            #should the users get data from rapd in their data_root_dir?
                            'copy_data' : True,
                            #directory for beamline puck settings files
                            'puck_dir'  : {'C' : '/mnt/shared_drive/config/phi/',
                                           'E' : '/mnt/shared_drive/config/phii/'},
                            #Cutoff date in MYSQL format,yyyy-mm-dd hh:mm:ss, for creating Master Puck List
                            'puck_cutoff' : '2011-01-01 00:00:00',
                            #testing information
                            'faux_coll_dir' : '/gpfs1/users/necat/test_rapd',
                            #where to place uploaded files 
                            'upload_dir' : '/gpfs1/users/necat/rapd/uranium/trunk/uploads/',
                            #turn on/off tranfer to ui
                            'xfer_to_ui' : True }

settings_C = { 'beamline'          : 'C',
               'multiprocessing'   : 'True',
               'spacegroup'        : 'None',
               'sample_type'       : 'Protein',
               'solvent_content'   : '0.55',
               'susceptibility'    : '1.0',
               'crystal_size_x'    : '100',      
               'crystal_size_y'    : '100',
               'crystal_size_z'    : '100',
               'a'                 : '0',
               'b'                 : '0',
               'c'                 : '0',
               'alpha'             : '0',
               'beta'              : '0',
               'gamma'             : '0',
               'work_dir_override' : 'False',
               'work_directory'    : 'None',
               'beam_flip'         : 'False',
               'x_beam'            : '0',
               'y_beam'            : '0',
               'index_hi_res'      : '0',
               'strategy_type'     : 'best',
               'best_complexity'   : 'none',
               'mosflm_seg'        : '1',
               'mosflm_rot'        : '0.0',
               'min_exposure_per'  : '1' ,
               'aimed_res'         : '0',
               'beam_size_x'       : 'AUTO',     
               'beam_size_y'       : 'AUTO',
               'integrate'         : 'rapd',
               'reference_data_id' : '0',
               #Beam center formula for overiding center
               'use_beam_formula'  : True,
               #Calculated based on shift seen in Labelit position
	       'beam_center_date'  : 'November 7, 2011 ',
               'beam_center_x_m6'  : -3.59352e-17,
               'beam_center_x_m5'  : 1.41876e-13,
               'beam_center_x_m4'  : -2.19571e-10,
               'beam_center_x_m3'  : 1.67170e-7,
               'beam_center_x_m2'  : -6.34163e-5,
               'beam_center_x_m1'  : 5.67586e-3,
               'beam_center_x_b'   : 158.224,
               'beam_center_y_m6'  : 1.88650e-17,
               'beam_center_y_m5'  : -8.64687e-14,
               'beam_center_y_m4'  : 1.50920e-10,
               'beam_center_y_m3'  : -1.26825e-7,
               'beam_center_y_m2'  : 5.41259e-5,
               'beam_center_y_m1'  : -1.19699e-2,
               'beam_center_y_b'   : 157.139,
               }


secret_settings_C = { 'beamline'          : 'C',
                      #cluster info
                      'cluster_host'      : '000.000.000.000',   #gadolinium
                      'adsc_server'       : 'http://000.000.000.000:8001',
                      #Redis database information
                      'redis_ip'          : '000.000.000.000',
                      'redis_port'        : 6379,
                      'redis_db'          : 0,
                      #alternative cluster information
                      'cluster_stac'      : '000.000.000.000',   #uranium                            
                      'cluster_strategy'  : False, 
                      'cluster_integrate' : False, 
                      #cloud information
                      'cloud_interval'    : 1.0,                           #set to 0.0 if you want cloud monitoring turned off
                      'local_ip_prefix'   : '000.000.000',
                      'console_marcollect': '/mnt/shared_drive/config/id_c_marcollect',
                      'diffcenter_test_image' : '/gpfs1/users/necat/rapd/uranium/trunk/test_data/dfa_test_1_001.img',
                      'diffcenter_test_dat' : '/gpfs1/users/necat/phi_dfa_1/out/dfa_heartbeat.dat',
                      'rastersnap_test_image' : '/gpfs1/users/necat/rapd/uranium/trunk/test_data/raster_snap_test_1_001.img',
                      'rastersnap_test_dat' : '/gpfs1/users/necat/phi_raster_snap/out/phi_heartbeat.dat'}

secret_settings_C.update(secret_settings_general)

##########################################################################

settings_E = { 'beamline'          : 'E',
               'multiprocessing'   : 'True',
               'spacegroup'        : 'None',
               'sample_type'       : 'Protein',
               'solvent_content'   : '0.55',
               'susceptibility'    : '1.0',
               'crystal_size_x'    : '100',      
               'crystal_size_y'    : '100',
               'crystal_size_z'    : '100',
               'a'                 : '0',
               'b'                 : '0',
               'c'                 : '0',
               'alpha'             : '0',
               'beta'              : '0',
               'gamma'             : '0',
               'work_dir_override' : 'False',
               'work_directory'    : 'None',
               'beam_flip'         : 'False',
               'x_beam'            : '0',
               'y_beam'            : '0',
               'index_hi_res'      : '0',
               'strategy_type'     : 'best',
               'best_complexity'   : 'none',
               'mosflm_seg'        : '1',
               'mosflm_rot'        : '0.0',
               'min_exposure_per'  : '1' ,
               'aimed_res'         : '0',
               'beam_size_x'       : 'AUTO',     
               'beam_size_y'       : 'AUTO',
               'integrate'         : 'rapd',
               'reference_data_id' : '0',
               #Beam center formula for overiding center
               'use_beam_formula'  : True,
	       'beam_center_date'  : 'November 1, 2011',
               #Calculated from Labelit refined position
               'beam_center_x_m6'  : 4.34733e-18,
               'beam_center_x_m5'  : -2.48888e-14,
               'beam_center_x_m4'  : 5.35492e-11,
               'beam_center_x_m3'  : -5.54388e-8,
               'beam_center_x_m2'  : 2.93067e-5,
               'beam_center_x_m1'  : -1.43881e-2,
               'beam_center_x_b'   : 158.164,
               'beam_center_y_m6'  : 4.52880e-17,
               'beam_center_y_m5'  : -1.61454e-13,
               'beam_center_y_m4'  : 2.16389e-10,
               'beam_center_y_m3'  : -1.35306e-7,
               'beam_center_y_m2'  : 4.05261e-5,
               'beam_center_y_m1'  : -6.35949e-3,
               'beam_center_y_b'   : 159.207,
               }




secret_settings_E = { 'beamline'          : 'E',
                      #cluster info
                      #'cluster_host'      : '164.54.212.165',    #uranium
                      #'cluster_host'      : '164.54.212.166',    #copper
                      'cluster_host'      : '164.54.212.150',    #gadolinium
                      #'cluster_host'      : '127.0.0.1',         #localhost
                      'adsc_server'       :  'http://164.54.212.180:8001',
                      #Redis database information
                      'redis_ip'          : '164.54.212.125',
                      'redis_port'        : 6379,
                      'redis_db'          : 0,
                      #alternative cluster information
                      'cluster_stac'      : '164.54.212.165',   #uranium                            
                      'cluster_strategy'  : False, 
                      'cluster_integrate' : False, 
                      #'cluster_strategy'  : '164.54.212.166',   #copper
                      #'cluster_integrate' : '164.54.212.150',   #gadolinium
                      #cloud information
                      'cloud_interval'    : 0.0,                           #set to 0.0 if you want cloud monitoring turned off
                      'local_ip_prefix'   : '164.54.212',
                      'console_marcollect': '/mnt/shared_drive/config/id_e_marcollect',
                      'rastersnap_test_image' : '/gpfs1/users/necat/rapd/copper/trunk/images/raster_snap_test_1_001.img',
                      'rastersnap_test_dat' : '/gpfs1/users/necat/phii_raster_snap/out/phii_heartbeat.dat'}

secret_settings_E.update(secret_settings_general)

################################################################################

settings_T = { 'beamline'          : 'T',
               'multiprocessing'   : 'True',
               'spacegroup'        : 'None',
               'sample_type'       : 'Protein',
               'solvent_content'   : '0.55',
               'susceptibility'    : '1.0',
               'crystal_size_x'    : '100',      
               'crystal_size_y'    : '100',
               'crystal_size_z'    : '100',
               'a'                 : '0',
               'b'                 : '0',
               'c'                 : '0',
               'alpha'             : '0',
               'beta'              : '0',
               'gamma'             : '0',
               'work_dir_override' : 'True',
               'work_directory'    : '/gpfs1/users/necat/rapd/uranium/trunk',
               'beam_flip'         : 'False',
               'x_beam'            : '0',
               'y_beam'            : '0',
               'index_hi_res'      : '0',
               'strategy_type'     : 'best',
               'best_complexity'   : 'none',
               'mosflm_seg'        : '1',
               'mosflm_rot'        : '0.0',
               'min_exposure_per'  : '1' ,
               'aimed_res'         : '0',
               'beam_size_x'       : 'AUTO',     
               'beam_size_y'       : 'AUTO',
               'integrate'         : 'rapd',
               #Beam center formula for overiding center
               'use_beam_formula'  : True,
               'beam_center_date'  : 'August 20, 2010',
               'beam_center_x_m'   : -0.004518,
               'beam_center_x_b'   : 159.30,
               'beam_center_y_m'   : -0.000300,
               'beam_center_y_b'   : 156.02 }


secret_settings_T = { 'beamline'          : 'T',
                      'cluster_host'       : '000.000.000.000', #gadolinium
                      'adsc_server'       :  'http://127.0.0.1:8001',
                      #alternative cluster information
                      'cluster_stac'      : False,                            
                      'cluster_strategy'  : False,
                      'cluster_integrate' : False,
                      #'cluster_strategy'  : '164.54.212.166',   #copper
                      #'cluster_integrate' : '164.54.212.150',   #gadolinium
                      #cloud information
                      'cloud_interval'    : 1.0,                           #set to 0.0 if you want cloud monitoring turned off
                      'local_ip_prefix'   : '000.000.000',
                      'console_marcollect': '/tmp/id_c_marcollect',  }

secret_settings_T.update(secret_settings_general)

######################################################################################

beamline_settings = { 'C' : settings_C,
                      'E' : settings_E,
                      'T' : settings_T }

secret_settings = { 'C' : secret_settings_C,
                    'E' : secret_settings_E,
                    'T' : secret_settings_T}

######################################################################################

dataserver_settings = {#ID24-C 
                       'myserver.mydomain.gov'  : ('/usr/local/ccd_dist_md2b_rpc/tmp/marcollect','/usr/local/ccd_dist_md2b_rpc/tmp/xf_status','C'),
                       #ID24-E
                       'myserver.mydomain.gov' : ('/usr/local/ccd_dist_md2_rpc/tmp/marcollect','/usr/local/ccd_dist_md2_rpc/tmp/xf_status','E'),
                       #DEFAULT
                       'default'                  : ('/tmp/marcollect','/tmp/xf_status','T')
                      }


def NecatDetermineFlux(header_in,beamline,logger):
    """
    Determine beam information from the header information and return in the header dict
    """
    logger.info('NecatDetermineFlux %s %s' %(beamline,str(header_in)))
    header_out = header_in.copy()
    
    #New numbers according to Raj's testing with APS flux counter          
    e_flux = 8E11            
    #C flux too high for Best to give good strategy
    c_flux = 3E12
    
    #the Gaussian description of the beam for Best
    header_out['gauss_x'] = '0.03'
    header_out['gauss_y'] = '0.01'
    
    #very old headers may be missing
    if not 'md2_aperture' in header_in.keys():
        if beamline == 'C':
            header_in['md2_aperture'] = '70' 
        else:
            header_in['md2_aperture'] = '50' 
    #header is occasionally missing the inormation
    elif header_in['md2_aperture'] == '0' or '-1':
        if beamline == 'C':
            header_in['md2_aperture'] = '70' 
        else:
            header_in['md2_aperture'] = '50'        

    #Sets beam shape for Raddose assuming 30 x 70 micron beam (ID-C) and 20 x 50 micron beam (ID-E). 
    #Number in flux calculation is % area of beam relative to largest aperture (70 micron). We found
    #that flux is roughly proportional to area of aperture.          
    if beamline == 'C':
        if header_in['md2_aperture'] == '5':
            header_out['beam_size_x'] = '0.005'
            header_out['beam_size_y'] = '0.005'
            header_out['flux']      = str(((c_flux)*(0.0121)*(float(header_in['transmission'])))/(100.0))
        if header_in['md2_aperture'] == '10':
            header_out['beam_size_x'] = '0.01'
            header_out['beam_size_y'] = '0.01'
            header_out['flux']      = str(((c_flux)*(0.0479)*(float(header_in['transmission'])))/(100.0))            
        if header_in['md2_aperture'] == '20':
            header_out['beam_size_x'] = '0.02'
            header_out['beam_size_y'] = '0.02'  
            header_out['flux']      = str(((c_flux)*(0.190)*(float(header_in['transmission'])))/(100.0))         
        if header_in['md2_aperture'] == '30':
            header_out['beam_size_x'] = '0.03'
            header_out['beam_size_y'] = '0.03' 
            header_out['flux']      = str(((c_flux)*(0.429)*(float(header_in['transmission'])))/(100.0))          
        if header_in['md2_aperture'] == '50':
            header_out['beam_size_x'] = '0.05'
            header_out['beam_size_y'] = '0.03'  
            header_out['flux']      = str(((c_flux)*(0.714)*(float(header_in['transmission'])))/(100.0))                        
        if header_in['md2_aperture'] == '70':
            header_out['beam_size_x'] = '0.07'
            header_out['beam_size_y'] = '0.03'  
            header_out['flux']      = str(((c_flux)*(1.000)*(float(header_in['transmission'])))/(100.0))                     
    else: 
        if header_in['md2_aperture'] == '5':
            header_out['beam_size_x'] = '0.005'
            header_out['beam_size_y'] = '0.005'
            header_out['flux']      = str(((e_flux)*(0.0182)*(float(header_in['transmission'])))/(100.0))         
        if header_in['md2_aperture'] == '10':
            header_out['beam_size_x'] = '0.01'
            header_out['beam_size_y'] = '0.01' 
            header_out['flux']      = str(((e_flux)*(0.0719)*(float(header_in['transmission'])))/(100.0))          
        if header_in['md2_aperture'] == '20':
            header_out['beam_size_x'] = '0.02'
            header_out['beam_size_y'] = '0.02' 
            header_out['flux']      = str(((e_flux)*(0.286)*(float(header_in['transmission'])))/(100.0))                 
        if header_in['md2_aperture'] == '30':
            header_out['beam_size_x'] = '0.03'
            header_out['beam_size_y'] = '0.02'   
            header_out['flux']      = str(((e_flux)*(0.429)*(float(header_in['transmission'])))/(100.0))      
        if header_in['md2_aperture'] == '50':
            header_out['beam_size_x'] = '0.05'
            header_out['beam_size_y'] = '0.02' 
            header_out['flux']      = str(((e_flux)*(0.714)*(float(header_in['transmission'])))/(100.0))         
        if header_in['md2_aperture'] == '70':
            header_out['beam_size_x'] = '0.07'
            header_out['beam_size_y'] = '0.02'  
            header_out['flux']      = str(((e_flux)*(1.000)*(float(header_in['transmission'])))/(100.0)) 
    
    return(header_out)

def NecatDetermineImageType(data,logger):
    """
    Determine the type of image that has been noticed by RAPD.
    
    Current types:
        data - user data image
        diffcenter - diffraction-based centering image
        beamcenter - direct beam shot for beam center calculations
        quickanalysis - for the so-called rastersnap protocol 
        quickanalysis-test - a heartbeat function to satisfy worried colleagues
        ignore - well, you get it
        
    data is currently expected to be a dict with a 'fullname' entry which is the full 
         name of the image file
    """
    logger.info('NecatDetermineImageType %s' % str(data))
    
    if (secret_settings_general['beamcenter_tag'] in data['fullname']):
        image_type = 'beamcenter'
    elif (secret_settings_general['diffcenter_tag'] in data['fullname']):
        image_type = 'diffcenter'
    elif (secret_settings_general['quickanalysis_test_tag'] in data['fullname']):
        image_type = 'quickanalysis-test'
    elif (secret_settings_general['quickanalysis_tag'] in data['fullname']):
        image_type = 'quickanalysis'
    elif (secret_settings_general['ignore_tag'] in data['fullname']):
        image_type = 'ignore'
    else:
        image_type = 'data'
    
    #output to the log
    logger.debug('%s id %s' % (data['fullname'],image_type))
    
    return(image_type)

def GetDataRootDir(fullname,logger):
    """
    Derive the data root directory from the user directory
    
    The logic will most likely be unique for each beamline, so this
    finds its home in rapd_site.py
    """
    #isolate distinct properties of the images path
    logger.info('GetRootDataDir %s', fullname) 
        
    path_split    = fullname.split(os.path.sep)
    data_root_dir = False
        
    gpfs   = False
    users  = False
    inst   = False
    group  = False
    images = False
    
    if path_split[1].startswith('gpfs'):
        gpfs = path_split[1]
        if path_split[2] == 'users':
            users = path_split[2]
            if path_split[3]:
                inst = path_split[3]
                if path_split[4]:
                    group = path_split[4]
    
    if group:
        data_root_dir = os.path.join('/',*path_split[1:5])
    elif inst:
        data_root_dir = os.path.join('/',*path_split[1:4])
    else:
        data_root_dir = False
    
    #return the determined directory
    return(data_root_dir)

def TransferToBeamline(results,type='DIFFCENTER'):
    """
    Make the file to be read by console
    """
    if (type == 'QUICKANALYSIS-TEST'):
        output_file = results['outfile']
        output = open(output_file,'w')
        output.write("%f \n"%time.time());
        output.close()
    elif (type=='DIFFCENTER'):
        output_file = results['fullname'].replace('in','out').replace('.img','.dat')
        output = open(output_file,'w')
        output.write('%10d\r\n'%results['distl_res'])
        output.write('%10d\r\n'%results['labelit_res'])
        output.write('%10d\r\n'%results['overloads'])
        output.write('%10d\r\n'%results['total_spots'])
        output.write('%10d\r\n'%results['good_b_spots'])
        output.write('%10d\r\n'%results['in_res_spots'])
        output.write('%10d\r\n'%int(results['max_signal_str']))
        output.write('%10d\r\n'%int(results['mean_int_signal']))
        output.write('%10d\r\n'%int(results['min_signal_str']))
        output.write('%10d\n'%int(results['total_signal']))
        output.write('%10d\n'%int(results['saturation_50']))
        output.close()
    elif (type=='QUICKANALYSIS'):
        output_file = results['fullname'].replace('in','out').replace('.img','.dat')
        output = open(output_file,'w')
        output.write('%12.2f\r\n'%results['distl_res'])
        output.write('%12.2f\r\n'%results['labelit_res'])
        output.write('%10d\r\n'%results['overloads'])
        output.write('%10d\r\n'%results['total_spots'])
        output.write('%10d\r\n'%results['good_b_spots'])
        output.write('%10d\r\n'%results['in_res_spots'])
        output.write('%12.2f\r\n'%int(results['max_signal_str']))
        output.write('%12.2f\r\n'%int(results['mean_int_signal']))
        output.write('%12.2f\r\n'%int(results['min_signal_str']))
        output.write('%12.2f\r\n'%int(results['total_signal']))
        output.write('%12.2f\r\n'%int(results['saturation_50']))
        output.close()
    return(True)

def TransferPucksToBeamline(beamline,puck_contents):
    """
    Make puck files to be read by console
    """
    puck_dir = secret_settings_general['puck_dir'][beamline]
    puck = puck_contents.keys()[0]
    output_file = puck_dir+puck+'/puck_contents.txt'
    print 'TransferPucksToBeamline dir: %s' % output_file
    contents = puck_contents.values()[0]
    output = open(output_file,'w')
    if type(contents) is str:
        for i in range(16):
            output.write('%s\n%s\n'%(contents,contents))
    else:
        for i in range(16):
            output.write('%s\n%s\n'%(contents[i]['CrystalID'],contents[i]['PuckID']))
    output.close()

def TransferMasterPuckListToBeamline(beamline,allpucks):
    """
    Make master list of all available pucks to be read by console
    """
    puck_dir = secret_settings_general['puck_dir'][beamline]
    output_file = puck_dir+'/allpucks.txt'
    print 'TransferMasterPuckListToBeamline dir: %s' % output_file
    output = open(output_file,'w')
    for puck in allpucks:
        output.write('%s %s\n'%(puck['PuckID'],puck['select']))
    output.close()
             
def CopyToUser(root,res_type,result,logger):
    """
    Copy processed data to the user's area.
    
    root - the data root directory for the trip
    res_type - the type of data we are moving
               integrate,sad,mr
    result - the dict from the result
    logger - instance of logger
    """
    
    logger.debug('CopyToUser dir:%s' % root)
    logger.debug(result)
    
    try:
        if result['download_file']:
            #files/directories
            if (res_type == "integrate"):
                targetdir = os.path.join(root,'process','rapd','integrate',result['repr'])
            elif (res_type == "sad"):
                targetdir = os.path.join(root,'process','rapd','sad',result['repr'])
            elif (res_type == "mr"):
                targetdir = os.path.join(root,'process','rapd','mr',result['repr'])
            else:
                targetdir = os.path.join(root,'process','rapd',result['repr'])
            targetfile = os.path.join(targetdir,os.path.basename(result['download_file']))
            #Make sure we aren't overwriting files
            if os.path.exists(targetfile):
                counter = 1
                targetbase = targetfile+'_'
                while (counter < 1000):
                    targetfile = targetbase+str(counter)
                    if not os.path.exists(targetfile):
                        break
            #make sure the target directory exists
            if not (os.path.exists(targetdir)):
                os.makedirs(targetdir)
            #now move the file
            shutil.copyfile(result['download_file'],targetfile)
            if (res_type == "sad"):
                shutil.copyfile(result['shelx_tar'],targetfile.replace(result['download_file'],result['shelx_tar']))
            #return that we are successful
            return(True)
        else:
            return(False)
    
    except:
        logger.exception('Error in CopyToUser')
        return(False)

def TransferToUI(type,settings,result,trip,logger):
    """
    Transfer files using pexpect and rsync to the UI Server.
    
    type - single,pair,sad,mr
    """
    
    logger.debug('TransferToUI type:%s'%type)
    logger.debug(result)
    
    #Handle the transfer to ui being turned off
    if (not settings['xfer_to_ui']):
        logger.debug("Not transferring files to web server!")
        return(False)

    #import for decoding
    import base64

    #set up simpler versions of the host parameters
    host     = settings['ui_host']
    port     = settings['ui_port']
    username = settings['ui_user']
    password = base64.b64decode(settings['ui_password'])
    
    #try:
    #create the log file
    paramiko.util.log_to_file('/tmp/paramiko.log')
    #create the Transport instance
    transport = paramiko.Transport((host, port))
    #connect with username and password
    transport.connect(username = username, password = password)
    #establish sftp client
    sftp = paramiko.SFTPClient.from_transport(transport)
    
    #now transfer the files
    if type == 'single':
        dest_dir = os.path.join(settings['ui_user_dir'],trip['username'],str(trip['trip_id']),'single/')
        if result.has_key('summary_short'):
            if result['summary_short'] != 'None':
                counter = 0
                while (not os.path.exists(result['summary_short'])):
                    logger.debug('Waiting for %s to exist' % result['summary_short'])
                    time.sleep(1)
                    counter += 1
                    if (counter > 100):
                        break
                time.sleep(secret_settings_general['filesystem_delay'])
                logger.debug("sftp.put("+str(result['summary_short'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'short.php'])))+")")
                sftp.put(result['summary_short'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'short.php'])))
            
                if result.has_key('summary_long'):
                    if result['summary_long'] != 'None':
                        logger.debug("sftp.put("+str(result['summary_long'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'long.php'])))+")")
                        sftp.put(result['summary_long'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'long.php'])))

                if result.has_key('best_plots'):
                    if result['best_plots'] not in (None,'None','FAILED'):
                        logger.debug("sftp.put("+str(result['best_plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'plots.php'])))+")")
                        sftp.put(result['best_plots'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'plots.php']))) 
        
                if result.has_key('image_raw'):
                    if result['image_raw'] not in (None,'0'):
                        #make sure the file is complete
                        logger.debug("sftp.put("+str(result['image_raw'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'pyr_000_090.tif'])))+")")
                        sftp.put(result['image_raw'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'pyr_000_090.tif'])))        
                        time.sleep(2)

                if result.has_key('image_preds'):
                    if result['image_preds'] not in  (None,'0'):
                        #make sure the file is complete
                        logger.debug("sftp.put("+str(result['image_preds'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'pyr_100_090.tif'])))+")")
                        sftp.put(result['image_preds'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'pyr_100_090.tif'])))   

        if result.has_key('summary_stac'):
            if result['summary_stac'] != "None":
                logger.debug("sftp.put("+str(result['summary_stac'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'stac.php'])))+")")
                sftp.put(result['summary_stac'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'stac.php'])))
    
    elif type == 'single-orphan':
        dest_dir = os.path.join(settings['ui_user_dir'],'orphans/single/')
        if result.has_key('summary_short'):
            if result['summary_short']:
                counter = 0 
                while (not os.path.exists(result['summary_short'])):
                    logger.debug('Waiting for %s to exist' % result['summary_short'])
                    time.sleep(1)
                    counter += 1
                    if (counter > 100):
                        break
                logger.debug("sftp.put("+str(result['summary_short'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'short.php'])))+")")
                sftp.put(result['summary_short'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'short.php'])))
            
        if result.has_key('summary_long'):
            if result['summary_long']:
                logger.debug("sftp.put("+str(result['summary_long'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'long.php'])))+")")
                sftp.put(result['summary_long'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'long.php'])))
    
        if result.has_key('summary_stac'):
            if result['summary_stac'] not in (None,'None','FAILED'):
                logger.debug("sftp.put("+str(result['summary_stac'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'stac.php'])))+")")
                sftp.put(result['summary_stac'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'stac.php'])))
    
        if result.has_key('best_plots'):
            if result['best_plots'] not in (None,'None','FAILED'):
                logger.debug("sftp.put("+str(result['best_plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'plots.php'])))+")")
                sftp.put(result['best_plots'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'plots.php']))) 
                              
        if result.has_key('image_raw'):
            if result['image_raw'] not in (None,'0'):
                #make sure the file is complete
                while ((time.time() - os.stat(result['image_raw']).st_mtime) < 0.5):
                    time.sleep(0.5)
                logger.debug("sftp.put("+str(result['image_raw'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'pyr_000_090.tif'])))+")")
                sftp.put(result['image_raw'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'pyr_000_090.tif'])))        

        if result.has_key('image_preds'):
            if result['image_preds'] not in (None,'0'):
                #make sure the file is complete
                while ((time.time() - os.stat(result['image_preds']).st_mtime) < 0.5):
                    time.sleep(0.5)
                logger.debug("sftp.put("+str(result['image_preds'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'pyr_100_090.tif'])))+")")
                sftp.put(result['image_preds'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'pyr_100_090.tif']))) 

    ##########################################################################################################################           
    elif type == 'pair':
        logger.debug('Working on transferring a pair result')
        
        dest_dir = os.path.join(settings['ui_user_dir'],trip['username'],str(trip['trip_id']),'pair/')
        logger.debug('Destination: %s'%dest_dir)
        
        if result.has_key('summary_short'):
            if (result['summary_short'] not in (None,'None','0')):
                counter = 0 
                while (not os.path.exists(result['summary_short'])):
                    logger.debug('Waiting for %s to exist' % result['summary_short'])
                    time.sleep(1)
                    counter += 1
                    if (counter > 100):
                        break
                logger.debug("sftp.put("+str(result['summary_short'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'short.php'])))+")")
                sftp.put(result['summary_short'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'short.php'])))
            
        if result.has_key('summary_long'):
            if (result['summary_long'] not in (None,'None','0')):
                logger.debug("sftp.put("+str(result['summary_long'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'long.php'])))+")")
                sftp.put(  result['summary_long'],  os.path.join(dest_dir,'_'.join((str(result['pair_result_id']),'long.php')))  )
    
        if result.has_key('summary_stac'):
            logger.debug('STAC summary: %s' % result['summary_stac'])
            if (result['summary_stac'] not in (None,'None','0')):
                logger.debug("sftp.put("+str(result['summary_stac'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'stac.php'])))+")")
                sftp.put(result['summary_stac'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'stac.php'])))
    
        if result.has_key('best_plots'):
            if (result['best_plots'] not in (None,'None','0')):
                logger.debug("sftp.put("+str(result['best_plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'plots.php'])))+")")
                sftp.put(result['best_plots'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'plots.php']))) 

        if result.has_key('image_raw_1'):
            if (result['image_raw_1'] not in (None,'None','0')):
                #make sure the file is complete
                logger.debug("sftp.put("+str(result['image_raw_1'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_000_090.tif'])))+")")
                sftp.put(result['image_raw_1'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_000_090.tif'])))        

        if result.has_key('image_preds_1'):
            if (result['image_preds_1'] not in (None,'None','0')):
                #make sure the file is complete
                logger.debug("sftp.put("+str(result['image_preds_1'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_100_090.tif'])))+")")
                sftp.put(result['image_preds_1'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_100_090.tif']))) 
                
        if result.has_key('image_raw_2'):
            if (result['image_raw_2'] not in  (None,'None','0')):
                #make sure the file is complete
                logger.debug("sftp.put("+str(result['image_raw_2'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_200_090.tif'])))+")")
                sftp.put(result['image_raw_2'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_200_090.tif'])))        

        if result.has_key('image_preds_2'):
            if (result['image_preds_2'] not in  (None,'None','0')):
                #make sure the file is complete
                logger.debug("sftp.put("+str(result['image_preds_2'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_300_090.tif'])))+")")
                sftp.put(result['image_preds_2'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_300_090.tif']))) 
 
    elif type == 'pair-orphan':
        dest_dir = os.path.join(settings['ui_user_dir'],'orphans/pair/')
        if result.has_key('summary_short'):
            if result['summary_short']:
                counter = 0
                while (not os.path.exists(result['summary_short'])):
                    logger.debug('Waiting for %s to exist' % result['summary_short'])
                    time.sleep(1)
                    counter += 1
                    if (counter > 100):
                        break
                logger.debug("sftp.put("+str(result['summary_short'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'short.php'])))+")")
                sftp.put(result['summary_short'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'short.php'])))
                        
        if result.has_key('summary_long'):
            if result['summary_long']:
                logger.debug("sftp.put("+str(result['summary_long'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'long.php'])))+")")
                sftp.put(result['summary_long'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'long.php'])))
        
        if result.has_key('summary_stac'):
            if result['summary_stac'] != "None":
                logger.debug("sftp.put("+str(result['summary_stac'])+","+str(os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'stac.php'])))+")")
                sftp.put(result['summary_stac'],os.path.join(dest_dir,'_'.join([str(result['single_result_id']),'stac.php'])))
                
        if result.has_key('best_plots'):
            if result['best_plots']:
                logger.debug("sftp.put("+str(result['best_plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'plots.php'])))+")")
                sftp.put(result['best_plots'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'plots.php']))) 
  
        if result.has_key('image_raw_1'):
            if result['image_raw_1'] not in  (None,'0'):
                #make sure the file is complete
                while ((time.time() - os.stat(result['image_raw_1']).st_mtime) < 0.5):
                    time.sleep(0.5)
                logger.debug("sftp.put("+str(result['image_raw_1'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_000_090.tif'])))+")")
                sftp.put(result['image_raw_1'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_000_090.tif'])))

        if result.has_key('image_preds_1'):
            if result['image_preds_1'] not in  (None,'0'):
                #make sure the file is complete
                while ((time.time() - os.stat(result['image_preds_1']).st_mtime) < 0.5):
                    time.sleep(0.5)
                logger.debug("sftp.put("+str(result['image_preds_1'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_100_090.tif'])))+")")
                sftp.put(result['image_preds_1'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_100_090.tif'])))

        if result.has_key('image_raw_2'):
            if result['image_raw_2'] not in  (None,'0'):
                #make sure the file is complete
                while ((time.time() - os.stat(result['image_raw_2']).st_mtime) < 0.5):
                    time.sleep(0.5)
                logger.debug("sftp.put("+str(result['image_raw_2'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_200_090.tif'])))+")")
                sftp.put(result['image_raw_2'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_200_090.tif'])))

        if result.has_key('image_preds_2'):
            if result['image_preds_2'] not in  (None,'0'):
                #make sure the file is complete
                while ((time.time() - os.stat(result['image_preds_2']).st_mtime) < 0.5):
                    time.sleep(0.5)
                logger.debug("sftp.put("+str(result['image_preds_2'])+","+str(os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_300_090.tif'])))+")")
                sftp.put(result['image_preds_2'],os.path.join(dest_dir,'_'.join([str(result['pair_result_id']),'pyr_300_090.tif'])))

    ##########################################################################################################################           
    elif type == 'xia2':
                    
        dest_dir = os.path.join(settings['ui_user_dir'],trip['username'],str(trip['trip_id']),'run/')
        
        #XIA2 process has succeeded
        if result['integrate_status'] == 'SUCCESS':
            #The parsed file
            try:
                counter = 0
                while (not os.path.exists(result['parsed'])):
                    logger.debug('Waiting for %s to exist' % result['parsed'])
                    time.sleep(1)
                    counter += 1
                    if (counter > 100):
                        break
                time.sleep(1) #let the filesystem catch up
                logger.debug("sftp.put("+str(result['parsed'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))+")")
                sftp.put(result['parsed'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))
            except:
                pass
            #The XIA2 log file
            try:
                counter = 0
                while (not os.path.exists(result['xia_log'])):
                    logger.debug('Waiting for %s to exist' % result['xia_log'])
                    time.sleep(1)
                    counter += 1
                    if (counter > 100):
                        break
                time.sleep(1) #let the filesystem catch up
                logger.debug("sftp.put("+str(result['xia_log'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xia2.log'])))+")")
                sftp.put(result['xia_log'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xia2.log'])))
            except:
                logger.exception('Could not transfer xia_log')
                logger.debug("sftp.put("+str(result['xia_log'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xia2.log'])))+")")
            #The XSCALE log file    
            try:
                logger.debug("sftp.put("+str(result['xscale_log'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xscale.log'])))+")")
                sftp.put(result['xscale_log'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xscale.log'])))
            except:
                logger.exception('Could not transfer xscale_log')
            #The SCALA log file    
            try:                    
                logger.debug("sftp.put("+str(result['scala_log'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'scala.log'])))+")")
                sftp.put(result['scala_log'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'scale.log'])))
            except:
                logger.exception('Could not transfer scala_log')
            #The plots file    
            try:                    
                logger.debug("sftp.put("+str(result['plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'plots.php'])))+")")
                sftp.put(result['plots'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'plots.php'])))
            except:
                logger.exception('Could not transfer plots')
        #XIA2 process has failed
        else:
            #The XIA2 log file
            logger.debug("sftp.put("+str(result['xia_log'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xia2.log'])))+")")
            sftp.put(result['xia_log'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xia2.log'])))
               
                 
    elif type == 'xia2-orphan':
        dest_dir = os.path.join(settings['ui_user_dir'],'orphans/run/')
        #XIA2 process has succeeded
        if result['integrate_status'] == 'SUCCESS':
            #The parsed file
            try:
                count = 0
                while (not os.path.exists(result['parsed'])):
                    logger.debug('Waiting for %s to exist' % result['parsed'])
                    time.sleep(1)
                    counter += 1
                    if (counter > 100):
                        break
                logger.debug("sftp.put("+str(result['parsed'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))+")")
                sftp.put(result['parsed'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))
            except:
                logger.exception('Error transferring parsed file')
            #The XIA2 log file
            try:
                logger.debug("sftp.put("+str(result['xia_log'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xia2.log'])))+")")
                sftp.put(result['xia_log'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xia2.log'])))
            except:
                logger.exception('Could not transfer xia_log')
            #The XSCALE log file    
            try:
                logger.debug("sftp.put("+str(result['xscale_log'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xscale.log'])))+")")
                sftp.put(result['xscale_log'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xscale.log'])))
            except:
                logger.exception('Could not transfer XSCALE log file')
            #The SCALA log file    
            try:                    
                logger.debug("sftp.put("+str(result['scala_log'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'scala.log'])))+")")
                sftp.put(result['scala_log'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'scale.log'])))
            except:
                logger.exception('Could not transfer SCALA log file')
            #The plots file    
            try:                    
                logger.debug("sftp.put("+str(result['plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'plots.php'])))+")")
                sftp.put(result['plots'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'plots.php'])))
            except:
                logger.exception('Could not transfer plots file')
        #XIA2 process has failed
        else:
            #The XIA2 log file
            logger.debug("sftp.put("+str(result['xia_log'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xia2.log'])))+")")
            sftp.put(result['xia_log'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'xia2.log'])))
            
    ###########################################################################################################################################################        
    elif type == 'integrate':
                    
        dest_dir = os.path.join(settings['ui_user_dir'],trip['username'],str(trip['trip_id']),'run/')
        
        #fastintegrate process has succeeded
        if result['integrate_status'] in ('SUCCESS','WORKING'):
            #The parsed file
            try:
                counter = 0
                while (not os.path.exists(result['parsed'])):
                    logger.debug('Waiting for %s to exist' % result['parsed'])
                    time.sleep(1)
                    counter += 1
                    if (counter > 100):
                        break
                time.sleep(1) #let the filesystem catch up
                logger.debug("sftp.put("+str(result['parsed'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))+")")
                sftp.put(result['parsed'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))
            except:
                pass
            #The long summary file
            try:
                counter = 0
                while (not os.path.exists(result['summary_long'])):
                    logger.debug('Waiting for %s to exist' % result['summary_long'])
                    time.sleep(1)
                    counter += 1
                    if (counter > 100):
                        break
                time.sleep(1) #let the filesystem catch up
                logger.debug("sftp.put("+str(result['summary_long'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'long.php'])))+")")
                sftp.put(result['summary_long'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'long.php'])))
            except:
                pass
            #The plots file    
            try:                    
                logger.debug("sftp.put("+str(result['plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'plots.php'])))+")")
                sftp.put(result['plots'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'plots.php'])))
            except:
                logger.exception('Could not transfer plots')
        #process has failed
        else:
            #The parsed file
            try:
                counter = 0
                while (not os.path.exists(result['parsed'])):
                    logger.debug('Waiting for %s to exist' % result['parsed'])
                    time.sleep(1)
                    counter += 1
                    if (counter > 100):
                        break
                time.sleep(1) #let the filesystem catch up
                logger.debug("sftp.put("+str(result['parsed'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))+")")
                sftp.put(result['parsed'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))
            except:
                pass
            #The long summary file
            try:
                while (not os.path.exists(result['summary_long'])):
                    logger.debug('Waiting for %s to exist' % result['summary_long'])
                    time.sleep(1)
                time.sleep(1) #let the filesystem catch up
                logger.debug("sftp.put("+str(result['summary_long'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'long.php'])))+")")
                sftp.put(result['summary_long'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'long.php'])))
            except:
                pass            
            
    ###########################################################################################################################################################        
    elif type == 'integrate-orphan':
                    
        dest_dir = os.path.join(settings['ui_user_dir'],'orphans/run/')
        
        #fastintegrate process has succeeded
        if result['integrate_status'] in ('SUCCESS','WORKING'):
            #The parsed file
            try:
                counter = 0
                while (not os.path.exists(result['parsed'])):
                    logger.debug('Waiting for %s to exist' % result['parsed'])
                    time.sleep(1)
                    counter += 1
                    if (counter > 100):
                        break
                time.sleep(1) #let the filesystem catch up
                logger.debug("sftp.put("+str(result['parsed'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))+")")
                sftp.put(result['parsed'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))
            except:
                pass
            #The long summary file
            try:
                counter = 0
                while (not os.path.exists(result['summary_long'])):
                    logger.debug('Waiting for %s to exist' % result['summary_long'])
                    time.sleep(1)
                    counter += 1
                    if (counter > 100):
                        break
                time.sleep(1) #let the filesystem catch up
                logger.debug("sftp.put("+str(result['summary_long'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'long.php'])))+")")
                sftp.put(result['summary_long'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'long.php'])))
            except:
                pass
            #The plots file    
            try:                    
                logger.debug("sftp.put("+str(result['plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'plots.php'])))+")")
                sftp.put(result['plots'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'plots.php'])))
            except:
                logger.exception('Could not transfer plots')
        #process has failed
        else:
            #The parsed file
            try:
                counter = 0
                while (not os.path.exists(result['parsed'])):
                    logger.debug('Waiting for %s to exist' % result['parsed'])
                    time.sleep(1)
                    counter += 1
                    if (counter > 100):
                        break
                time.sleep(1) #let the filesystem catch up
                logger.debug("sftp.put("+str(result['parsed'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))+")")
                sftp.put(result['parsed'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'short.php'])))
            except:
                pass
            #The long summary file
            try:
                counter = 0
                while (not os.path.exists(result['summary_long'])):
                    logger.debug('Waiting for %s to exist' % result['summary_long'])
                    time.sleep(1)
                    counter += 1
                    if (counter > 100):
                        break
                time.sleep(1) #let the filesystem catch up
                logger.debug("sftp.put("+str(result['summary_long'])+","+str(os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'long.php'])))+")")
                sftp.put(result['summary_long'],os.path.join(dest_dir,'_'.join([str(result['integrate_result_id']),'long.php'])))
            except:
                pass   
    ##########################################################################################################################
    elif type == 'smerge':
                    
        dest_dir = os.path.join(settings['ui_user_dir'],trip['username'],str(trip['trip_id']),'merge/')
        
        #fastintegrate process has succeeded
        if result['merge_status'] in ('SUCCESS'):
            #The parsed file
            try:
                counter = 0
                while (not os.path.exists(result['summary'])):
                    logger.debug('Waiting for %s to exist' % result['summary'])
                    time.sleep(1)
                    counter += 1
                    if (counter > 100):
                        break
                time.sleep(1) #let the filesystem catch up
                logger.debug("sftp.put("+str(result['summary'])+","+str(os.path.join(dest_dir,'_'.join([str(result['merge_result_id']),'short.php'])))+")")
                sftp.put(result['summary'],os.path.join(dest_dir,'_'.join([str(result['merge_result_id']),'short.php'])))
            except:
                logger.exception('Could not transfer summary')
            #The long summary file
            try:
                counter = 0
                while (not os.path.exists(result['details'])):
                    logger.debug('Waiting for %s to exist' % result['details'])
                    time.sleep(1)
                    counter += 1
                    if (counter > 100):
                        break
                time.sleep(1) #let the filesystem catch up
                logger.debug("sftp.put("+str(result['details'])+","+str(os.path.join(dest_dir,'_'.join([str(result['merge_result_id']),'long.php'])))+")")
                sftp.put(result['details'],os.path.join(dest_dir,'_'.join([str(result['merge_result_id']),'long.php'])))
            except:
                logger.exception('Could not transfer details')
            #The plots file    
            try:                    
                logger.debug("sftp.put("+str(result['plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['merge_result_id']),'plots.php'])))+")")
                sftp.put(result['plots'],os.path.join(dest_dir,'_'.join([str(result['merge_result_id']),'plots.php'])))
            except:
                logger.exception('Could not transfer plots')
                     
    ##########################################################################################################################           
    elif type == 'sad':
        
        #the destination directory
        dest_dir = os.path.join(settings['ui_user_dir'],trip['username'],str(trip['trip_id']),'structure/')

        #Move file that should always exist
        #The shelx summary
        try:
            counter = 0
            while (not os.path.exists(result['shelx_html'])):
                logger.debug('Waiting for %s to exist' % result['shelx_html'])
                time.sleep(1)
                counter += 1
                if (counter > 100):
                    break
            time.sleep(1) #let the filesystem catch up
            logger.debug("sftp.put("+str(result['shelx_html'])+","+str(os.path.join(dest_dir,'_'.join([str(result['sad_result_id']),'shelx.php'])))+")")
            sftp.put(result['shelx_html'],os.path.join(dest_dir,'_'.join([str(result['sad_result_id']),'shelx.php'])))
        except:
            logger.debug('Error transferring %s to %s' %(result['shelx_html'],os.path.join(dest_dir,'_'.join([str(result['sad_result_id']),'shelx.php']))))
            
        #The shelx plots
        try:
            logger.debug("sftp.put("+str(result['shelx_plots'])+","+str(os.path.join(dest_dir,'_'.join([str(result['sad_result_id']),'shelx_plots.php'])))+")")
            sftp.put(result['shelx_plots'],os.path.join(dest_dir,'_'.join([str(result['sad_result_id']),'shelx_plots.php'])))
        except:
            logger.debug('Error transferring %s to %s' %(result['shelx_plots'],os.path.join(dest_dir,'_'.join([str(result['sad_result_id']),'shelx_plots.php']))))
        
        #The autosol results
        try:
            logger.debug("sftp.put("+str(result['autosol_html'])+","+str(os.path.join(dest_dir,'_'.join([str(result['sad_result_id']),'autosol.php'])))+")")
            sftp.put(result['autosol_html'],os.path.join(dest_dir,'_'.join([str(result['sad_result_id']),'autosol.php'])))
        except:
            logger.debug('Error transferring %s to %s' %(result['autosol_html'],os.path.join(dest_dir,'_'.join([str(result['sad_result_id']),'autosol.php']))))
        
    ##########################################################################################################################           
    elif type == 'mr':
        
        #the destination directory
        dest_dir = os.path.join(settings['ui_user_dir'],trip['username'],str(trip['trip_id']),'structure/')

        #Move file that should always exist
        #The summary
        try:
            counter = 0
            while (not os.path.exists(result['summary_html'])):
                logger.debug('Waiting for %s to exist' % result['summary_html'])
                time.sleep(1)
                counter += 1
                if (counter > 100):
                    break
            time.sleep(1) #let the filesystem catch up
            logger.debug("sftp.put("+str(result['summary_html'])+","+str(os.path.join(dest_dir,'_'.join([str(result['mr_result_id']),'mr.php'])))+")")
            sftp.put(result['summary_html'],os.path.join(dest_dir,'_'.join([str(result['mr_result_id']),'mr.php'])))
        except:
            logger.debug('Error transferring %s to %s' %(result['summary_html'],os.path.join(dest_dir,'_'.join([str(result['mr_result_id']),'mr.php']))))

    ##########################################################################################################################           
    elif type == 'stats':
        
        #the destination directory
        dest_dir = os.path.join(settings["ui_user_dir"],trip["username"],str(trip["trip_id"]),"run/")

        #Move file that should always exist
        files = [("cell_sum","stats_cellsum.php"),
                 ("xtriage_sum","stats_xtriagesum.php"),
                 ("xtriage_plots","stats_xtriageplots.php"),
                 ("molrep_sum","stats_molrepsum.php"),
                 ("molrep_img","stats_molrep.jpg")]
        
        #The summary
        for src,dest in files:
            try:
                counter = 0
                while (not os.path.exists(result[src])):
                    logger.debug('Waiting for %s to exist' % result[src])
                    time.sleep(1)
                    counter += 1
                    if (counter > 100):
                        break
                time.sleep(1) #let the filesystem catch up
                logger.debug("sftp.put("+str(result[src])+","+str(os.path.join(dest_dir,'_'.join([str(result['result_id']),dest])))+")")
                sftp.put(result[src],os.path.join(dest_dir,'_'.join([str(result['result_id']),dest])))
            except:
                logger.debug('Error transferring %s to %s' %(result[src],os.path.join(dest_dir,'_'.join([str(result['result_id']),dest]))))  
                   
                   
    elif type == 'stats-orphan':
        
        #the destination directory
        dest_dir = os.path.join(settings["ui_user_dir"],"orphans/run/")

        #Move file that should always exist
        files = [("cell_sum","stats_cellsum.php"),
                 ("xtriage_sum","stats_xtriagesum.php"),
                 ("xtriage_plots","stats_xtriageplots.php"),
                 ("molrep_sum","stats_molrepsum.php"),
                 ("molrep_img","stats_molrep.jpg")]
        
        #The summary
        for src,dest in files:
            try:
                counter = 0
                while (not os.path.exists(result[src])):
                    logger.debug('Waiting for %s to exist' % result[src])
                    time.sleep(1)
                    counter += 1
                    if (counter > 100):
                        break
                time.sleep(1) #let the filesystem catch up
                logger.debug("sftp.put("+str(result[src])+","+str(os.path.join(dest_dir,'_'.join([str(result['result_id']),dest])))+")")
                sftp.put(result[src],os.path.join(dest_dir,'_'.join([str(result['result_id']),dest])))
            except:
                logger.debug('Error transferring %s to %s' %(result[src],os.path.join(dest_dir,'_'.join([str(result['result_id']),dest])))) 
    ##########################################################################################################################           
    elif type == 'download':
        dest_dir = os.path.join(settings['ui_user_dir'],trip['username'],str(trip['trip_id']),'download/')
        if result.has_key('archive'):
            if result['archive']:
                counter = 0
                while (not os.path.exists(result['archive'])):
                    logger.debug('Waiting for %s to exist' % result['archive'])
                    time.sleep(1)
                    counter += 1
                    if (counter > 100):
                        break
                logger.debug("sftp.put("+str(result['archive'])+","+str(os.path.join(dest_dir,os.path.basename(result['archive'])))+")")
                sftp.put(result['archive'],os.path.join(dest_dir,os.path.basename(result['archive'])))   
            
    ##########################################################################################################################                           
    #close out the connection
    sftp.close()
    transport.close()  
    return(True)
    """
    except:
        #close out the connection
        sftp.close()
        transport.close()
        return(False)
   """ 
