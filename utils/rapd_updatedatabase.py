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
Designed to help update the rapd database from major revision and distributed systems
"""

import getpass
import MySQLdb,_mysql_exceptions
from rapd_beamlinespecific import secret_settings_general

class UpdateDB:
    """
    Given host,user,password and new db name, updates a database to a certain
    specification
    
    This relies on the database being up to version 1
    """
    def __init__(self,host,user,passwd,verbose=True):
        
        if verbose:
            print 'MakeDB::__init__'
        
        #passed-in variables    
        self.host    = host
        self.user    = user
        self.passwd  = passwd
        self.verbose = verbose
        
    def getVersion(self):
        """
        Get the version of the database which we are starting with
        """
        conn = MySQLdb.connect(host=self.host,user=self.user,passwd=self.passwd)
        curs = conn.cursor()
        
        #
        # Settings
        # 
        tblcmd = '''select version FROM rapd_data.version'''
        curs.execute(tblcmd)
        version = curs.fetchone()[0]
         
        #close the connection
        curs.close()
        conn.close()
        
        #return the data
        return(version)
        
    def Update_1_2(self):
        """
        Update rapd_data from version 1 to 2
        """
        if self.verbose:
            print 'RapdData_1_2'

        conn = MySQLdb.connect(host=self.host,user=self.user,passwd=self.passwd)
        curs = conn.cursor()
        
        #
        # rapd_data.images
        # 
        try:
            curs.execute('ALTER TABLE rapd_data.images ADD flux FLOAT AFTER beamline') 
            curs.execute('ALTER TABLE rapd_data.images ADD beam_size_x FLOAT AFTER flux')
            curs.execute('ALTER TABLE rapd_data.images ADD beam_size_y FLOAT AFTER beam_size_x')
            curs.execute('ALTER TABLE rapd_data.images ADD gauss_x FLOAT AFTER beam_size_y')
            curs.execute('ALTER TABLE rapd_data.images ADD gauss_y FLOAT AFTER gauss_x')
        
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Trouble updating from 1 to 2'
        
        #close the connection
        curs.close()
        conn.close()
                
        #
        # Update the version number
        #               
        self.UpdateVersion(2)

    def Update_2_3(self):
        """
        Update rapd_data from version 2 to 3
        """
        if self.verbose:
            print 'RapdData_2_3'

        conn = MySQLdb.connect(host=self.host,user=self.user,passwd=self.passwd)
        curs = conn.cursor()
        
        #
        # rapd_data.images
        # 
        try:
            #add mosflm settings
            curs.execute('ALTER TABLE rapd_data.settings ADD mosflm_seg TINYINT UNSIGNED AFTER best_complexity') 
            curs.execute('ALTER TABLE rapd_data.settings ADD mosflm_rot FLOAT AFTER mosflm_seg')
            #drop anomalous, transmission and user_dir settings
            curs.execute('ALTER TABLE rapd_data.settings DROP COLUMN anomalous')
            curs.execute('ALTER TABLE rapd_data.settings DROP COLUMN user_dir_override')
            curs.execute('ALTER TABLE rapd_data.settings DROP COLUMN user_directory')
            curs.execute('ALTER TABLE rapd_data.settings DROP COLUMN transmission')
            
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Trouble updating from 2 to 3'
        
        #close the connection
        curs.close()
        conn.close()
                
        #
        # Update the version number
        #               
        self.UpdateVersion(3)
    
    def Update_3_4(self):
        """
        Update rapd_data from version 3 to 4
        """
        if self.verbose:
            print 'RapdData_3_4'

        conn = MySQLdb.connect(host=self.host,user=self.user,passwd=self.passwd)
        curs = conn.cursor()
        
        #
        # rapd_data.images
        # 
        try:
            #add run_id to integrate_results
            curs.execute('ALTER TABLE rapd_data.integrate_results ADD run_id MEDIUMINT UNSIGNED AFTER result_id') 
            #add some id's to various tables
            curs.execute('ALTER TABLE rapd_data.images ADD sample_id MEDIUMINT UNSIGNED AFTER sample')
            curs.execute('ALTER TABLE rapd_data.single_results ADD sample_id MEDIUMINT UNSIGNED AFTER date')
            curs.execute('ALTER TABLE rapd_data.single_results ADD process_id MEDIUMINT UNSIGNED AFTER result_id')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD sample_id MEDIUMINT UNSIGNED AFTER date_2')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD process_id MEDIUMINT UNSIGNED AFTER result_id')
            curs.execute('ALTER TABLE rapd_data.integrate_results ADD sample_id MEDIUMINT UNSIGNED AFTER run_id')
            curs.execute('ALTER TABLE rapd_data.integrate_results ADD process_id MEDIUMINT UNSIGNED AFTER result_id')
            #move the best_complexity column around
            curs.execute('ALTER TABLE rapd_data.single_results ADD COLUMN temp varchar(8) AFTER raddose_exp_dose_limit')
            curs.execute('UPDATE rapd_data.single_results SET temp = best_complexity')
            curs.execute('ALTER TABLE rapd_data.single_results DROP best_complexity')
            curs.execute('ALTER TABLE rapd_data.single_results CHANGE COLUMN temp best_complexity VARCHAR(8)')
            #add the normal mode results to the single_results table
            curs.execute('ALTER TABLE rapd_data.single_results CHANGE best_status best_norm_status VARCHAR(8)')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_norm_res_limit FLOAT AFTER best_norm_status')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_norm_completeness FLOAT AFTER best_norm_res_limit')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_norm_atten FLOAT AFTER best_norm_completeness')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_norm_rot_range FLOAT AFTER best_norm_atten')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_norm_phi_end FLOAT AFTER best_norm_rot_range')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_norm_total_exp FLOAT AFTER best_norm_phi_end')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_norm_redundancy FLOAT AFTER best_norm_total_exp')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_norm_i_sigi_all FLOAT AFTER best_norm_redundancy')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_norm_i_sigi_high FLOAT AFTER best_norm_i_sigi_all')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_norm_r_all FLOAT AFTER best_norm_i_sigi_high')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_norm_r_high FLOAT AFTER best_norm_r_all')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_norm_unique_in_blind FLOAT AFTER best_norm_r_high')
            #add the anomalous mode results to the single_results table
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_anom_status VARCHAR(8) AFTER best_norm_unique_in_blind')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_anom_res_limit FLOAT AFTER best_anom_status')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_anom_completeness FLOAT AFTER best_anom_res_limit')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_anom_atten FLOAT AFTER best_anom_completeness')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_anom_rot_range FLOAT AFTER best_anom_atten')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_anom_phi_end FLOAT AFTER best_anom_rot_range')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_anom_total_exp FLOAT AFTER best_anom_phi_end')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_anom_redundancy FLOAT AFTER best_anom_total_exp')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_anom_i_sigi_all FLOAT AFTER best_anom_redundancy')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_anom_i_sigi_high FLOAT AFTER best_anom_i_sigi_all')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_anom_r_all FLOAT AFTER best_anom_i_sigi_high')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_anom_r_high FLOAT AFTER best_anom_r_all')
            curs.execute('ALTER TABLE rapd_data.single_results ADD best_anom_unique_in_blind FLOAT AFTER best_anom_r_high')
            #Alter the mosflm results columns
            curs.execute('ALTER TABLE rapd_data.single_results CHANGE mosflm_status mosflm_norm_status VARCHAR(8)')
            curs.execute('ALTER TABLE rapd_data.single_results ADD mosflm_norm_res_limit FLOAT AFTER mosflm_norm_status')
            curs.execute('ALTER TABLE rapd_data.single_results ADD mosflm_norm_completeness FLOAT AFTER mosflm_norm_res_limit')
            curs.execute('ALTER TABLE rapd_data.single_results ADD mosflm_norm_redundancy FLOAT AFTER mosflm_norm_completeness')
            curs.execute('ALTER TABLE rapd_data.single_results ADD mosflm_norm_distance FLOAT AFTER mosflm_norm_redundancy')
            curs.execute('ALTER TABLE rapd_data.single_results ADD mosflm_norm_delta_phi FLOAT AFTER mosflm_norm_distance')
            curs.execute('ALTER TABLE rapd_data.single_results ADD mosflm_norm_img_exposure_time FLOAT AFTER mosflm_norm_delta_phi')
            #add the anomalous mode results to the single_results table
            curs.execute('ALTER TABLE rapd_data.single_results ADD mosflm_anom_status VARCHAR(8) AFTER mosflm_norm_img_exposure_time')
            curs.execute('ALTER TABLE rapd_data.single_results ADD mosflm_anom_res_limit FLOAT AFTER mosflm_anom_status')
            curs.execute('ALTER TABLE rapd_data.single_results ADD mosflm_anom_completeness FLOAT AFTER mosflm_anom_res_limit')
            curs.execute('ALTER TABLE rapd_data.single_results ADD mosflm_anom_redundancy FLOAT AFTER mosflm_anom_completeness')
            curs.execute('ALTER TABLE rapd_data.single_results ADD mosflm_anom_distance FLOAT AFTER mosflm_anom_redundancy')
            curs.execute('ALTER TABLE rapd_data.single_results ADD mosflm_anom_delta_phi FLOAT AFTER mosflm_anom_distance')
            curs.execute('ALTER TABLE rapd_data.single_results ADD mosflm_anom_img_exposure_time FLOAT AFTER mosflm_anom_delta_phi')
            #move the best_complexity column around  in the pair_results table
            curs.execute('ALTER TABLE rapd_data.pair_results ADD COLUMN temp varchar(8) AFTER raddose_exp_dose_limit')
            curs.execute('UPDATE rapd_data.pair_results SET temp = best_complexity')
            curs.execute('ALTER TABLE rapd_data.pair_results DROP best_complexity')
            curs.execute('ALTER TABLE rapd_data.pair_results CHANGE COLUMN temp best_complexity VARCHAR(8)')
            #add more detailed normal strategy columns to the pair_results table
            curs.execute('ALTER TABLE rapd_data.pair_results CHANGE best_status best_norm_status VARCHAR(8)')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_norm_res_limit FLOAT AFTER best_norm_status')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_norm_completeness FLOAT AFTER best_norm_res_limit')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_norm_atten FLOAT AFTER best_norm_completeness')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_norm_rot_range FLOAT AFTER best_norm_atten')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_norm_phi_end FLOAT AFTER best_norm_rot_range')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_norm_total_exp FLOAT AFTER best_norm_phi_end')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_norm_redundancy FLOAT AFTER best_norm_total_exp')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_norm_i_sigi_all FLOAT AFTER best_norm_redundancy')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_norm_i_sigi_high FLOAT AFTER best_norm_i_sigi_all')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_norm_r_all FLOAT AFTER best_norm_i_sigi_high')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_norm_r_high FLOAT AFTER best_norm_r_all')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_norm_unique_in_blind FLOAT AFTER best_norm_r_high')
            #add more detailed anomalous strategy columns to the pair_results table
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_anom_status VARCHAR(8) AFTER best_norm_unique_in_blind')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_anom_res_limit FLOAT AFTER best_anom_status')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_anom_completeness FLOAT AFTER best_anom_res_limit')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_anom_atten FLOAT AFTER best_anom_completeness')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_anom_rot_range FLOAT AFTER best_anom_atten')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_anom_phi_end FLOAT AFTER best_anom_rot_range')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_anom_total_exp FLOAT AFTER best_anom_phi_end')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_anom_redundancy FLOAT AFTER best_anom_total_exp')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_anom_i_sigi_all FLOAT AFTER best_anom_redundancy')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_anom_i_sigi_high FLOAT AFTER best_anom_i_sigi_all')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_anom_r_all FLOAT AFTER best_anom_i_sigi_high')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_anom_r_high FLOAT AFTER best_anom_r_all')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD best_anom_unique_in_blind FLOAT AFTER best_anom_r_high')
            #Alter the mosflm results columns in pair_results
            curs.execute('ALTER TABLE rapd_data.pair_results CHANGE mosflm_status mosflm_norm_status VARCHAR(8)')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD mosflm_norm_res_limit FLOAT AFTER mosflm_norm_status')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD mosflm_norm_completeness FLOAT AFTER mosflm_norm_res_limit')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD mosflm_norm_redundancy FLOAT AFTER mosflm_norm_completeness')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD mosflm_norm_distance FLOAT AFTER mosflm_norm_redundancy')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD mosflm_norm_delta_phi FLOAT AFTER mosflm_norm_distance')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD mosflm_norm_img_exposure_time FLOAT AFTER mosflm_norm_delta_phi')
            #add the anomalous mode results to the pair_results table
            curs.execute('ALTER TABLE rapd_data.pair_results ADD mosflm_anom_status VARCHAR(8) AFTER mosflm_norm_img_exposure_time')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD mosflm_anom_res_limit FLOAT AFTER mosflm_anom_status')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD mosflm_anom_completeness FLOAT AFTER mosflm_anom_res_limit')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD mosflm_anom_redundancy FLOAT AFTER mosflm_anom_completeness')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD mosflm_anom_distance FLOAT AFTER mosflm_anom_redundancy')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD mosflm_anom_delta_phi FLOAT AFTER mosflm_anom_distance')
            curs.execute('ALTER TABLE rapd_data.pair_results ADD mosflm_anom_img_exposure_time FLOAT AFTER mosflm_anom_delta_phi')
            #unused columns
            curs.execute('ALTER TABLE rapd_data.single_results DROP html_image_file')
            #change to only username
            curs.execute('ALTER TABLE rapd_users.trips CHANGE user_name username VARCHAR(48)')
            #create the table for in-process display
            tblcmd = '''CREATE TABLE rapd_data.processes ( process_id    MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                           type          VARCHAR(12),
                                                           rtype         VARCHAR(12),
                                                           repr          VARCHAR(128), 
                                                           data_root_dir VARCHAR(256),
                                                           display       VARCHAR(12) DEFAULT 'show',
                                                           progress      TINYINT UNSIGNED DEFAULT 0,
                                                           timestamp1    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                           timestamp2    TIMESTAMP,
                                                           PRIMARY KEY   (process_id))'''
            curs.execute(tblcmd)
            #create strategy_wedges to store data from strategy pipeline
            tblcmd = '''CREATE TABLE strategy_wedges ( strategy_wedge_id  MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                                       id                 MEDIUMINT UNSIGNED NOT NULL,
                                                       int_type           VARCHAR(12),
                                                       strategy_type      VARCHAR(12),
                                                       run_number         TINYINT UNSIGNED,
                                                       phi_start          FLOAT,
                                                       number_images      SMALLINT UNSIGNED,
                                                       delta_phi          FLOAT,
                                                       overlap            VARCHAR(4),
                                                       distance           FLOAT,
                                                       exposure_time      FLOAT,
                                                       timestamp          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                       PRIMARY KEY        (strategy_wedge_id))'''
            
            curs.execute(tblcmd)
            #alter the cloud_state table for more functionality
            curs.execute('ALTER TABLE rapd_cloud.cloud_state CHANGE active_allowed everything TINYINT UNSIGNED')
            curs.execute('ALTER TABLE rapd_cloud.cloud_state CHANGE inactive_allowed processing TINYINT UNSIGNED')
            curs.execute('ALTER TABLE rapd_cloud.cloud_state ADD download TINYINT UNSIGNED AFTER processing')
            curs.execute('ALTER TABLE rapd_cloud.cloud_state ADD remote_proccessing TINYINT UNSIGNED AFTER download')
            curs.execute('ALTER TABLE rapd_cloud.cloud_state ADD remote_download TINYINT UNSIGNED AFTER remote_proccessing')
            curs.execute('ALTER TABLE rapd_cloud.cloud_state ADD remote_concurrent_allowed SMALLINT UNSIGNED AFTER remote_download')
            curs.execute('ALTER TABLE rapd_cloud.cloud_state ADD current_queue SMALLINT UNSIGNED AFTER remote_concurrent_allowed')
            
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Trouble updating from 3 to 4'
        
        #close the connection
        curs.close()
        conn.close()
                
        #
        # Update the version number
        #               
        self.UpdateVersion(4)   
        
    def UpdateVersion(self,new_version):
        """
        Update rapd_data.version to new value
        """
        if self.verbose:
            print 'UpdateVersion %d' % new_version

        conn = MySQLdb.connect(host=self.host,user=self.user,passwd=self.passwd)
        curs = conn.cursor()
        
        #
        # Update the version number
        #
        tblcmd = 'UPDATE rapd_data.version SET version=%d WHERE version=%d'
                
        try:
            curs.execute(tblcmd % (new_version,new_version-1))
        except _mysql_exceptions.OperationalError:
            if self.verbose:
                print 'Trouble updating version table'               
         
        #close the connection
        curs.close()
        conn.close()
  
            

if __name__ == '__main__':
    
    print 'rapd_updatedatabase.py'
    print '======================'
    
    #get the host name
    msg1    = '\nInput host of MySQL database: '
    select1 = raw_input(msg1).strip()
    if select1:
        try:
            my_hostname =  str(select1)
        except:
            print 'Error obtaining host name, Goodbye.\n'
            
    #get the user name
    msg2    = '\nInput user name: '
    select2 = raw_input(msg2).strip()
    if select2:
        try:
            my_username =  str(select2)
        except:
            print 'Error obtaining user name, Goodbye.\n'
            
    #get the password
    msg3    = '\nInput password: '
#    select3 = raw_input(msg3).strip()
    select3 = getpass.getpass(msg3).strip()
    if select3:
        try:
            my_password =  str(select3)
        except:
            print 'Error obtaining password, Goodbye.\n'
    
    
    #Get the curent database version
    tmp = UpdateDB(host=my_hostname,user=my_username,passwd=my_password,verbose=True)
    start_version = tmp.getVersion()
    
    max_version = 4
    print 'Current database version: %d' % start_version
    print 'Highest update version: %d' % max_version
    
    if (start_version < max_version):
        print 'V    Description'
        print '==   ====================================================='
    
    if start_version < 2:
        print '2    Add beam properties to the database'
    if start_version < 3:
        print '3    Settings changes'
    if start_version < 4:
        print '4    Adds run_id to integrate_results'
        
    #now ask where to update to   
    msg4 =  '\nVersion to update to: '
    select4 = raw_input(msg4).strip()
    if (select4):
        try:
            update_version =  int(select4)
        except:
            print 'Error in entering version number, Goodbye.\n'
        
    #Error if the current version is higher than selected
    if (update_version < start_version):
        print 'Your database is already at a higher version than %d' % update_version
        exit()
    
    cur_version = start_version
    while (cur_version < update_version+1):
        print 'Update from version %d to %d' %(cur_version,cur_version+1)
        
        #From 1 to 2
        if (cur_version == 1):
            tmp.Update_1_2()
        if (cur_version == 2):
            tmp.Update_2_3()
        if (cur_version == 3):
            tmp.Update_3_4()
        cur_version += 1
            
