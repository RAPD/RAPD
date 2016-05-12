"""
This is an adapter for RAPD to connect to the control database when it is a MySQL
type database.
"""

__license__ = """
This file is part of RAPD

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

__created__ = "2009-07-08"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

"""
To run a mariadb instance in docker:
sudo docker run --name mariadb -v /home/schuerjp/data:/var/lib/mysql -p 3306:3306
            -e MYSQL_ROOT_PASSWORD=root_password -d mariadb
"""

# Standard imports
import json
import logging
import operator
import os
import threading
import time

import numpy
import pymysql

MYSQL_ATTEMPTS = 30

class Database(object):
    """
    Provides connection to MySQL database for Model.
    """
    def __init__(self,
                 host=None,
                 port=3306,
                 user=None,
                 password=None,
                 settings=None):

        """
        Initialize the adapter

        Keyword arguments
        host --
        port --
        user --
        password --
        settings --
        """

        # Get the logger
        self.logger = logging.getLogger("RAPDLogger")

        # Store passed in variables
        # Using the settings "shorthand"
        if settings:
            self.db_host = settings["DATABASE_HOST"]
            self.db_port = settings["DATABASE_PORT"]
            self.db_user = settings["DATABASE_USER"]
            self.db_password = settings["DATABASE_PASSWORD"]
            # self.db_data_name = settings["DATABASE_NAME_DATA"]
            # self.db_users_name = settings["DATABASE_NAME_USERS"]
            # self.db_cloud_name = settings["DATABASE_NAME_CLOUD"]
        # Olde Style
        else:
            self.db_host = host
            self.db_port = port
            self.db_user = user
            self.db_password = password
            # self.db_data_name = data_name
            # self.db_users_name = users_name
            # self.db_cloud_name = cloud_name

        # A lock for troublesome fast-acting data entry
        self.LOCK = threading.Lock()

    ############################################################################
    #Functions for connecting to the database                                  #
    ############################################################################

    def get_db_connection(self):
        """
        Returns a connection and cursor for interaction with the database.
        """
        attempts = 0
        while attempts < MYSQL_ATTEMPTS:
            try:
                # Connect
                connection = pymysql.connect(host=self.db_host,
                                             port=self.db_port,
                                             db="rapd",
                                             user=self.db_user,
                                             password=self.db_password)
                cursor = connection.cursor()
                cursor.execute("SET AUTOCOMMIT=1")
                return(connection, cursor)
            except:
                self.logger.exception("Error connecting to MySQL server")
                attempts += 1
                time.sleep(10)

    def get_db_connection(self):
        """
        Returns a connection and cursor for interaction with the database.
        """
        attempts = 0
        while attempts < MYSQL_ATTEMPTS:
            try:
                # Connect
                connection = pymysql.connect(host=self.db_host,
                                             port=self.db_port,
                                             db="rapd",
                                             user=self.db_user,
                                             password=self.db_password)
                cursor = connection.cursor()
                cursor.execute("SET AUTOCOMMIT=1")
                return(connection, cursor)
            except:
                self.logger.exception("Error connecting to MySQL server")
                attempts += 1
                time.sleep(10)

    def connect_to_user(self):
        """
        Returns a connection and cursor for interaction with the database.
        """
        attempts = 0
        while attempts < MYSQL_ATTEMPTS:
            try:
                # Connect
                connection = pymysql.connect(host=self.db_host,
                                             port=self.db_port,
                                             db=self.db_users_name,
                                             user=self.db_user,
                                             password=self.db_password)
                cursor = connection.cursor()
                cursor.execute("SET AUTOCOMMIT=1")
                return(connection, cursor)
            except:
                self.logger.exception("Error connecting to MySQL server")
                attempts += 1
                time.sleep(10)

    def connect_to_cloud(self):
        """
        Returns a connection and cursor for interaction with the database.
        """
        attempts = 0
        while attempts < MYSQL_ATTEMPTS:
            try:
                # Connect
                connection = pymysql.connect(host=self.db_host,
                                             port=self.db_port,
                                             db=self.db_cloud_name,
                                             user=self.db_user,
                                             password=self.db_password)
                cursor = connection.cursor()
                cursor.execute("SET AUTOCOMMIT=1")
                return(connection, cursor)
            except:
                self.logger.exception("Error connecting to MySQL server")
                attempts += 1
                time.sleep(10)

    def closeConnection(self, connection, cursor):
        try:
            cursor.close()
        except:
            self.logger.exception("Error closing cursor to MySQL database")
        try:
            connection.close()
        except:
            self.logger.exception("Error closing connection to MySQL database")

    ############################################################################
    # Functions for images                                                     #
    ############################################################################
    def add_image(self, data):
        """
        Add new image to the MySQL database.
        """

        self.logger.debug(data)

        connection, cursor = self.get_db_connection()

        cursor.execute("""INSERT INTO images (beam_center_calc_x,
                                              beam_center_calc_y,
                                              beam_center_x,
                                              beam_center_y,
                                              beam_gauss_x,
                                              beam_gauss_y,
                                              beam_size_x,
                                              beam_size_y,
                                              binning,
                                              collect_mode,
                                              date,
                                              detector,
                                              detector_sn,
                                              distance,
                                              energy,
                                              flux,
                                              fullname,
                                              image_number,
                                              kappa,
                                              omega,
                                              osc_axis,
                                              osc_range,
                                              osc_start,
                                              phi,
                                              period,
                                              pixel_size,
                                              prefix,
                                              rapd_detector_id,
                                              robot_position,
                                              run_id,
                                              run_number,
                                              sample_id,
                                              sample_pos_x,
                                              sample_pos_y,
                                              sample_pos_z,
                                              site_tag,
                                              size1,
                                              size2,
                                              source_current,
                                              source_mode,
                                              time,
                                              transmission,
                                              twotheta) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                       (data.get("beam_center_calc_x", None),
                        data.get("beam_center_calc_y", None),
                        data.get("beam_center_x", None),
                        data.get("beam_center_y", None),
                        data.get("beam_gauss_x", None),
                        data.get("beam_gauss_y", None),
                        data.get("beam_size_x", None),
                        data.get("beam_size_y", None),
                        data.get("binning", None),
                        data.get("collect_mode", None),
                        data.get("date", None),
                        data.get("detector", None),
                        data.get("detector_sn", None),
                        data.get("distance", None),
                        data.get("energy", None),
                        data.get("flux", None),
                        data.get("fullname", None),
                        data.get("image_number", None),
                        data.get("kappa", None),
                        data.get("omega", None),
                        data.get("osc_axis", None),
                        data.get("osc_range", None),
                        data.get("osc_start", None),
                        data.get("period", None),
                        data.get("phi", None),
                        data.get("pixel_size", None),
                        data.get("prefix", None),
                        data.get("rapd_detector_id", None),
                        data.get("robot_position", None),
                        data.get("run_id", None),
                        data.get("run_number", None),
                        data.get("sample_id", None),
                        data.get("sample_pos_x", None),
                        data.get("sample_pos_y", None),
                        data.get("sample_pos_z", None),
                        data.get("site_tag", None),
                        data.get("size1", None),
                        data.get("size_2", None),
                        data.get("source_current", None),
                        data.get("source_mode", None),
                        data.get("time", None),
                        data.get("transmission", None),
                        data.get("twotheta", None)))

        # Put the image_id in the dict for future use
        image_id = cursor.lastrowid

        self.closeConnection(connection, cursor)

        # Now grab the dict from the MySQL table
        image_dict = self.get_image_by_image_id(image_id=image_id)

        return(image_dict, True)

    def add_pilatus_image(self, data):
        """
        Add new Pilatus image to the MySQL database.
        """

        self.logger.debug("Database::add_pilatus_image")
        self.logger.debug(data)
        connection, cursor = self.get_db_connection()

        try:
            cursor.execute("""INSERT INTO images (fullname,
                                                  axis,
                                                  beam_center_x,
                                                  beam_center_y,
                                                  count_cutoff,
                                                  date,
                                                  detector,
                                                  detector_sn,
                                                  collect_mode,
                                                  site,
                                                  distance,
                                                  osc_range,
                                                  osc_start,
                                                  phi,
                                                  kappa,
                                                  pixel_size,
                                                  time,
                                                  period,
                                                  twotheta,
                                                  wavelength,
                                                  directory,
                                                  image_prefix,
                                                  run_number,
                                                  image_number,
                                                  transmission,
                                                  puck,
                                                  sample,
                                                  ring_current,
                                                  ring_mode,
                                                  md2_aperture,
                                                  md2_x,
                                                  md2_y,
                                                  md2_z,
                                                  flux,
                                                  beam_size_x,
                                                  beam_size_y,
                                                  gauss_x,
                                                  gauss_y,
                                                  run_id) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                                                                   (data['fullname'],
                                                                    data['axis'],
                                                                    data['x_beam'],
                                                                    data['y_beam'],
                                                                    data['count_cutoff'],
                                                                    data['date'],
                                                                    data['detector'],
                                                                    data['detector_sn'],
                                                                    data['collect_mode'],
                                                                    data['site'],
                                                                    data['distance'],
                                                                    data['osc_range'],
                                                                    data['osc_start'],
                                                                    data['phi'],
                                                                    data['kappa'],
                                                                    data['pixel_size'],
                                                                    data['time'],
                                                                    data['period'],
                                                                    data['twotheta'],
                                                                    data['wavelength'],
                                                                    data['directory'],
                                                                    data['image_prefix'],
                                                                    data['run_number'],
                                                                    data['image_number'],
                                                                    data['transmission'],
                                                                    data['puck'],
                                                                    data['sample'],
                                                                    data['ring_current'],
                                                                    data['ring_mode'],
                                                                    data['md2_aperture'],
                                                                    data['md2_x'],
                                                                    data['md2_y'],
                                                                    data['md2_z'],
                                                                    data['flux'],
                                                                    data['beam_size_x'],
                                                                    data['beam_size_y'],
                                                                    data['gauss_x'],
                                                                    data['gauss_y'],
                                                                    data['run_id']))
            #connection.commit()
            #put the image_id in the dict for future use
            image_id = cursor.lastrowid

            self.closeConnection(connection, cursor)

            #now grab the dict from the MySQL table
            image_dict = self.get_image_by_image_id(image_id=image_id)

            return(image_dict, True)

        except pymysql.IntegrityError, (errno, strerror):
            self.closeConnection(connection, cursor)
            if errno == 1062:
                self.logger.warning('%s is already in the database' % data['fullname'])
                #check if this image is in one of the special use image sets and try to add anyway
                return(data, False)
            else:
                self.logger.exception('ERROR : unknown IntegrityError exception in Database::add_pilatus_image')
                self.logger.warning(errno)
                self.logger.warning(strerror)
            return(False)

        except:
            self.logger.exception('ERROR : unknown exception in Database::add_pilatus_image')
            self.closeConnection(connection,cursor)
            return(False)

    def updateImageCBC(self,image_id,cbcx,cbcy):
        """
        Updates the calc_beam_center_x/y for a given image_id.

        image_id - an int that indexes the rapd_data.images table
        cbcx - float of the X beam center in mm
        cbcy - float of the Y beam center in mm

        """

        self.logger.debug('Database::updateImageCBC image_id: %d, cbcx: %d, cbcy: %d' % (image_id,cbcx,cbcy))
        connection,cursor = self.get_db_connection()

        try:
            cursor.execute('UPDATE images set calc_beam_center_x=%s, calc_beam_center_y=%s WHERE image_id=%s',(cbcx,cbcy,image_id))
            self.closeConnection(connection,cursor)
            return(True)
        except:
            self.logger.exception('Exception in updating calculated beam center values in database')
            self.closeConnection(connection,cursor)

    def get_image_by_image_id(self, image_id):
        """
        Returns a dict from the database when queried with image_id.

        image_id - an int that indexes the rapd_data.images table
        """

        self.logger.debug("Database::get_image_by_image_id %d", image_id)

        query1 = "SELECT * FROM images WHERE image_id=%s"
        image_dict = self.make_dicts(query=query1, params=(image_id,) )[0]

        #format the dates to be JSON-compatible
        image_dict["timestamp"] = image_dict["timestamp"].isoformat()
        image_dict["date"] = image_dict["date"].isoformat()

        return(image_dict)

    def getImageIDByFullname(self, fullname):
        """
        Returns an image_id given a fullname.

        fullname - the image name including full path

        """

        if self.logger:
          self.logger.debug('Database::getImageIDByFullname %s' % fullname)
        else:
          print 'Database::getImageIDByFullname %s' % fullname

        try:
            query1 = 'SELECT image_id FROM images WHERE fullname=%s LIMIT 1'
            image_dict = self.make_dicts(query=query1, params=(fullname,))[0]
            return(image_dict['image_id'])

        except:
            return(0)


    ##################################################################################################################
    # Functions for sample identification                                                                            #
    ##################################################################################################################
    def setImageSampleId(self,image_dict,puckset_id):
        """
        Updates an image record with the sample_id, given a puckset_id.

        image_dict - a dict formed from a row of rapd_data.images
        puckset_id - an int used to index pucksets in rapd_data.puck_settings

        """

        self.logger.debug('Database::setImageSampleId image_id:%d  puckset_id:%s' %(image_dict['image_id'],str(puckset_id)))

        try:
            #connect to the mysql server
            connection,cursor = self.get_db_connection()

            #retrieve the sample id for the Puck:Sample in the image header
            query1 = '''SELECT samples.sample_id as sample_id from samples
                            JOIN (puck_settings,images)
                                ON (puck_settings.'''+image_dict['puck']+'''=samples.PuckID
                                    AND samples.sample=images.sample)
                            WHERE puck_settings.puckset_id=%s
                                AND  images.image_id=%s'''
            #print query1 % (puckset_id,image_dict['image_id'])
            cursor.execute(query1,(puckset_id,image_dict['image_id']))
            sample_id = cursor.fetchone()[0]

            #update the image record with the new sample_id
            query2 = 'UPDATE images set sample_id=%s WHERE image_id=%s'
            cursor.execute(query2,(sample_id,image_dict['image_id']))
            #return the image dict with the sample_id in it
            image_dict['sample_id'] = sample_id
            self.closeConnection(connection,cursor)
            return(image_dict)
        except:
            self.logger.exception('Error in setImageSampleId')
            self.closeConnection(connection,cursor)
            #return the original image_dict
            return(image_dict)

    def getSetPuckInfo(self,puckset_id):
        """
        Return the entries for the given puckset_id.

        puckset_id - a varchar used to identify pucks in rapd_data.samples and rapd_data.puck_settings

        """

        self.logger.debug('Database::getSetPuckInfo puckset_id:%s' %str(puckset_id))

        #query for puck_settings
        try:
            query1  = 'SELECT A,B,C,D FROM puck_settings WHERE puckset_id="%s"' % (str(puckset_id))
            request_dict = self.make_dicts(query1,(),'DATA')[0]
        except:
            request_dict = False

        #see if we have a request
        return(request_dict)

    def getPuckInfo(self,puckid):
        """
        Return the CrystalIDs for a given puckid in ascending order.

        puckid - a varchar used to identify pucks in rapd_data.samples and rapd_data.puck_settings

        """
        self.logger.debug('Database::getPuckInfo puckid:%s' %str(puckid))
        try:
            query1  = 'SELECT sample, CrystalID, PuckID FROM samples WHERE PuckID="%s" ORDER BY sample' % (str(puckid))
            request_dict = self.make_dicts(query1,(),'DATA')
            #force the dictionary to be sorted
            if len(request_dict) < 16:
                temp_dict = []
                for i in range(1,17):
                    temp_dict.append({'sample': i, 'CrystalID': 'NULL', 'PuckID': puckid})
                for entry in request_dict:
                    temp_dict[entry['sample']-1] = entry
                request_dict = temp_dict
            request_dict.sort(key=operator.itemgetter('sample'))

        except:
            request_dict = False

        #see if we have a request
        return(request_dict)

    def getAllPucks(self,puck_cutoff):
        """
        Return a list of all available pucks for CONSOLE.  Limited by a cutoff date.

        puck_cutoff - a variable describing the cutoff date in MYSQL format.
        """
        self.logger.debug('Database::getAllPucks after %s' % (puck_cutoff))

        #query for list of pucks
        try:
            query1  = 'SELECT PuckID FROM samples WHERE timestamp>"%s" GROUP BY PuckID' % (puck_cutoff)
            request_dict = self.make_dicts(query1,(),'DATA')
        except:
            request_dict = False
         #see if we have a request
        return(request_dict)

    def getCurrentPucks(self, site_id="C"):
        """
        Return a list of all currently selected pucks for a site.

        """
        self.logger.debug('Database::getCurrentPucks for %s' % (site_id))

        #query for list of pucks
        try:
            #connect to the mysql server
            connection,cursor = self.get_db_connection()
            query  = "SELECT puckset_id FROM current WHERE site=%s" % (site_id)
            cursor.execute(query, site_id)
            puckset_id = cursor.fetchone()[0]
            if puckset_id == 0:
                request_dict = False
            else:
                request_dict = self.getSetPuckInfo(puckset_id)
        except:
            request_dict = False

        self.closeConnection(connection,cursor)

        #see if we have a request
        return(request_dict)

    def resetPucks(self, site_id="C"):
        """
        Reset the puckset to none for a given site_id.
        """

        self.logger.debug("resetPucks")

        try:
            #connect to the mysql server
            connection,cursor = self.get_db_connection()
            query = "UPDATE current SET puckset_id=0 WHERE site=%s"
            cursor.execute(query, (site_id, ))
            self.closeConnection(connection, cursor)
        except:
            self.logger.exception("Error in resetPucks")




    ############################################################################
    # Functions for settings                                                   #
    ############################################################################
    def addSettings(self, settings, preset=False):
        """
        Updates the mysql database with settings in the passed-in dict and returns the setting_id
        """
        self.logger.debug('Database::addSettings')

        blank = {'site'                     : '0',
                 'data_root_dir'            : 'DEFAULTS',
                 'multiprocessing'          : 'True',
                 'spacegroup'               : 'None',
                 'sample_type'              : 'Protein',
                 'solvent_content'          : '0.55',
                 'susceptibility'           : '1.0',
                 'crystal_size_x'           : '100',
                 'crystal_size_y'           : '100',
                 'crystal_size_z'           : '100',
                 'a'                        : 'None',
                 'b'                        : 'None',
                 'c'                        : 'None',
                 'alpha'                    : 'None',
                 'beta'                     : 'None',
                 'gamma'                    : 'None',
                 'work_dir_override'        : 'False',
                 'work_directory'           : 'None',
                 'beam_flip'                : 'False',
                 'x_beam'                   : 'False',
                 'y_beam'                   : 'False',
                 'index_hi_res'             : 'AUTO',
                 'strategy_type'            : 'best',
                 'best_complexity'          : 'none',
                 'mosflm_seg'               : '0',
                 'mosflm_rot'               : '0.0',
                 'mosflm_start'             : '0.0',
                 'mosflm_end'               : '360.0',
                 'min_exposure_per'         : '1.0',
                 'aimed_res'                : '0.0',
                 'beam_size_x'              : 'AUTO',
                 'beam_size_y'              : 'AUTO',
                 'integrate'                : 'rapd',
                 'reference_data_id'        : '0',
                 'setting_type'             : 'GLOBAL'}

        #aggregate the passed-in settings with the 'blank'
        blank.update(settings)

        #connect to the mysql server
        connection,cursor = self.get_db_connection()

        try:
            cursor.execute("""INSERT INTO settings  ( site,
                                                      data_root_dir,
                                                      multiprocessing,
                                                      spacegroup,
                                                      sample_type,
                                                      solvent_content,
                                                      susceptibility,
                                                      crystal_size_x,
                                                      crystal_size_y,
                                                      crystal_size_z,
                                                      a,
                                                      b,
                                                      c,
                                                      alpha,
                                                      beta,
                                                      gamma,
                                                      work_dir_override,
                                                      work_directory,
                                                      beam_flip,
                                                      x_beam,
                                                      y_beam,
                                                      index_hi_res,
                                                      strategy_type,
                                                      best_complexity,
                                                      mosflm_seg,
                                                      mosflm_rot,
                                                      mosflm_start,
                                                      mosflm_end,
                                                      min_exposure_per,
                                                      aimed_res,
                                                      beam_size_x,
                                                      beam_size_y,
                                                      integrate,
                                                      reference_data_id,
                                                      setting_type)  VALUES   (%s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s,
                                                                               %s)""",  ( blank['site'],
                                                                                          blank['data_root_dir'],
                                                                                          blank['multiprocessing'],
                                                                                          blank['spacegroup'],
                                                                                          blank['sample_type'],
                                                                                          blank['solvent_content'],
                                                                                          blank['susceptibility'],
                                                                                          blank['crystal_size_x'],
                                                                                          blank['crystal_size_y'],
                                                                                          blank['crystal_size_z'],
                                                                                          blank['a'],
                                                                                          blank['b'],
                                                                                          blank['c'],
                                                                                          blank['alpha'],
                                                                                          blank['beta'],
                                                                                          blank['gamma'],
                                                                                          blank['work_dir_override'],
                                                                                          blank['work_directory'],
                                                                                          blank['beam_flip'],
                                                                                          blank['x_beam'],
                                                                                          blank['y_beam'],
                                                                                          blank['index_hi_res'],
                                                                                          blank['strategy_type'],
                                                                                          blank['best_complexity'],
                                                                                          blank['mosflm_seg'],
                                                                                          blank['mosflm_rot'],
                                                                                          blank['mosflm_start'],
                                                                                          blank['mosflm_end'],
                                                                                          blank['min_exposure_per'],
                                                                                          blank['aimed_res'],
                                                                                          blank['beam_size_x'],
                                                                                          blank['beam_size_y'],
                                                                                          blank['integrate'],
                                                                                          blank['reference_data_id'],
                                                                                          blank['setting_type']))

        except:
            self.logger.exception('ERROR : unknown exception in Database::setSettings')
            self.closeConnection(connection,cursor)
            return(False)

        try:
            #retrieve the dict
            settings_dict = self.getSettings(cursor.lastrowid)
            #now update the current table in the database
            self.update_current(settings_dict)
            #nowupdate the preset table, if necessary
            if preset:
                self.addPreset(settings_dict)
            self.closeConnection(connection,cursor)
            return(settings_dict)

        except:
            self.logger.exception('ERROR in updating settings from database')
            self.closeConnection(connection,cursor)
            return(False)


    def update_current(self,in_dict):
        """
        update the current table in the database (the current table keeps track of the most recent
        happenings in the RAPD universe)
        """
        self.logger.debug('Database::update_current')
        self.logger.debug(in_dict)

        #connect
        connection,cursor = self.get_db_connection()

        #make sure there is a row for this site
        cursor.execute("SELECT * FROM current WHERE site=%s",(in_dict['site']))
        #must add a row for this site
        if cursor.rowcount == 0:
            self.logger.debug('Inserting row for this site into current')
            cursor.execute("INSERT INTO current ( site ) VALUES (%s)",(in_dict['site']))
        #in the clear
        else:
            pass

        try:
            command = 'UPDATE current SET '
            value_array = []
            do_and = False

            #update setting_id
            if in_dict.has_key('setting_id'):
                self.logger.debug('Updating current table using setting_id %d' % in_dict['setting_id'])
                command += 'setting_id=%s'
                value_array.append(in_dict['setting_id'])
                #cursor.execute("UPDATE current SET setting_id=%s WHERE site=%s",(in_dict['setting_id'],in_dict['site']))
                do_and = True

            #update data_root_dir
            if in_dict.has_key('data_root_dir'):
                self.logger.debug('Updating current table using data_root_dir %s' % in_dict['data_root_dir'])
                #cursor.execute("UPDATE current SET data_root_dir=%s WHERE site=%s",(in_dict['data_root_dir'],in_dict['site']))
                if (do_and):
                    command += ','
                command += 'data_root_dir=%s'
                value_array.append(in_dict['data_root_dir'])
                do_and = True

            #update puckset_id
            if in_dict.has_key('puckset_id'):
                self.logger.debug('Updating current table using puckset_id %d' % in_dict['puckset_id'])
                if (do_and):
                    command += ','
                command += 'puckset_id=%s'
                value_array.append(in_dict['puckset_id'])
                do_and = True

            #finish up the command and execute
            command += ' WHERE site=%s'
            value_array.append(in_dict['site'])
            if (do_and):
                cursor.execute(command,value_array)

            self.closeConnection(connection,cursor)
        except:
            self.logger.exception('ERROR in updating current settings')
            self.closeConnection(connection,cursor)

    def addPreset(self, settings):
        """
        Change the entry for the given site in the presets table
        This allows for easy change of the presets table to reflect the python settings
        """
        self.logger.debug('Database::addPreset')

        #connect
        connection,cursor = self.get_db_connection()

        #make sure there is a row for this site
        cursor.execute("SELECT * FROM presets WHERE site=%s and data_root_dir='DEFAULTS'",(settings['site']))

        #must add a row for this site
        if cursor.rowcount == 0:
            self.logger.debug('rowcount 0')
            self.logger.debug('%s %s' % (str(settings['setting_id']), str(settings['site'])))
            self.logger.debug('Inserting row for this site into current')
            cursor.execute("INSERT INTO presets ( setting_id, site, data_root_dir ) VALUES (%s,%s,%s)",(settings['setting_id'],settings['site'],'DEFAULTS'))
        #in the clear
        else:
            cursor.execute("UPDATE presets SET setting_id=%s  WHERE site=%s and data_root_dir=%s", (settings['setting_id'], settings['site'], 'DEFAULTS'))

        self.closeConnection(connection,cursor)

    def putBeamcenter(self,beamcenter_data):
        """
        Add a new beamcenter equation to the database
        """
        self.logger.debug('Database::addBeamcenter')

        #make the code simpler to read
        d = beamcenter_data

        #connect
        connection,cursor = self.get_db_connection()

        #add to the table
        cursor.execute('''INSERT INTO site (site,x_b,x_m1,x_m2,x_m3,x_m4,x_m5,x_m6,x_r,y_b,y_m1,y_m2,y_m3,y_m4,y_m5,y_m6,y_r)
                          VALUES (d.site,d.x_b,d.x_m1,d.x_m2,d.x_m3,d.x_m4,d.x_m5,d.x_m6,d.x_r,d.y_b,d.y_m1,d.y_m2,d.y_m3,d.y_m4,d.y_m5,d.y_m6,d.y_r,json.dumps(d.image_ids))''')

        #clean up connection
        self.closeConnection(connection,cursor)

        #return the latest values
        return(self.getBeamcenter(d.site))

    def getBeamcenter(self, site, date=False):
        """
        Return the latest
        """
        self.logger.debug('Database.getBeamcenter site: %s' % site)

        my_dict = {}

        if (date):
            #not working for specific date yet
            pass
        else:
            my_dict = self.make_dicts('SELECT * FROM beamcenter WHERE site=%s ORDER BY timestamp DESC LIMIT 1', (site, ))

        return(my_dict)

    def getSettingsByBDT(self, site_id, data_root_dir="DEFAULTS",setting_type="GLOBAL"):
        """
        Returns a dict with the most recent settings for the given conditions.

        This attempts to find settings for a site_id+data root dir of a particular
        type, ususally global.
        """

        self.logger.warning('Database::getSettingsByBDT site_id:%s drd:%s type:%s' % (site_id, data_root_dir, setting_type))

        try:
            query1 = 'SELECT * FROM settings WHERE site=%s AND data_root_dir=%s AND setting_type=%s ORDER BY setting_id DESC LIMIT 1'
            settings_dict = self.make_dicts(query1, (site_id, data_root_dir, setting_type))[0]

            #handle the addition of reference_data_id
            if settings_dict['reference_data_id']:
                settings_dict['reference_data'] = self.getReferenceData(reference_data_id=settings_dict['reference_data_id'])

            #change the datetimes to JSON encodable
            settings_dict['timestamp'] = settings_dict['timestamp'].isoformat()

            return(settings_dict)

        except:
            self.logger.exception('Error in getSettingsByBDT')
            return(False)


    def getSettings(self,setting_id):
        """
        Returns a dict with all the settings for a given setting_id
        """
        self.logger.debug('Database::getSettings setting_id: %d' % setting_id)

        try:
            query1 = 'SELECT * FROM settings WHERE setting_id=%s'
            settings_dict = self.make_dicts(query1,(setting_id,))[0]

            #handle the addition of reference_data_id
            if settings_dict['reference_data_id']:
                settings_dict['reference_data'] = self.getReferenceData(reference_data_id=settings_dict['reference_data_id'])

            #change the datetimes to JSON encodable
            settings_dict['timestamp'] = settings_dict['timestamp'].isoformat()

            return(settings_dict)

        except:
            self.logger.exception('Error in getSettings')
            return(False)

    def getReferenceData(self,reference_data_id):
        """
        Return a dict with the information on data described in the reference_data entry for the given id
        """
        self.logger.debug('getReferenceData reference_data_id:%s' % reference_data_id)

        #get the information in the reference_data table
        query1 = ('SELECT * from reference_data WHERE reference_data_id=%s')
        reference_data_dict = self.make_dicts(query=query1,
                                             params=(reference_data_id,),
                                             db='DATA')[0]

        runs_dict = {}
        for key,value in reference_data_dict.iteritems():
            if key.startswith('result_id_') and value:
                query = '''SELECT integrate_results.repr as repr,integrate_results.spacegroup as spacegroup,integrate_results.work_dir as work_dir,
                                  runs.phi as phi_start,runs.phi+runs.width*runs.total as phi_end
                           FROM integrate_results LEFT JOIN runs ON integrate_results.run_id=runs.run_id WHERE integrate_results.result_id=%s;'''
                #query = '''SELECT runs.directory as directory,runs.image_prefix as prefix,runs.run_number as run_number,runs.start as start_image_number,runs.phi as phi_start,runs.phi+runs.width*runs.total as phi_end
                #           FROM integrate_results LEFT JOIN runs ON integrate_results.run_id=runs.run_id WHERE integrate_results.result_id=%s;'''
                temp_dict = self.make_dicts(query=query,
                                             params=(value,),
                                             db='DATA')[0]
                runs_dict[key] = temp_dict

        #print runs_dict
        out_array = []
        for tmp_dict in runs_dict.itervalues():
            mat_file = os.path.join(tmp_dict['work_dir'],'reference.mat')
            #fullname = os.path.join(tmp_dict['directory'],'_'.join((tmp_dict['prefix'],str(tmp_dict['run_number']),str(tmp_dict['start_image_number']).zfill(3)))+'.img')
            phi_start = tmp_dict['phi_start']
            phi_end = tmp_dict['phi_end']
            repr = tmp_dict['repr']
            spacegroup = tmp_dict['spacegroup'].replace(' ','')
            out_array.append([mat_file,phi_start,phi_end,repr,spacegroup])
        return(out_array)

    def get_current_settings(self, id):
        """
        Returns a dict with the current settings for a given site
        """
        self.logger.debug('Database::get_current_settings for id %s', id)

        try:

            # 1st get the imagesettings_id from current
            query1 = 'SELECT * FROM current WHERE site=%s'
            current_dict = self.make_dicts(query=query1,
                                          params=(id,),
                                          db='DATA')[0]

            my_id = current_dict['setting_id']

            #now get the settings dict from the db based on the
            settings_dict = self.getSettings(my_id)
            settings_dict['puckset_id'] = current_dict['puckset_id']

            return(settings_dict)

        except:
            self.logger.exception('Error in get_current_settings')
            return(False)

    def check_new_data_root_dir_setting(self, data_root_dir, site_id):
        """
        Check to see if there is an entry for this data_root_dir.

        An attempt is made to get the most recent global settings for the drd.
        If this fails, the most recent default entry in the database is acquired.
        """
        self.logger.debug('Database::check_new_data_root_dir_setting %s %s',
                          (data_root_dir, site_id))

        #check to see if there is an entry in presets for this drd
        settings_dict = self.getSettingsByBDT(site_id=site_id,
                                              data_root_dir=data_root_dir,
                                              setting_type='GLOBAL')
        if (settings_dict):
            # Make sure the site_id is correct
            self.update_current(settings_dict)
        else:

            # Get the defaults for this site_id
            query = "SELECT * FROM settings WHERE site=%s AND data_root_dir=%s ORDER BY setting_id DESC LIMIT 1"

            print query
            print site_id
            settings_dict = self.make_dicts(query, (site_id, "DEFAULTS"))[0]

            # Update the dict with current data
            my_dict = {"site":site_id, "data_root_dir":data_root_dir}
            settings_dict.update(my_dict)

            # Make a new entry for this drd
            settings_dict = self.addSettings(settings_dict)
            self.logger.debug(settings_dict)

        # Change the datetimes to JSON encodable
        try:
            settings_dict["timestamp"] = settings_dict["timestamp"].isoformat()
        except:
            pass

        return(settings_dict)

    ##################################################################################################################
    # Functions for processes                                                                                        #
    ##################################################################################################################
    def addNewProcess(self,type,rtype,data_root_dir,repr,display='show'):
        """
        Add an entry to the processes table which enables the GUI to display current processes

        type - sad,
        rtype - reprocess or original
        data_root_dir -
        repr - representation of the run to be shown in the UI
        display - show,hide  - controls whether a process will be displayed in the UI
        """

        self.logger.debug('Database::addNewProcess %s %s %s %s %s' % (type,rtype,data_root_dir,repr,display))

        try:
            #connect to the database
            connection,cursor = self.get_db_connection()

            #the query
            query         = 'INSERT INTO processes (type,rtype,data_root_dir,repr,display) VALUES (%s,%s,%s,%s,%s)'
            insert_values = [type,rtype,data_root_dir,repr,display]

            #deposit the result
            self.logger.debug(query)
            self.logger.debug(insert_values)
            cursor.execute(query,insert_values)

            #now get the process_id for the inserted process
            process_id = cursor.lastrowid
            self.closeConnection(connection,cursor)
            return(process_id)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addNewProcess')
            self.closeConnection(connection,cursor)
            return(False)

    def modifyProcessDisplay(self,process_id,display_value):
        """
        Modify display property of an entry in processes to value
        """
        self.logger.debug('Database::modifyProcessDisplay %d  %s' % (process_id,display_value))

        try:
            #get cursor
            connection,cursor = self.get_db_connection()

            #change the line
            cursor.execute("UPDATE processes SET display=%s, timestamp2=NOW() WHERE process_id=%s",(display_value,process_id))
            self.closeConnection(connection,cursor)
            return(True)

        except:
            self.logger.exception('ERROR : unknown exception in Database::modifyProcessDisplay')
            self.closeConnection(connection,cursor)
            return(False)

    ############################################################################
    # Functions for results                                                    #
    ##########################################################################$#
    def makeNewResult(self, rtype, process_id=0, data_root_dir=None):
        """
        Create a new (blank) entry for a given type of result

        rtype - sad,single,pair,integrate
        process_id - the index of the rapd_data.processes table for this result
        """

        self.logger.debug("Database::makeNewResult  rtype:%s" % rtype)

        try:
            #get cursor
            connection, cursor = self.get_db_connection()
            #create entry
            query = "INSERT INTO "+rtype+"_results (process_id,data_root_dir) VALUES (%s, %s)"
            cursor.execute(query, (process_id, data_root_dir))
            #get the rtype_result_id
            rtype_result_id = cursor.lastrowid
            #now add the rtype_result to the results table
            cursor.execute("INSERT INTO results (type,id,process_id,data_root_dir,display) VALUES (%s,%s,%s,%s,%s)",(rtype,rtype_result_id,process_id,data_root_dir,'none'))
            #get the result_id
            result_id = cursor.lastrowid
            self.closeConnection(connection, cursor)
            #return to the caller
            return(rtype_result_id, result_id)

        except:
            self.logger.exception('ERROR : unknown exception in Database::makeNewResult')
            self.closeConnection(connection, cursor)
            return(False, False)


    def addSingleResult(self,dirs,info,settings,results):
        """
        Add data to the single_results table
        """
        #Put out some info to the logger
        self.logger.debug('Database::addSingleResult')
        self.logger.debug(dirs['data_root_dir'])
        self.logger.debug(os.path.basename(info['fullname']))
        self.logger.debug(info['fullname'])
        # self.logger.debug(info['adsc_number'])

        #Get a nuanced version of the type of single result this is
        if (settings['reference_data_id'] > 0):
            my_type = 'ref_strat'
        elif settings.has_key('request'):
            my_type = settings['request']['request_type']
        else:
            my_type ='original'

        #set up some variables for the logic (so-called)
        norm_strat_type = None
        anom_strat_type = None

        try:
            #connect to the database
            connection,cursor = self.get_db_connection()

            #regardless of failure level
            command_front = """INSERT INTO single_results ( process_id,
                                                       data_root_dir,
                                                       settings_id,
                                                       repr,
                                                       fullname,
                                                       image_id,
                                                    #    adsc_number,
                                                       date,
                                                       sample_id,
                                                       work_dir,
                                                       type"""

            command_back = """) VALUES ( %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                # %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s"""

            insert_values = [ info['process_id'],
                              dirs['data_root_dir'],
                              settings['setting_id'],
                              info['repr'],
                              info['fullname'],
                              info['image_id'],
                            #   info['adsc_number'],
                              info['date'],
                              info['sample_id'],
                              dirs['work'],
                              my_type]

            #DISTL
            try:
                if results['Distl results'] == 'FAILED':
                    command_front += """,
                                           distl_status"""

                    command_back += """,
                                           %s"""

                    insert_values.append("FAILED")

                else:
                    if (results['Distl results']['max cell'][0] == 'None'):
                        results['Distl results']['max cell'][0] = 0
                    tmp_command_front = """,
                                                       distl_status,
                                                       distl_res,
                                                       distl_labelit_res,
                                                       distl_ice_rings,
                                                       distl_total_spots,
                                                       distl_spots_in_res,
                                                       distl_good_bragg_spots,
                                                       distl_overloads,
                                                       distl_max_cell,
                                                       distl_mean_int_signal,
                                                       distl_min_signal_strength,
                                                       distl_max_signal_strength"""

                    tmp_command_back = """,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s"""

                    tmp_insert_values = ['SUCCESS',
                                      results['Distl results']['distl res'][0],
                                      results['Distl results']['labelit res'][0],
                                      results['Distl results']['ice rings'][0],
                                      results['Distl results']['total spots'][0],
                                      results['Distl results']['spots in res'][0],
                                      results['Distl results']['good Bragg spots'][0],
                                      results['Distl results']['overloads'][0],
                                      results['Distl results']['max cell'][0],
                                      results['Distl results']['mean int signal'][0],
                                      results['Distl results']['min signal strength'][0],
                                      results['Distl results']['max signal strength'][0]]

                    #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                    command_front += tmp_command_front
                    command_back  += tmp_command_back
                    insert_values += tmp_insert_values
            except:
                command_front += """,
                                                       distl_status"""

                command_back += """,
                                                                %s"""

                insert_values.append("FAILED")

            #LABELIT
            try:
                if results['Labelit results'] == 'FAILED':
                    command_front += """,
                                                       labelit_status"""

                    command_back += """,
                                                                %s"""

                    insert_values.append("FAILED")

                else:
                    tmp_command_front = """,
                                                       labelit_status,
                                                       labelit_iteration,
                                                       labelit_res,
                                                       labelit_spots_fit,
                                                       labelit_metric,
                                                       labelit_spacegroup,
                                                       labelit_distance,
                                                       labelit_x_beam,
                                                       labelit_y_beam,
                                                       labelit_a,
                                                       labelit_b,
                                                       labelit_c,
                                                       labelit_alpha,
                                                       labelit_beta,
                                                       labelit_gamma,
                                                       labelit_mosaicity,
                                                       labelit_rmsd"""

                    tmp_command_back = """,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s"""

                    tmp_insert_values = ['SUCCESS',
                                      results['Labelit results']['labelit_iteration'],
                                      results['Labelit results']['mosflm_res'][0],
                                      results['Labelit results']['labelit_spots_fit'][0],
                                      results['Labelit results']['labelit_metric'][0],
                                      results['Labelit results']['mosflm_sg'][0],
                                      results['Labelit results']['mosflm_distance'][0],
                                      results['Labelit results']['mosflm_beam_x'][0],
                                      results['Labelit results']['mosflm_beam_y'][0],
                                      results['Labelit results']['labelit_cell'][0][0],
                                      results['Labelit results']['labelit_cell'][0][1],
                                      results['Labelit results']['labelit_cell'][0][2],
                                      results['Labelit results']['labelit_cell'][0][3],
                                      results['Labelit results']['labelit_cell'][0][4],
                                      results['Labelit results']['labelit_cell'][0][5],
                                      results['Labelit results']['mosflm_mos'][0],
                                      results['Labelit results']['labelit_rmsd'][0]]

                    #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                    command_front += tmp_command_front
                    command_back  += tmp_command_back
                    insert_values += tmp_insert_values

            except:
                command_front += """,
                                                       labelit_status"""

                command_back += """,
                                                                %s"""

                insert_values.append("FAILED")


            #RADDOSE
            try:
                if results['Raddose results'] == 'FAILED':
                    command_front += """,
                                                       raddose_status"""

                    command_back += """,
                                                                %s"""

                    insert_values.append("FAILED")

                else:
                    tmp_command_front = """,
                                                       raddose_status,
                                                       raddose_dose_per_image,
                                                       raddose_henderson_limit,
                                                       raddose_exp_dose_limit"""

                    tmp_command_back = """,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s"""

                    tmp_insert_values = ['SUCCESS',
                                      results['Raddose results']['dose per image'],
                                      results['Raddose results']['henderson limit'],
                                      results['Raddose results']['exp dose limit']]

                    #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                    command_front += tmp_command_front
                    command_back  += tmp_command_back
                    insert_values += tmp_insert_values

            except:
                command_front += """,
                                                       raddose_status"""

                command_back += """,
                                                                %s"""

                insert_values.append("FAILED")


            #The normal strategy results
            enter_norm_mosflm = False
            try:
                if results.has_key('Best results'):
                #if results['Best results']:
                    self.logger.debug('Best results is there')
                    if results['Best results'] == 'FAILED':
                        tmp_command_front = """,
                                                           best_norm_status"""

                        tmp_command_back = """,
                                                                    %s"""

                        tmp_insert_values = ["FAILED"]

                        #MOSFLM STRATEGY
                        if results['Mosflm strategy results'] == 'FAILED':
                            tmp_command_front += """,
                                                           mosflm_norm_status"""

                            tmp_command_back += """,
                                                                    %s"""

                            tmp_insert_values.append("FAILED")
                        else:
                            enter_norm_mosflm = True

                    else:
                        norm_strat_type = 'best'
                        tmp_command_front = """,
                                                       best_complexity,
                                                       best_norm_status,
                                                       best_norm_res_limit,
                                                       best_norm_completeness,
                                                       best_norm_atten,
                                                       best_norm_rot_range,
                                                       best_norm_phi_end,
                                                       best_norm_total_exp,
                                                       best_norm_redundancy,
                                                       best_norm_i_sigi_all,
                                                       best_norm_i_sigi_high,
                                                       best_norm_r_all,
                                                       best_norm_r_high,
                                                       best_norm_unique_in_blind,
                                                       mosflm_norm_status"""

                        tmp_command_back = """,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s"""

                        tmp_insert_values = [settings['best_complexity'],
                                          'SUCCESS',
                                          results['Best results']['strategy res limit'],
                                          results['Best results']['strategy completeness'][:-1],
                                          results['Best results']['strategy attenuation'],
                                          results['Best results']['strategy rot range'],
                                          results['Best results']['strategy phi end'],
                                          results['Best results']['strategy total exposure time'],
                                          results['Best results']['strategy redundancy'],
                                          results['Best results']['strategy I/sig'].split(' ')[0],
                                          results['Best results']['strategy I/sig'].split(' ')[1][1:-1],
                                          results['Best results']['strategy R-factor'].split(' ')[0][:-1],
                                          results['Best results']['strategy R-factor'].split(' ')[1][1:-2],
                                          results['Best results']['strategy frac of unique in blind region'][:-1],
                                          'NONE' ]

                #There is no entry in the results for 'Best results'
                else:
                    self.logger.debug('NO key Best results')
                    #BEST STRATEGY
                    tmp_command_front = """,
                                                           best_norm_status"""
                    tmp_command_back = """,
                                                                    %s"""
                    tmp_insert_values = ["NONE"]

                    #MOSFLM STRATEGY
                    if results.has_key('Mosflm strategy results'):
                        if results['Mosflm strategy results'] == 'FAILED':
                            tmp_command_front += """,
                                                               mosflm_norm_status"""
                            tmp_command_back += """,
                                                                        %s"""
                            tmp_insert_values.append("FAILED")
                        else:
                            enter_norm_mosflm = True
                    else:
                        tmp_command_front += """,
                                                               mosflm_norm_status"""
                        tmp_command_back += """,
                                                                        %s"""
                        tmp_insert_values.append("NONE")

                #If it is necessary, enterthe mosflm strategy results into the database
                if enter_norm_mosflm:
                    norm_strat_type = 'mosflm'
                    tmp_command_front += """,
                                                           mosflm_norm_status,
                                                           mosflm_norm_res_limit,
                                                           mosflm_norm_completeness,
                                                           mosflm_norm_redundancy,
                                                           mosflm_norm_distance,
                                                           mosflm_norm_delta_phi,
                                                           mosflm_norm_img_exposure_time
                                                           """

                    tmp_command_back += """,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s"""

                    tmp_insert_values += [ 'SUCCESS',
                                         results['Mosflm strategy results']['strategy resolution'],
                                         results['Mosflm strategy results']['strategy completeness'][:-1],
                                         results['Mosflm strategy results']['strategy redundancy'],
                                         results['Mosflm strategy results']['strategy distance'],
                                         results['Mosflm strategy results']['strategy delta phi'],
                                         results['Mosflm strategy results']['strategy image exp time'] ]

                #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                command_front += tmp_command_front
                command_back  += tmp_command_back
                insert_values += tmp_insert_values

            except:
                self.logger.exception('Exception in addSingleResult in the normal strategy results section')
                command_front += """,
                                                       best_norm_status,
                                                       mosflm_norm_status"""

                command_back += """,
                                                                %s,
                                                                %s"""

                insert_values += ['FAILED',
                                  'FAILED']

            #The anomalous strategy results
            enter_anom_mosflm = False
            try:
                if results.has_key('Best ANOM results'):
                    self.logger.debug('Best ANOM results present')
                    if results['Best ANOM results'] == 'FAILED':
                        tmp_command_front = """,
                                                           best_anom_status"""

                        tmp_command_back = """,
                                                                    %s"""

                        tmp_insert_values = ["FAILED"]

                        #MOSFLM STRATEGY
                        if results['Mosflm strategy results'] == 'FAILED':
                            command_front += """,
                                                           mosflm_anom_status"""

                            command_back += """,
                                                                    %s"""

                            insert_values.append("FAILED")
                        else:
                            enter_anom_mosflm = True

                    else:
                        anom_strat_type = 'best'
                        tmp_command_front = """,
                                                       best_anom_status,
                                                       best_anom_res_limit,
                                                       best_anom_completeness,
                                                       best_anom_atten,
                                                       best_anom_rot_range,
                                                       best_anom_phi_end,
                                                       best_anom_total_exp,
                                                       best_anom_redundancy,
                                                       best_anom_i_sigi_all,
                                                       best_anom_i_sigi_high,
                                                       best_anom_r_all,
                                                       best_anom_r_high,
                                                       best_anom_unique_in_blind,
                                                       mosflm_anom_status"""

                        tmp_command_back = """,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s"""

                        tmp_insert_values = ['SUCCESS',
                                          results['Best ANOM results']['strategy anom res limit'],
                                          results['Best ANOM results']['strategy anom completeness'][:-1],
                                          results['Best ANOM results']['strategy anom attenuation'],
                                          results['Best ANOM results']['strategy anom rot range'],
                                          results['Best ANOM results']['strategy anom phi end'],
                                          results['Best ANOM results']['strategy anom total exposure time'],
                                          results['Best ANOM results']['strategy anom redundancy'],
                                          results['Best ANOM results']['strategy anom I/sig'].split(' ')[0],
                                          results['Best ANOM results']['strategy anom I/sig'].split(' ')[1][1:-1],
                                          results['Best ANOM results']['strategy anom R-factor'].split(' ')[0][:-1],
                                          results['Best ANOM results']['strategy anom R-factor'].split(' ')[1][1:-2],
                                          results['Best ANOM results']['strategy anom frac of unique in blind region'][:-1],
                                          'NONE' ]

                #There is no entry in the results for 'Best results'
                else:
                    self.logger.debug('NO key Best ANOM results')
                    #BEST STRATEGY
                    tmp_command_front = """,
                                                           best_anom_status"""
                    tmp_command_back = """,
                                                                    %s"""
                    tmp_insert_values = ["NONE"]

                    #MOSFLM STRATEGY
                    if ((results.has_key('Mosflm ANOM strategy results')) and (results['Mosflm ANOM strategy results']['strategy anom run number'] != 'skip')):
                        self.logger.debug('Has key Mosflm ANOM results')
                        if results['Mosflm ANOM strategy results'] == 'FAILED':
                            tmp_command_front += """,
                                                               mosflm_anom_status"""
                            tmp_command_back += """,
                                                                        %s"""
                            tmp_insert_values.append("FAILED")
                        else:
                            enter_anom_mosflm = True
                    else:
                        self.logger.debug('NO key Mosflm ANOM results')
                        tmp_command_front += """,
                                                               mosflm_anom_status"""
                        tmp_command_back += """,
                                                                        %s"""
                        tmp_insert_values.append("NONE")

                #If it is necessary, enterthe mosflm strategy results into the database
                if enter_anom_mosflm:
                    anom_strat_type = 'mosflm'
                    tmp_command_front = """,
                                                           mosflm_anom_status,
                                                           mosflm_anom_res_limit,
                                                           mosflm_anom_completeness,
                                                           mosflm_anom_redundancy,
                                                           mosflm_anom_distance,
                                                           mosflm_anom_delta_phi,
                                                           mosflm_anom_img_exposure_time
                                                           """

                    tmp_command_back = """,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s"""

                    tmp_insert_values = [ 'SUCCESS',
                                         results['Mosflm ANOM strategy results']['strategy anom resolution'],
                                         results['Mosflm ANOM strategy results']['strategy anom completeness'][:-1],
                                         results['Mosflm ANOM strategy results']['strategy anom redundancy'],
                                         results['Mosflm ANOM strategy results']['strategy anom distance'],
                                         results['Mosflm ANOM strategy results']['strategy anom delta phi'],
                                         results['Mosflm ANOM strategy results']['strategy anom image exp time'] ]

                #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                command_front += tmp_command_front
                command_back  += tmp_command_back
                insert_values += tmp_insert_values

            except:
                self.logger.exception('Exception in addSingleResult in the anomalous strategy results section')
                command_front += """,
                                                       best_anom_status,
                                                       mosflm_anom_status"""

                command_back += """,
                                                                %s,
                                                                %s"""

                insert_values += ['FAILED',
                                  'FAILED']

            #NOW the html, image and stac files
            try:
                #Add stac summary only if there is a stac run
                if (info.has_key('mk3_phi')):
                    summary_stac = results['Output files']['Stac summary html']
                else:
                    summary_stac = 'None'

                if results['Output files'] == 'FAILED':
                        command_back += ")"


                else:
                    tmp_command_front = """,
                                                       summary_short,
                                                       summary_long,
                                                       summary_stac,
                                                       image_raw,
                                                       image_preds,
                                                       best_plots,
                                                       stac_file1,
                                                       stac_file2"""

                    tmp_command_back = """,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s,
                                                                %s)"""

                    tmp_insert_values = [ results['Output files']['Short summary html'],
                                          results['Output files']['Long summary html'],
                                          summary_stac,
                                          results['Output files']['image_path_raw_1'],
                                          results['Output files']['image_path_pred_1'],
                                          results['Output files']['Best plots html'],
                                          results['Output files']['STAC file1'],
                                          results['Output files']['STAC file2'] ]

                    #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                    command_front += tmp_command_front
                    command_back  += tmp_command_back
                    insert_values += tmp_insert_values

            except:
                command_back += ")"


            #deposit the result
            self.logger.debug(command_front+command_back)
            self.logger.debug(insert_values)
            cursor.execute(command_front+command_back,insert_values)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addSingleResult')
            return(False)


        try:
            #get the result's pair_result_dict
            single_result_dict = self.make_dicts('SELECT * FROM single_results WHERE single_result_id=%s',(cursor.lastrowid,))[0]

            #register the result in results table
            cursor.execute('INSERT INTO results (type,id,setting_id,process_id,sample_id,data_root_dir) VALUES (%s, %s, %s, %s, %s, %s)',
                                 ('single',
                                  single_result_dict['single_result_id'],
                                  single_result_dict['settings_id'],
                                  single_result_dict['process_id'],
                                  single_result_dict['sample_id'],
                                  single_result_dict['data_root_dir']))

            #add the result_id to the current dict
            single_result_dict['result_id'] = cursor.lastrowid

            #update the single_results table with the result_id
            cursor.execute("UPDATE single_results SET result_id=%s WHERE single_result_id=%s",(single_result_dict['result_id'],single_result_dict['single_result_id']))

            #log the "normal" strategy wedges
            if (norm_strat_type == 'best') :
                self.addStrategyWedges(id = single_result_dict['single_result_id'],
                                       int_type = 'single',
                                       strategy_type = 'normal',
                                       strategy_program = 'best',
                                       results = results['Best results'])
            elif (norm_strat_type == 'mosflm') :
                self.addStrategyWedges(id=single_result_dict['single_result_id'],
                                       int_type='single',
                                       strategy_type='normal',
                                       strategy_program='mosflm',
                                       results=results['Mosflm strategy results'])
            #log the anomalous strategy wedges
            if (anom_strat_type == 'best'):
                self.addStrategyWedges(id=single_result_dict['single_result_id'],
                                       int_type='single',
                                       strategy_type='anomalous',
                                       strategy_program='best',
                                       results=results['Best ANOM results'])
            elif (anom_strat_type == 'mosflm') :
                self.addStrategyWedges(id = single_result_dict['single_result_id'],
                                       int_type = 'single',
                                       strategy_type = 'anomalous',
                                       strategy_program = 'mosflm',
                                       results = results['Mosflm ANOM strategy results'])
            self.closeConnection(connection,cursor)
            return(single_result_dict)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addSingleResult - results updating subsection')
            self.closeConnection(connection,cursor)
            return(False)

    def addStrategyWedges(self,id,int_type,strategy_type,strategy_program,results):
        """
        Add a strategy wedge entry to the database
        """
        self.logger.debug('Database::addStrategyWedges')
        self.logger.debug(id)
        self.logger.debug(int_type)
        self.logger.debug(strategy_type)
        self.logger.debug(strategy_program)
        self.logger.debug(results)

        if (results == None):
            return False

        #accomodate normal and anomalous entries
        if strategy_type == 'anomalous':
            tag = 'strategy anom '
        else:
            tag = 'strategy '

        #there can be multiple runs depending on various factors
        for i in range(len(results[tag+'run number'])):
            try:
                #connect to the database
                connection,cursor = self.get_db_connection()

                if (strategy_program == 'best'):

                    cmd = '''INSERT INTO strategy_wedges ( id,
                                                           int_type,
                                                           strategy_type,
                                                           run_number,
                                                           phi_start,
                                                           number_images,
                                                           delta_phi,
                                                           overlap,
                                                           distance,
                                                           exposure_time ) VALUES ( %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s)'''
                    insert_values = ( id,
                                      int_type,
                                      strategy_type,
                                      results[tag+'run number'][i],
                                      results[tag+'phi start'][i],
                                      results[tag+'num of images'][i],
                                      results[tag+'delta phi'][i],
                                      results[tag+'overlap'][i],
                                      results[tag+'distance'][i],
                                      results[tag+'image exp time'][i] )

                elif (strategy_program == 'mosflm'):

                    cmd = '''INSERT INTO strategy_wedges ( id,
                                                        int_type,
                                                        strategy_type,
                                                        run_number,
                                                        phi_start,
                                                        number_images,
                                                        delta_phi,
                                                        overlap,
                                                        distance,
                                                        exposure_time ) VALUES ( %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s)'''
                    insert_values = ( id,
                                      int_type,
                                      strategy_type,
                                      results[tag+'run number'][i],
                                      results[tag+'phi start'][i],
                                      results[tag+'num of images'][i],
                                      results[tag+'delta phi'],
                                      'NULL',
                                      results[tag+'distance'],
                                      results[tag+'image exp time'] )

                #output for log
                self.logger.debug(cmd)
                self.logger.debug(insert_values)

                #put in the database
                cursor.execute(cmd,insert_values)

            except:
                self.logger.exception('ERROR : unknown exception in Database::addStrategyWedges')
                self.closeConnection(connection,cursor)
                return(False)

        #close connection and return
        self.closeConnection(connection,cursor)
        return(True)

    def getStrategyWedges(self,id):
        """
        Retrieve strategy wedges, given an id (either single_result_id or pair_result_id)
        """
        self.logger.debug('Database::getStrategyWedges %s' % str(id))

        #find all solutions for this result
        query = "SELECT * FROM strategy_wedges WHERE id=%s"
        request_dict = self.make_dicts(query=query,
                                      params=(id,))

        return(request_dict)

    def addPairResult(self,dirs,info1,info2,settings,results):
        """
        Add data to the pair_results table
        """
        self.logger.debug('Database::addPairResult')
        self.logger.debug(dirs['data_root_dir'])
        self.logger.debug(info1['fullname'])
        # self.logger.debug(info1['adsc_number'])
        self.logger.debug(info2['fullname'])
        # self.logger.debug(info2['adsc_number'])

        #set the request type
        if (settings['reference_data_id'] > 0):
             my_type = 'ref_strat'
        elif settings.has_key('request'):
            my_type = settings['request']['request_type']
        else:
            my_type ='original'

        norm_strat_type = None
        anom_strat_type = None

        try:
            #connect to the database
            connection,cursor = self.get_db_connection()

            #regardless of failure level
            command_front = """INSERT INTO pair_results ( process_id,
                                                       data_root_dir,
                                                       settings_id,
                                                       repr,
                                                       fullname_1,
                                                       image1_id,
                                                    #    adsc_number_1,
                                                       date_1,
                                                       fullname_2,
                                                       image2_id,
                                                    #    adsc_number_2,
                                                       date_2,
                                                       sample_id,
                                                       work_dir,
                                                       type"""

            command_back = """) VALUES ( %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            # %s,
                                                                            # %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s"""

            insert_values = [info1['process_id'],
                             dirs['data_root_dir'],
                             settings['setting_id'],
                             info1['repr'],
                             info1['fullname'],
                             info1['image_id'],
                            #  info1['adsc_number'],
                             info1['date'],
                             info2['fullname'],
                             info2['image_id'],
                            #  info2['adsc_number'],
                             info2['date'],
                             info1['sample_id'],
                             dirs['work'],
                             my_type]

            #DISTL
            try:
                if results['Distl results'] == 'FAILED':
                    command_front += """,
                                                       distl_status"""

                    command_back += """,
                                                                            %s"""

                    insert_values.append("FAILED")

                else:
                    if (results['Distl results']['max cell'][0] == 'None'):
                        results['Distl results']['max cell'][0] = 0
                    if (results['Distl results']['max cell'][1] == 'None'):
                        results['Distl results']['max cell'][1] = 0

                    tmp_command_front = """,
                                                       distl_status,
                                                       distl_res_1,
                                                       distl_labelit_res_1,
                                                       distl_ice_rings_1,
                                                       distl_total_spots_1,
                                                       distl_spots_in_res_1,
                                                       distl_good_bragg_spots_1,
                                                       distl_overloads_1,
                                                       distl_max_cell_1,
                                                       distl_mean_int_signal_1,
                                                       distl_min_signal_strength_1,
                                                       distl_max_signal_strength_1,
                                                       distl_res_2,
                                                       distl_labelit_res_2,
                                                       distl_ice_rings_2,
                                                       distl_total_spots_2,
                                                       distl_spots_in_res_2,
                                                       distl_good_bragg_spots_2,
                                                       distl_overloads_2,
                                                       distl_max_cell_2,
                                                       distl_mean_int_signal_2,
                                                       distl_min_signal_strength_2,
                                                       distl_max_signal_strength_2"""

                    tmp_command_back = """,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s"""

                    tmp_insert_values = ['SUCCESS',
                                      results['Distl results']['distl res'][0],
                                      results['Distl results']['labelit res'][0],
                                      results['Distl results']['ice rings'][0],
                                      results['Distl results']['total spots'][0],
                                      results['Distl results']['spots in res'][0],
                                      results['Distl results']['good Bragg spots'][0],
                                      results['Distl results']['overloads'][0],
                                      results['Distl results']['max cell'][0],
                                      results['Distl results']['mean int signal'][0],
                                      results['Distl results']['min signal strength'][0],
                                      results['Distl results']['max signal strength'][0],
                                      results['Distl results']['distl res'][1],
                                      results['Distl results']['labelit res'][1],
                                      results['Distl results']['ice rings'][1],
                                      results['Distl results']['total spots'][1],
                                      results['Distl results']['spots in res'][1],
                                      results['Distl results']['good Bragg spots'][1],
                                      results['Distl results']['overloads'][1],
                                      results['Distl results']['max cell'][1],
                                      results['Distl results']['mean int signal'][1],
                                      results['Distl results']['min signal strength'][1],
                                      results['Distl results']['max signal strength'][1]]

                    #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                    command_front += tmp_command_front
                    command_back  += tmp_command_back
                    insert_values += tmp_insert_values

            except:
                command_front += """,
                                                       distl_status"""

                command_back += """,
                                                                            %s"""

                insert_values.append("FAILED")

            #LABELIT
            try:
                if results['Labelit results'] == 'FAILED':
                    command_front += """,
                                                       labelit_status"""

                    command_back += """,
                                                                            %s"""

                    insert_values.append("FAILED")

                else:
                    tmp_command_front = """,
                                                       labelit_status,
                                                       labelit_iteration,
                                                       labelit_res,
                                                       labelit_spots_fit,
                                                       labelit_metric,
                                                       labelit_spacegroup,
                                                       labelit_distance,
                                                       labelit_x_beam,
                                                       labelit_y_beam,
                                                       labelit_a,
                                                       labelit_b,
                                                       labelit_c,
                                                       labelit_alpha,
                                                       labelit_beta,
                                                       labelit_gamma,
                                                       labelit_mosaicity,
                                                       labelit_rmsd"""

                    tmp_command_back = """,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s"""

                    tmp_insert_values = ['SUCCESS',
                                      results['Labelit results']['labelit_iteration'],
                                      results['Labelit results']['mosflm_res'][0],
                                      results['Labelit results']['labelit_spots_fit'][0],
                                      results['Labelit results']['labelit_metric'][0],
                                      results['Labelit results']['mosflm_sg'][0],
                                      results['Labelit results']['mosflm_distance'][0],
                                      results['Labelit results']['mosflm_beam_x'][0],
                                      results['Labelit results']['mosflm_beam_y'][0],
                                      results['Labelit results']['labelit_cell'][0][0],
                                      results['Labelit results']['labelit_cell'][0][1],
                                      results['Labelit results']['labelit_cell'][0][2],
                                      results['Labelit results']['labelit_cell'][0][3],
                                      results['Labelit results']['labelit_cell'][0][4],
                                      results['Labelit results']['labelit_cell'][0][5],
                                      results['Labelit results']['mosflm_mos'][0],
                                      results['Labelit results']['labelit_rmsd'][0]]

                    #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                    command_front += tmp_command_front
                    command_back  += tmp_command_back
                    insert_values += tmp_insert_values

            except:
                command_front += """,
                                                       labelit_status"""

                command_back += """,
                                                                            %s"""

                insert_values.append("FAILED")


            #RADDOSE
            try:
                if results['Raddose results'] == 'FAILED':
                    command_front += """,
                                                       raddose_status"""

                    command_back += """,
                                                                            %s"""

                    insert_values.append("FAILED")

                else:
                    tmp_command_front = """,
                                                       raddose_status,
                                                       raddose_dose_per_image,
                                                       raddose_henderson_limit,
                                                       raddose_exp_dose_limit"""

                    tmp_command_back = """,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s"""

                    tmp_insert_values = ['SUCCESS',
                                      results['Raddose results']['dose per image'],
                                      results['Raddose results']['henderson limit'],
                                      results['Raddose results']['exp dose limit']]

                    #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                    command_front += tmp_command_front
                    command_back  += tmp_command_back
                    insert_values += tmp_insert_values

            except:
                command_front += """,
                                                       raddose_status"""

                command_back += """,
                                                                            %s"""

                insert_values.append("FAILED")

            #The normal strategy results
            enter_norm_mosflm = False
            try:
                if results.has_key('Best results'):
                #if results['Best results']:
                    self.logger.debug('Best results is there')
                    if results['Best results'] == 'FAILED':
                        tmp_command_front = """,
                                                           best_norm_status"""

                        tmp_command_back = """,
                                                                    %s"""

                        tmp_insert_values = ["FAILED"]

                        #MOSFLM STRATEGY
                        if results['Mosflm strategy results'] == 'FAILED':
                            tmp_command_front += """,
                                                           mosflm_norm_status"""

                            tmp_command_back += """,
                                                                    %s"""

                            tmp_insert_values.append("FAILED")
                        else:
                            enter_norm_mosflm = True

                    else:
                        norm_strat_type = 'best'
                        tmp_command_front = """,
                                                       best_complexity,
                                                       best_norm_status,
                                                       best_norm_res_limit,
                                                       best_norm_completeness,
                                                       best_norm_atten,
                                                       best_norm_rot_range,
                                                       best_norm_phi_end,
                                                       best_norm_total_exp,
                                                       best_norm_redundancy,
                                                       best_norm_i_sigi_all,
                                                       best_norm_i_sigi_high,
                                                       best_norm_r_all,
                                                       best_norm_r_high,
                                                       best_norm_unique_in_blind,
                                                       mosflm_norm_status"""

                        tmp_command_back = """,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s"""

                        tmp_insert_values = [settings['best_complexity'],
                                          'SUCCESS',
                                          results['Best results']['strategy res limit'],
                                          results['Best results']['strategy completeness'][:-1],
                                          results['Best results']['strategy attenuation'],
                                          results['Best results']['strategy rot range'],
                                          results['Best results']['strategy phi end'],
                                          results['Best results']['strategy total exposure time'],
                                          results['Best results']['strategy redundancy'],
                                          results['Best results']['strategy I/sig'].split(' ')[0],
                                          results['Best results']['strategy I/sig'].split(' ')[1][1:-1],
                                          results['Best results']['strategy R-factor'].split(' ')[0][:-1],
                                          results['Best results']['strategy R-factor'].split(' ')[1][1:-2],
                                          results['Best results']['strategy frac of unique in blind region'][:-1],
                                          'NONE' ]

                #There is no entry in the results for 'Best results'
                else:
                    self.logger.debug('NO key Best results')
                    #BEST STRATEGY
                    tmp_command_front = """,
                                                           best_norm_status"""
                    tmp_command_back = """,
                                                                    %s"""
                    tmp_insert_values = ["NONE"]

                    #MOSFLM STRATEGY
                    if results.has_key('Mosflm strategy results'):
                        if results['Mosflm strategy results'] == 'FAILED':
                            tmp_command_front += """,
                                                               mosflm_norm_status"""
                            tmp_command_back += """,
                                                                        %s"""
                            tmp_insert_values.append("FAILED")
                        else:
                            enter_norm_mosflm = True
                    else:
                        tmp_command_front += """,
                                                               mosflm_norm_status"""
                        tmp_command_back += """,
                                                                        %s"""
                        tmp_insert_values.append("NONE")

                #If it is necessary, enterthe mosflm strategy results into the database
                if enter_norm_mosflm:
                    norm_strat_type = 'mosflm'
                    tmp_command_front += """,
                                                           mosflm_norm_status,
                                                           mosflm_norm_res_limit,
                                                           mosflm_norm_completeness,
                                                           mosflm_norm_redundancy,
                                                           mosflm_norm_distance,
                                                           mosflm_norm_delta_phi,
                                                           mosflm_norm_img_exposure_time
                                                           """

                    tmp_command_back += """,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s"""

                    tmp_insert_values += [ 'SUCCESS',
                                         results['Mosflm strategy results']['strategy resolution'],
                                         results['Mosflm strategy results']['strategy completeness'][:-1],
                                         results['Mosflm strategy results']['strategy redundancy'],
                                         results['Mosflm strategy results']['strategy distance'],
                                         results['Mosflm strategy results']['strategy delta phi'],
                                         results['Mosflm strategy results']['strategy image exp time'] ]

                #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                command_front += tmp_command_front
                command_back  += tmp_command_back
                insert_values += tmp_insert_values

            except:
                self.logger.exception('Exception in addPairResult in the normal strategy results section')
                command_front += """,
                                                       best_norm_status,
                                                       mosflm_norm_status"""

                command_back += """,
                                                                %s,
                                                                %s"""

                insert_values += ['FAILED',
                                  'FAILED']

            #The anomalous strategy results
            enter_anom_mosflm = False
            try:
                if results.has_key('Best ANOM results'):
                    self.logger.debug('Best ANOM results present')
                    if results['Best ANOM results'] == 'FAILED':
                        tmp_command_front = """,
                                                           best_anom_status"""

                        tmp_command_back = """,
                                                                    %s"""

                        tmp_insert_values = ["FAILED"]

                        #MOSFLM STRATEGY
                        if results['Mosflm strategy results'] == 'FAILED':
                            command_front += """,
                                                           mosflm_anom_status"""

                            command_back += """,
                                                                    %s"""

                            insert_values.append("FAILED")
                        else:
                            enter_anom_mosflm = True

                    else:
                        anom_strat_type = 'best'
                        tmp_command_front = """,
                                                       best_anom_status,
                                                       best_anom_res_limit,
                                                       best_anom_completeness,
                                                       best_anom_atten,
                                                       best_anom_rot_range,
                                                       best_anom_phi_end,
                                                       best_anom_total_exp,
                                                       best_anom_redundancy,
                                                       best_anom_i_sigi_all,
                                                       best_anom_i_sigi_high,
                                                       best_anom_r_all,
                                                       best_anom_r_high,
                                                       best_anom_unique_in_blind,
                                                       mosflm_anom_status"""

                        tmp_command_back = """,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s"""

                        tmp_insert_values = ['SUCCESS',
                                          results['Best ANOM results']['strategy anom res limit'],
                                          results['Best ANOM results']['strategy anom completeness'][:-1],
                                          results['Best ANOM results']['strategy anom attenuation'],
                                          results['Best ANOM results']['strategy anom rot range'],
                                          results['Best ANOM results']['strategy anom phi end'],
                                          results['Best ANOM results']['strategy anom total exposure time'],
                                          results['Best ANOM results']['strategy anom redundancy'],
                                          results['Best ANOM results']['strategy anom I/sig'].split(' ')[0],
                                          results['Best ANOM results']['strategy anom I/sig'].split(' ')[1][1:-1],
                                          results['Best ANOM results']['strategy anom R-factor'].split(' ')[0][:-1],
                                          results['Best ANOM results']['strategy anom R-factor'].split(' ')[1][1:-2],
                                          results['Best ANOM results']['strategy anom frac of unique in blind region'][:-1],
                                          'NONE' ]

                #There is no entry in the results for 'Best results'
                else:
                    self.logger.debug('NO key Best ANOM results')
                    #BEST STRATEGY
                    tmp_command_front = """,
                                                           best_anom_status"""
                    tmp_command_back = """,
                                                                    %s"""
                    tmp_insert_values = ["NONE"]

                    #MOSFLM STRATEGY
                    if results.has_key('Mosflm ANOM strategy results'):
                        self.logger.debug('Has key Mosflm ANOM results')
                        if results['Mosflm ANOM strategy results'] == 'FAILED':
                            tmp_command_front += """,
                                                               mosflm_anom_status"""
                            tmp_command_back += """,
                                                                        %s"""
                            tmp_insert_values.append("FAILED")
                        else:
                            enter_anom_mosflm = True
                    else:
                        self.logger.debug('NO key Mosflm ANOM results')
                        tmp_command_front += """,
                                                               mosflm_anom_status"""
                        tmp_command_back += """,
                                                                        %s"""
                        tmp_insert_values.append("NONE")

                #If it is necessary, enterthe mosflm strategy results into the database
                if enter_anom_mosflm:
                    anom_strat_type = 'mosflm'
                    tmp_command_front = """,
                                                           mosflm_anom_status,
                                                           mosflm_anom_res_limit,
                                                           mosflm_anom_completeness,
                                                           mosflm_anom_redundancy,
                                                           mosflm_anom_distance,
                                                           mosflm_anom_delta_phi,
                                                           mosflm_anom_img_exposure_time
                                                           """

                    tmp_command_back = """,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s"""

                    tmp_insert_values = [ 'SUCCESS',
                                         results['Mosflm ANOM strategy results']['strategy anom resolution'],
                                         results['Mosflm ANOM strategy results']['strategy anom completeness'][:-1],
                                         results['Mosflm ANOM strategy results']['strategy anom redundancy'],
                                         results['Mosflm ANOM strategy results']['strategy anom distance'],
                                         results['Mosflm ANOM strategy results']['strategy anom delta phi'],
                                         results['Mosflm ANOM strategy results']['strategy anom image exp time'] ]

                #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                command_front += tmp_command_front
                command_back  += tmp_command_back
                insert_values += tmp_insert_values

            except:
                self.logger.exception('Exception in addPairResult in the anomalous strategy results section')
                command_front += """,
                                                       best_anom_status,
                                                       mosflm_anom_status"""

                command_back += """,
                                                                %s,
                                                                %s"""

                insert_values += ['FAILED',
                                  'FAILED']

            #NOW the html and image files
            try:
                #Add stac summary only if there is a stac run
                if (info1.has_key('mk3_phi')):
                    summary_stac = results['Output files']['Stac summary html']
                else:
                    summary_stac = 'None'


                if results['Output files'] == 'FAILED':
                        command_back += ")"


                else:
                    tmp_command_front = """,
                                                       summary_short,
                                                       summary_long,
                                                       summary_stac,
                                                       image_raw_1,
                                                       image_preds_1,
                                                       image_raw_2,
                                                       image_preds_2,
                                                       best_plots,
                                                       stac_file1,
                                                       stac_file2"""

                    tmp_command_back = """,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s)"""

                    tmp_insert_values = [results['Output files']['Short summary html'],
                                      results['Output files']['Long summary html'],
                                      summary_stac,
                                      results['Output files']['image_path_raw_1'],
                                      results['Output files']['image_path_pred_1'],
                                      results['Output files']['image_path_raw_2'],
                                      results['Output files']['image_path_pred_2'],
                                      results['Output files']['Best plots html'],
                                      results['Output files']['STAC file1'],
                                      results['Output files']['STAC file2']]

                    #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                    command_front += tmp_command_front
                    command_back  += tmp_command_back
                    insert_values += tmp_insert_values

            except:
                command_back += ")"


            #deposit the result
            self.logger.debug(command_front+command_back)
            self.logger.debug(insert_values)
            cursor.execute(command_front+command_back,insert_values)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addPairResult')
            return(False)

        try:

            #get the result's pair_result_dict
            pair_result_dict = self.make_dicts('SELECT * FROM pair_results WHERE pair_result_id=%s',(cursor.lastrowid,))[0]

            #register the result in results table
            cursor.execute('INSERT INTO results (type,id,setting_id,process_id,sample_id,data_root_dir) VALUES (%s, %s, %s, %s, %s, %s)',('pair',pair_result_dict['pair_result_id'],pair_result_dict['settings_id'],pair_result_dict['process_id'],pair_result_dict['sample_id'],pair_result_dict['data_root_dir']))

            #add the result_id to the current dict
            pair_result_dict['result_id'] = cursor.lastrowid;

            #update the pair_results table with the result_id
            cursor.execute("UPDATE pair_results SET result_id=%s WHERE pair_result_id=%s",(pair_result_dict['result_id'],pair_result_dict['pair_result_id']))

            #log the "normal" strategy wedges
            if (norm_strat_type == 'best') :
                self.addStrategyWedges(id = pair_result_dict['pair_result_id'],
                                       int_type = 'pair',
                                       strategy_type = 'normal',
                                       strategy_program = 'best',
                                       results = results['Best results'])
            elif (norm_strat_type == 'mosflm') :
                self.addStrategyWedges(id = pair_result_dict['pair_result_id'],
                                       int_type = 'pair',
                                       strategy_type = 'normal',
                                       strategy_program = 'mosflm',
                                       results = results['Mosflm strategy results'])
            #log the anomalous strategy wedges
            if (anom_strat_type == 'best'):
                self.addStrategyWedges(id = pair_result_dict['pair_result_id'],
                                       int_type = 'pair',
                                       strategy_type = 'anomalous',
                                       strategy_program = 'best',
                                       results = results['Best ANOM results'])
            elif (anom_strat_type == 'mosflm') :
                self.addStrategyWedges(id = pair_result_dict['pair_result_id'],
                                       int_type = 'pair',
                                       strategy_type = 'anomalous',
                                       strategy_program = 'mosflm',
                                       results = results['Mosflm ANOM strategy results'])

            self.closeConnection(connection,cursor)
            return(pair_result_dict)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addPairResult - results updating subsection')
            self.closeConnection(connection,cursor)
            return(False)

    def addDiffcenterResult(self,dirs,info,settings,results):
        """
        Add data from diffraction-based centering analysis to diffcenter_results table
        """
        self.logger.debug('Database::addDiffcenterResult')
        self.logger.debug(results)
        try:
            #connect to the database
            connection,cursor = self.get_db_connection()

            #regardless of failure level
            command = '''INSERT INTO diffcenter_results ( process_id,
                                                          settings_id,
                                                          image_id,
                                                          fullname,
                                                          sample_id,
                                                          work_dir,
                                                          ice_rings,
                                                          max_cell,
                                                          distl_res,
                                                          overloads,
                                                          labelit_res,
                                                          total_spots,
                                                          good_b_spots,
                                                          max_signal_str,
                                                          mean_int_signal,
                                                          min_signal_str,
                                                          total_signal,
                                                          in_res_spots,
                                                          saturation_50) VALUES (%s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s )'''
            if dirs == False:
                insert_values = [None,
                                 None,
                                 results['image_id'],
                                 results['fullname'],
                                 results['sample_id'],
                                 None,
                                 results['ice_rings'],
                                 results['max_cell'],
                                 results['distl_res'],
                                 results['overloads'],
                                 results['labelit_res'],
                                 results['total_spots'],
                                 results['good_b_spots'],
                                 results['max_signal_str'],
                                 results['mean_int_signal'],
                                 results['min_signal_str'],
                                 results['total_signal'],
                                 results['in_res_spots'],
                                 results['saturation_50']]
            else:
                insert_values = [info['process_id'],
                                 settings['setting_id'],
                                 info['image_id'],
                                 info['fullname'],
                                 info['sample_id'],
                                 dirs['work'],
                                 results['Distl results']['ice_rings'][0],
                                 results['Distl results']['max_cell'][0],
                                 results['Distl results']['distl_res'][0],
                                 results['Distl results']['overloads'][0],
                                 results['Distl results']['labelit_res'][0],
                                 results['Distl results']['total_spots'][0],
                                 results['Distl results']['good_b_spots'][0],
                                 results['Distl results']['max_signal_str'][0],
                                 results['Distl results']['mean_int_signal'][0],
                                 results['Distl results']['min_signal_str'][0],
                                 results['Distl results']['total_signal'][0],
                                 results['Distl results']['in_res_spots'][0],
                                 results['Distl results']['saturation_50'][0]]

            #deposit the result
            self.logger.debug(command)
            self.logger.debug(insert_values)
            cursor.execute(command,insert_values)
            diffcenter_result_dict = self.make_dicts('SELECT * FROM diffcenter_results WHERE diffcenter_result_id=%s',(cursor.lastrowid,))[0]
            self.closeConnection(connection,cursor)
            return(diffcenter_result_dict)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addDiffcenterResult')
            self.closeConnection(connection,cursor)
            return(False)

    def addQuickanalysisResult(self,dirs,info,settings,results):
        """
        Add data from snapshot-based analysis  analysis to quickanalysis_results table
        """
        if self.logger:
          self.logger.debug('Database::addQuickanalysisResult')
          self.logger.debug(info)
          self.logger.debug(results)
        else:
          print 'Database::addQuickanalysisResult'

        try:
            #connect to the database
            connection,cursor = self.get_db_connection()

            #regardless of failure level
            command = '''INSERT INTO quickanalysis_results ( process_id,
                                                             settings_id,
                                                             image_id,
                                                             fullname,
                                                             sample_id,
                                                             work_dir,
                                                             ice_rings,
                                                             max_cell,
                                                             distl_res,
                                                             overloads,
                                                             labelit_res,
                                                             total_spots,
                                                             good_b_spots,
                                                             max_signal_str,
                                                             mean_int_signal,
                                                             min_signal_str,
                                                             total_signal,
                                                             in_res_spots,
                                                             saturation_50) VALUES (%s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s,
                                                                                    %s )'''
            if dirs == False:
                insert_values = [None,
                                 None,
                                 results['image_id'],
                                 results['fullname'],
                                 results['sample_id'],
                                 None,
                                 results['ice_rings'],
                                 results['max_cell'],
                                 results['resolution_1'],
                                 results['overloads'],
                                 results['resolution_2'],
                                 results['total_spots'],
                                 results['good_b_spots'],
                                 results['signal_max'],
                                 results['signal_mean'],
                                 results['signal_min'],
                                 results['total_signal'],
                                 results['in_res_spots'],
                                 results['saturation_50']]
            # TODO - add saturation min mean and max to the result
            else:
                if ('image_id' not in info):
                    info['image_id'] = 0
                    info['sample_id'] = 0
                insert_values = [info['process_id'],
                                 None,   #settings['setting_id']
                                 info['image_id'],
                                 info['fullname'],
                                 info['sample_id'],
                                 dirs['work'],
                                 results['Distl results']['ice_rings'][0],
                                 results['Distl results']['max_cell'][0],
                                 results['Distl results']['distl_res'][0],
                                 results['Distl results']['overloads'][0],
                                 results['Distl results']['labelit_res'][0],
                                 results['Distl results']['total_spots'][0],
                                 results['Distl results']['good_b_spots'][0],
                                 results['Distl results']['max_signal_str'][0],
                                 results['Distl results']['mean_int_signal'][0],
                                 results['Distl results']['min_signal_str'][0],
                                 results['total_signal'][0],
                                 results['Distl results']['in_res_spots'][0],
                                 results['saturation_50'][0]]

            #deposit the result
            if self.logger:
              self.logger.debug(command)
              self.logger.debug(insert_values)
            cursor.execute(command,insert_values)
            quickanalysis_result_dict = self.make_dicts('SELECT * FROM quickanalysis_results WHERE quickanalysis_result_id=%s',(cursor.lastrowid,))[0]
            self.closeConnection(connection,cursor)
            return(quickanalysis_result_dict)

        except:
            if self.logger:
              self.logger.exception('ERROR : unknown exception in Database::addQuickAnalysisResult')
              self.closeConnection(connection,cursor)
            return(False)

    def addYesSolved(self,result_id,sad_result_id=False):
        """
        Add a Yes status to solved column in integrate_ or merge_ results tables
        To be triggered by addSadResult, addCellAnalysisResult or addMrResult
        """
        self.logger.debug('Database::addYesSolved')

        if sad_result_id:
            #join sad_results and results tables to get type
            query = '''SELECT results.* FROM results,sad_results WHERE sad_results.sad_result_id=%s
                        AND sad_results.source_data_id=results.result_id'''
            request_dict = self.make_dicts(query=query, params=(sad_result_id,))
        elif result_id:
            query = "SELECT * FROM results WHERE result_id=%s"
            request_dict = self.make_dicts(query=query, params=(result_id,))
        result_table = request_dict[0]['type']
        if result_table == 'merge' or result_table == 'integrate':
            command = "UPDATE %s_results " % (result_table)
            command += "SET solved=%s WHERE result_id=%s"
            insert_values = ['Yes',
                            request_dict[0]['result_id']]
            #connect to the database
            connection,cursor = self.get_db_connection()

            cursor.execute(command,insert_values)
            #change timestamp in results table to cue runs list update
            command_restamp = "UPDATE results SET timestamp=NOW() WHERE result_id=%s"
            insert_restamp = [request_dict[0]['result_id']]
            cursor.execute(command_restamp,insert_restamp)
        else:
            self.logger.debug('Database::Wrong Type::Aborting Flagging')

    def addXia2Result(self,dirs,info,settings,results):
        """
        Add data to the integrate_results table
        Modified to work with updates (i.e. adding results from the same process over and over)
        """
        self.logger.debug('Database::addXia2Result DRD:%s' % dirs['data_root_dir'])

        #Determine the type of run this is
        if settings.has_key('request'):
            my_type = settings['request']['request_type']
        else:
            my_type ='original'

        #Check to see if there is a previous result with this process_id
        integrate_result_id,result_id = self.getTypeResultId(process_id=info['image_data']['process_id'])
        if (integrate_result_id):
            integrate_result_dict = self.getResultById(integrate_result_id, 'integrate')
        else:
            #make a new entry to then update
            integrate_result_id,result_id = self.makeNewResult(rtype='integrate',
                                                               process_id=info['image_data']['process_id'])
            integrate_result_dict = False

        try:
            #connect to the database
            connection,cursor = self.get_db_connection()

            #Information stored regardless of failure level
            command = '''UPDATE integrate_results SET timestamp=NOW(),
                                                       result_id=%s,
                                                       process_id=%s,
                                                       run_id=%s,
                                                       version=version+1,
                                                       pipeline=%s,
                                                       data_root_dir=%s,
                                                       settings_id=%s,
                                                       repr=%s,
                                                       template=%s,
                                                       date=%s,
                                                       work_dir=%s,
                                                       type=%s,
                                                       images_dir=%s,
                                                       image_start=%s,
                                                       image_end=%s'''

            insert_values = [ result_id,
                              info['image_data']['process_id'],
                              info['run_data']['run_id'],
                              'xia2',
                              dirs['data_root_dir'],
                              settings['setting_id'],
                              os.path.basename(dirs['work']),
                              info['image_data']['repr'],
                              info['image_data']['date'],
                              dirs['work'],
                              my_type,
                              info['image_data']['directory'],
                              info['run_data']['start'],
                              info['run_data']['total']+info['run_data']['start']-1 ]

            #FILES
            try:
                if (results['status'] == 'Error'):
                    tmp_command = ''',
                                                          integrate_status=%s,
                                                          parsed=%s,
                                                          plots=%s,
                                                          xia_log=%s'''

                    tmp_insert_values = ['FAILED','None','None',results['files']['xia_log']]

                else:
                    tmp_command = ''',
                                                          integrate_status=%s,
                                                          parsed=%s,
                                                          plots=%s,
                                                          xia_log=%s,
                                                          xscale_log=%s,
                                                          scala_log=%s,
                                                          unmerged_sca_file=%s,
                                                          sca_file=%s,
                                                          mtz_file=%s,
                                                          merge_file=%s'''

                    tmp_insert_values = [ results['status'],
                                          os.path.join(dirs['work'],results['parsed']),
                                          os.path.join(dirs['work'],results['plots']),
                                          results['files']['xia_log'],
                                          results['files']['xscale_log'],
                                          results['files']['scala_log'],
                                          results['files']['unmerged'],
                                          results['files']['scafile'],
                                          results['files']['mtzfile'],
                                          results['files']['mergable'] ]

                #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                command += tmp_command
                insert_values += tmp_insert_values

            except:
                self.logger.exception('Error in writing files section of integrate_result table')

            #SPACEGROUP and CELL info
            try:
                if (results['status'] == 'SUCCESS'):
                    cell = results['summary']['cell'].split()
                    #change the format of the time for database entry
                    proc_time = ''
                    for i in results['summary']['procTime'].split():
                        proc_time += i[:2]
                        if i[2] != 's':
                            proc_time += ':'
                    #handle rD values
                    if not results['summary'].has_key('rD_analysis'):
                        results['summary']['rD_analysis'] = 0
                        results['summary']['rD_conclusion'] = 0

                    tmp_command = ''',
                                                          spacegroup=%s,
                                                          a=%s,
                                                          b=%s,
                                                          c=%s,
                                                          alpha=%s,
                                                          beta=%s,
                                                          gamma=%s,
                                                          twinscore=%s,
                                                          proc_time=%s,
                                                          rd_analysis=%s,
                                                          rd_conclusion=%s'''

                    tmp_insert_values = [ results['summary']['spacegroup'],
                                          cell[0],
                                          cell[1],
                                          cell[2],
                                          cell[3],
                                          cell[4],
                                          cell[5],
                                          results['summary']['twinScore'],
                                          proc_time,
                                          results['summary']['rD_analysis'],
                                          results['summary']['rD_conclusion'] ]

                    #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                    command += tmp_command
                    insert_values += tmp_insert_values

            except:
                self.logger.exception('Error in writing spacegroup and cell info section of integrate_result table')


            #integrate_shell_results section
            try:
                if (results['status'] == 'SUCCESS'):
                    if integrate_result_dict:
                        overall_shell_id = self.addXia2ShellResult(shell_dict=results['summary']['overall'],
                                                                        type='overall',
                                                                        isr_id=integrate_result_dict['shell_overall'])
                        inner_shell_id   = self.addXia2ShellResult(shell_dict=results['summary']['innerShell'],
                                                                        type='inner',
                                                                        isr_id=integrate_result_dict['shell_inner'])
                        outer_shell_id   = self.addXia2ShellResult(shell_dict=results['summary']['outerShell'],
                                                                        type='outer',
                                                                        isr_id=integrate_result_dict['shell_outer'])
                    else:
                        overall_shell_id = self.addXia2ShellResult(shell_dict=results['summary']['overall'],
                                                                        type='overall')
                        inner_shell_id   = self.addXia2ShellResult(shell_dict=results['summary']['innerShell'],
                                                                        type='inner')
                        outer_shell_id   = self.addXia2ShellResult(shell_dict=results['summary']['outerShell'],
                                                                        type='outer')

                    command += ''',
                                                          shell_overall=%s,
                                                          shell_inner=%s,
                                                          shell_outer=%s'''

                    insert_values += [ overall_shell_id,
                                       inner_shell_id,
                                       outer_shell_id ]

            except:
                self.logger.exception('Error in writing integrate_shell_results section of integrate_result table')

            #finish up the commands
            command += ' WHERE integrate_result_id=%s'
            insert_values.append(integrate_result_id)

            #deposit the result
            self.logger.debug(command)
            self.logger.debug(insert_values)
            cursor.execute(command,insert_values)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addIntegrateResult')
            return(False)

        try:
            #get the result's pair_result_dict
            new_integrate_result_dict = self.make_dicts('SELECT * FROM integrate_results WHERE integrate_result_id=%s',(integrate_result_id,))[0]

            #update the result in results table
            cursor.execute('UPDATE results SET setting_id=%s,process_id=%s,sample_id=%s,data_root_dir=%s,timestamp=%s WHERE result_id=%s',
                           (new_integrate_result_dict['settings_id'],new_integrate_result_dict['process_id'],new_integrate_result_dict['sample_id'],new_integrate_result_dict['data_root_dir'],new_integrate_result_dict['timestamp'],result_id))

            #close the connection to the database
            self.closeConnection(connection,cursor)
            return(new_integrate_result_dict)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addIntegrateResult - results updating subsection')
            self.closeConnection(connection,cursor)
            return(False)

    def addXia2ShellResult(self,shell_dict,type,isr_id=None):
        """
        Add a shell result from integration and return the isr_id
        """
        self.logger.debug('addXia2ShellResult %s' % type)
        self.logger.debug(shell_dict)

        try:
            #connect to the database
            connection,cursor = self.get_db_connection()

            if not (isr_id):
                cursor.execute("INSERT INTO integrate_shell_results () VALUES ()")
                isr_id = cursor.lastrowid

            if (type != 'overall'):
                 shell_dict['wilsonB'] = '0'

            #regardless of failure level
            command = '''UPDATE integrate_shell_results SET shell_type=%s,
                                                             high_res=%s,
                                                             low_res=%s,
                                                             completeness=%s,
                                                             multiplicity=%s,
                                                             i_sigma=%s,
                                                             r_merge=%s,
                                                             r_meas=%s,
                                                             r_meas_pm=%s,
                                                             r_pim=%s,
                                                             r_pim_pm=%s,
                                                             wilson_b=%s,
                                                             partial_bias=%s,
                                                             anom_completeness=%s,
                                                             anom_multiplicity=%s,
                                                             anom_correlation=%s,
                                                             anom_slope=%s,
                                                             total_obs=%s,
                                                             unique_obs=%s WHERE isr_id=%s'''

            insert_values = [ type,
                              shell_dict['high_res'],
                              shell_dict['low_res'],
                              shell_dict['completeness'],
                              shell_dict['multiplicity'],
                              shell_dict['I/sigma'],
                              shell_dict['Rmerge'],
                              shell_dict['Rmeas(I)'],
                              shell_dict['Rmeas(I+/-)'],
                              shell_dict['Rpim(I)'],
                              shell_dict['Rpim(I+/-)'],
                              shell_dict['wilsonB'],
                              shell_dict['partialBias'],
                              shell_dict['anomComp'],
                              shell_dict['anomMult'],
                              shell_dict['anomCorr'],
                              shell_dict['anomSlope'],
                              shell_dict['totalObs'],
                              shell_dict['totalUnique'],
                              isr_id ]

            #deposit the result
            self.logger.debug(command)
            self.logger.debug(insert_values)
            cursor.execute(command,insert_values)
            self.closeConnection(connection,cursor)
            return(isr_id)

        except:
            self.logger.exception('Error in addXia2ShellResult')
            self.closeConnection(connection,cursor)
            return(0)

    def addIntegrateResult(self,dirs,info,settings,results):
        """
        Add data to the integrate_results table
        This function works with the new XDS-based fast integration pipeline
        Modified to work with updates (i.e. adding results from the same process over and over)
        """
        self.logger.debug('Database::addIntegrateResult DRD:%s' % dirs['data_root_dir'])

        #Determine the type of run this is
        if settings.has_key('request'):
            my_type = settings['request']['request_type']
        else:
            my_type ='original'

        #Check the results to construct a new repr on the fly
        my_repr = os.path.basename(dirs['work'])

        #Construct a template on the fly
        my_template = info["image_data"]["fullname"][:-7]+"###.img"

        #Check for request_id - if this is a reprocess event
        if (settings.has_key('request')):
            request_id = settings['request']['cloud_request_id']
        else:
            request_id = 0

        #Acquire the lock to avoid pesky problem with two rapid results
        self.LOCK.acquire()
        try:
            #Check to see if there is a previous result with this process_id
            integrate_result_id,result_id = self.getTypeResultId(process_id=info['image_data']['process_id'])
            if (integrate_result_id):
                integrate_result_dict = self.getResultById(integrate_result_id, 'integrate')
            else:
                #make a new entry to then update
                integrate_result_id,result_id = self.makeNewResult(rtype='integrate',
                                                                   process_id=info['image_data']['process_id'])
                integrate_result_dict = False
        except:
            self.logger.exception("Error in addIntegrateResult acquiring the result_ids")

        #Release the lock
        self.LOCK.release()

        try:
            self.logger.debug("Enter try")
            #connect to the database
            connection,cursor = self.get_db_connection()

            #Information stored regardless of failure level
            command = '''UPDATE integrate_results SET timestamp=NOW(),
                                                       result_id=%s,
                                                       process_id=%s,
                                                       run_id=%s,
                                                       sample_id=%s,
                                                       version=version+1,
                                                       pipeline=%s,
                                                       data_root_dir=%s,
                                                       settings_id=%s,
                                                       request_id=%s,
                                                       repr=%s,
                                                       template=%s,
                                                       date=%s,
                                                       work_dir=%s,
                                                       type=%s,
                                                       images_dir=%s,
                                                       image_start=%s,
                                                       image_end=%s'''

            insert_values = [ result_id,
                              info['image_data']['process_id'],
                              info['run_data']['run_id'],
                              info['image_data']['sample_id'],
                              'fastint',
                              dirs['data_root_dir'],
                              settings['setting_id'],
                              request_id,
                              my_repr,
                              my_template,
                              #info['image_data']['repr'],
                              info['image_data']['date'],
                              dirs['work'],
                              my_type,
                              info['image_data']['directory'],
                              results['summary']['wedge'].split('-')[0],
                              results['summary']['wedge'].split('-')[1] ]

            #FILES
            try:
                #a failed run
                if (results['status'] == 'FAILED'):
                    tmp_command = ''',
                                                          integrate_status=%s,
                                                          parsed=%s,
                                                          plots=%s,
                                                          xia_log=%s'''

                    tmp_insert_values = ['FAILED','None','None',results['files']['xia_log']]

                #The final result
                elif (results.has_key('files')):
                    tmp_command = ''',
                                                          integrate_status=%s,
                                                          parsed=%s,
                                                          summary_long=%s,
                                                          plots=%s,
                                                          xds_log=%s,
                                                          scala_log=%s,
                                                          mtz_file=%s,
                                                          hkl_file=%s,
                                                          merge_file=%s,
                                                          download_file=%s'''

                    tmp_insert_values = [ results['status'],
                                          os.path.join(dirs['work'],results['short']),
                                          os.path.join(dirs['work'],results['long']),
                                          os.path.join(dirs['work'],results['plots']),
                                          results['files']['xds_log'],
                                          results['files']['scala_log'],
                                          results['files']['mtzfile'],
                                          results['files']['xds_data'],
                                          results['files']['mergable'],
                                          results['files']['downloadable'] ]


                    if results['files'].has_key('ANOM_sca'):
                        tmp_command += ''',
                                                                  unmerged_sca_file=%s,
                                                                  sca_file=%s'''
                        tmp_insert_values += [ results['files']['ANOM_sca'],
                                              results['files']['NATIVE_sca'] ]

                        #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                        command += tmp_command
                        insert_values += tmp_insert_values

                #a partial run
                else:
                    tmp_command = ''',
                                                          integrate_status=%s,
                                                          parsed=%s,
                                                          summary_long=%s,
                                                          plots=%s'''

                    tmp_insert_values = [ results['status'],
                                          os.path.join(dirs['work'],results['short']),
                                          os.path.join(dirs['work'],results['long']),
                                          os.path.join(dirs['work'],results['plots']) ]

                #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                command += tmp_command
                insert_values += tmp_insert_values

            except:
                self.logger.exception('Error in writing files section of integrate_result table')

            #SPACEGROUP, CELL and anomalous
            try:
                if (results['status'] in ('SUCCESS','ANALYSIS','WORKING','FAILED')):
                    cell = results['summary']['scaling_unit_cell'][:]
                    tmp_command = ''',
                                                          spacegroup=%s,
                                                          a=%s,
                                                          b=%s,
                                                          c=%s,
                                                          alpha=%s,
                                                          beta=%s,
                                                          gamma=%s'''

                    tmp_insert_values = [ results['summary']['scaling_spacegroup'],
                                          cell[0],
                                          cell[1],
                                          cell[2],
                                          cell[3],
                                          cell[4],
                                          cell[5]]

                    #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                    command += tmp_command
                    insert_values += tmp_insert_values

            except:
                self.logger.exception('Error in writing spacegroup and cell info section of integrate_result table')


            #integrate_shell_results section
            try:
                if (results['status'] in ('SUCCESS','ANALYSIS','WORKING','FAILED')):
                    if integrate_result_dict:
                        overall_shell_id = self.addIntegrateShellResult(shell_dict=results['summary'],
                                                                        type='overall',
                                                                        isr_id=integrate_result_dict['shell_overall'])
                        inner_shell_id   = self.addIntegrateShellResult(shell_dict=results['summary'],
                                                                        type='inner',
                                                                        isr_id=integrate_result_dict['shell_inner'])
                        outer_shell_id   = self.addIntegrateShellResult(shell_dict=results['summary'],
                                                                        type='outer',
                                                                        isr_id=integrate_result_dict['shell_outer'])
                    else:
                        overall_shell_id = self.addIntegrateShellResult(shell_dict=results['summary'],
                                                                        type='overall')
                        inner_shell_id   = self.addIntegrateShellResult(shell_dict=results['summary'],
                                                                        type='inner')
                        outer_shell_id   = self.addIntegrateShellResult(shell_dict=results['summary'],
                                                                        type='outer')

                    command += ''',
                                                          shell_overall=%s,
                                                          shell_inner=%s,
                                                          shell_outer=%s'''

                    insert_values += [ overall_shell_id,
                                       inner_shell_id,
                                       outer_shell_id ]

            except:
                self.logger.exception('Error in writing integrate_shell_results section of integrate_result table')

            #finish up the commands
            command += ' WHERE integrate_result_id=%s'
            insert_values.append(integrate_result_id)

            #deposit the result
            self.logger.debug(command)
            self.logger.debug(insert_values)
            cursor.execute(command,insert_values)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addIntegrateResult')
            self.closeConnection(connection,cursor)
            return(False)

        try:
            #get the result's pair_result_dict
            new_integrate_result_dict = self.make_dicts('SELECT * FROM integrate_results WHERE integrate_result_id=%s',(integrate_result_id,))[0]

            #update the result in results table
            cursor.execute('UPDATE results SET setting_id=%s,process_id=%s,sample_id=%s,data_root_dir=%s,timestamp=%s WHERE result_id=%s',
                           (new_integrate_result_dict['settings_id'],new_integrate_result_dict['process_id'],new_integrate_result_dict['sample_id'],new_integrate_result_dict['data_root_dir'],new_integrate_result_dict['timestamp'],result_id))

            #close the connection to the database
            self.closeConnection(connection,cursor)
            return(new_integrate_result_dict)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addIntegrateResult - results updating subsection')
            self.closeConnection(connection,cursor)
            return(False)

    def addReIntegrateResult(self,dirs,info,settings,results):
        """
        Add data to the integrate_results table
        This function works with the new XDS-based fast integration pipeline
        Modified to work with updates (i.e. adding results from the same process over and over)
        """
        self.logger.debug('Database::addIntegrateResult DRD:%s' % dirs['data_root_dir'])

        #Determine the type of run this is
        if settings.has_key('request'):
            if (settings['request']['request_type'] == "start-fastin"):
                my_type = "refastint"
                my_pipeline = "fastint"
                results['files']['xia2_log'] = "None"
            else:
                my_type = "rexia2"
                my_pipeline = "xia2"
                results['files']['xds_log'] = "None"
                results['files']['scala_log'] = "None"

        #Check the results to construct a new repr on the fly
        #my_repr = "_".join(info["original"]["repr"].split("_")[:-1])+"_"+str(settings["request"]["frame_start"])+"-"+str(settings["request"]["frame_finish"])
        my_repr = info["original"]["repr"] + "_" + str(settings["request"]["frame_start"]) + "-" + str(settings["request"]["frame_finish"])

        #Check for request_id - if this is a reprocess event
        if (settings.has_key('request')):
            request_id = settings['request']['cloud_request_id']
        else:
            request_id = 0

        #Acquire the lock to avoid pesky problem with two rapid results
        self.LOCK.acquire()
        try:
            #Check to see if there is a previous result with this process_id
            integrate_result_id,result_id = self.getTypeResultId(process_id=settings['process_id'])
            try:
                if (integrate_result_id):
                    integrate_result_dict = self.getResultById(integrate_result_id, 'integrate')
                else:
                    #make a new entry to then update
                    integrate_result_id,result_id = self.makeNewResult(rtype='integrate',
                                                                       process_id=settings['process_id'])
                    integrate_result_dict = False
            except:
                self.logger.exception("Got the integrate_result_id, but no result dict")
                integrate_result_dict = False

        except:
            self.logger.exception("Error in addReIntegrateResult acquisition of result ids")

        #Release the lock
        self.LOCK.release()

        try:
            self.logger.debug("Enter try")
            #connect to the database
            connection,cursor = self.get_db_connection()

            #Information stored regardless of failure level
            command = '''UPDATE integrate_results SET timestamp=NOW(),
                                                       result_id=%s,
                                                       process_id=%s,
                                                       run_id=%s,
                                                       sample_id=%s,
                                                       version=version+1,
                                                       pipeline=%s,
                                                       data_root_dir=%s,
                                                       settings_id=%s,
                                                       request_id=%s,
                                                       repr=%s,
                                                       template=%s,
                                                       date=%s,
                                                       work_dir=%s,
                                                       type=%s,
                                                       images_dir=%s,
                                                       image_start=%s,
                                                       image_end=%s'''

            insert_values = [ result_id,
                              settings['process_id'],
                              info['original']['run_id'],
                              info['original']['sample_id'],
                              my_pipeline,
                              dirs['data_root_dir'],
                              settings['setting_id'],
                              request_id,
                              my_repr,
                              info['original']['template'],
                              info['original']['date'],
                              dirs['work'],
                              my_type,
                              info['original']['images_dir'],
                              settings['request']['frame_start'],
                              settings['request']['frame_finish'] ]

            #FILES
            try:
                #a failed run
                if (results['status'] == 'FAILED'):
                    tmp_command = ''',
                                                          integrate_status=%s,
                                                          parsed=%s,
                                                          plots=%s,
                                                          xia_log=%s'''

                    tmp_insert_values = ['FAILED','None','None',results['files']['xia_log']]

                #The final result
                elif (results.has_key('files')):
                    tmp_command = ''',
                                                          integrate_status=%s,
                                                          parsed=%s,
                                                          summary_long=%s,
                                                          plots=%s,
                                                          xia_log=%s,
                                                          xds_log=%s,
                                                          scala_log=%s,
                                                          mtz_file=%s,
                                                          hkl_file=%s,
                                                          merge_file=%s,
                                                          download_file=%s'''

                    tmp_insert_values = [ results['status'],
                                          os.path.join(dirs['work'],results['short']),
                                          os.path.join(dirs['work'],results['long']),
                                          os.path.join(dirs['work'],results['plots']),
                                          results['files']['xia2_log'],
                                          results['files']['xds_log'],
                                          results['files']['scala_log'],
                                          results['files']['mtzfile'],
                                          results['files']['xds_data'],
                                          results['files']['mergable'],
                                          results['files']['downloadable'] ]


                    if results['files'].has_key('ANOM_sca'):
                        tmp_command += ''',
                                                                  unmerged_sca_file=%s,
                                                                  sca_file=%s'''
                        tmp_insert_values += [ results['files']['ANOM_sca'],
                                              results['files']['NATIVE_sca'] ]

                        #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                        command += tmp_command
                        insert_values += tmp_insert_values

                #a partial run
                else:
                    tmp_command = ''',
                                                          integrate_status=%s,
                                                          parsed=%s,
                                                          summary_long=%s,
                                                          plots=%s'''

                    tmp_insert_values = [ results['status'],
                                          os.path.join(dirs['work'],results['short']),
                                          os.path.join(dirs['work'],results['long']),
                                          os.path.join(dirs['work'],results['plots']) ]

                #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                command += tmp_command
                insert_values += tmp_insert_values

            except:
                self.logger.exception('Error in writing files section of integrate_result table')

            #SPACEGROUP, CELL and anomalous
            try:
                if (results['status'] in ('SUCCESS','ANALYSIS','WORKING','FAILED')):
                    cell = results['summary']['scaling_unit_cell'][:]
                    tmp_command = ''',
                                                          spacegroup=%s,
                                                          a=%s,
                                                          b=%s,
                                                          c=%s,
                                                          alpha=%s,
                                                          beta=%s,
                                                          gamma=%s'''

                    tmp_insert_values = [ results['summary']['scale_spacegroup'],
                                          cell[0],
                                          cell[1],
                                          cell[2],
                                          cell[3],
                                          cell[4],
                                          cell[5] ]

                    #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                    command += tmp_command
                    insert_values += tmp_insert_values

            except:
                self.logger.exception('Error in writing spacegroup and cell info section of integrate_result table')


            #integrate_shell_results section
            try:
                if (results['status'] in ('SUCCESS','ANALYSIS','WORKING','FAILED')):
                    if integrate_result_dict:
                        overall_shell_id = self.addIntegrateShellResult(shell_dict=results['summary'],
                                                                        type='overall',
                                                                        isr_id=integrate_result_dict['shell_overall'])
                        inner_shell_id   = self.addIntegrateShellResult(shell_dict=results['summary'],
                                                                        type='inner',
                                                                        isr_id=integrate_result_dict['shell_inner'])
                        outer_shell_id   = self.addIntegrateShellResult(shell_dict=results['summary'],
                                                                        type='outer',
                                                                        isr_id=integrate_result_dict['shell_outer'])
                    else:
                        overall_shell_id = self.addIntegrateShellResult(shell_dict=results['summary'],
                                                                        type='overall')
                        inner_shell_id   = self.addIntegrateShellResult(shell_dict=results['summary'],
                                                                        type='inner')
                        outer_shell_id   = self.addIntegrateShellResult(shell_dict=results['summary'],
                                                                        type='outer')

                    command += ''',
                                                          shell_overall=%s,
                                                          shell_inner=%s,
                                                          shell_outer=%s'''

                    insert_values += [ overall_shell_id,
                                       inner_shell_id,
                                       outer_shell_id ]

            except:
                self.logger.exception('Error in writing integrate_shell_results section of integrate_result table')

            #finish up the commands
            command += ' WHERE integrate_result_id=%s'
            insert_values.append(integrate_result_id)

            #deposit the result
            self.logger.debug(command)
            self.logger.debug(insert_values)
            cursor.execute(command,insert_values)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addIntegrateResult')
            self.closeConnection(connection,cursor)
            return(False)

        try:
            #get the result's pair_result_dict
            new_integrate_result_dict = self.make_dicts('SELECT * FROM integrate_results WHERE integrate_result_id=%s',(integrate_result_id,))[0]

            #update the result in results table
            cursor.execute('UPDATE results SET setting_id=%s,process_id=%s,sample_id=%s,data_root_dir=%s,timestamp=%s WHERE result_id=%s',
                           (new_integrate_result_dict['settings_id'],new_integrate_result_dict['process_id'],new_integrate_result_dict['sample_id'],new_integrate_result_dict['data_root_dir'],new_integrate_result_dict['timestamp'],result_id))
            self.closeConnection(connection,cursor)
            return(new_integrate_result_dict)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addIntegrateResult - results updating subsection')
            self.closeConnection(connection,cursor)
            return(False)

    def addIntegrateShellResult(self,shell_dict,type,isr_id=None):
        """
        Add a shell result from integration and return the isr_id
        """
        self.logger.debug('addIntegrateShellResult %s' % type)
        self.logger.debug(shell_dict)

        #filter NaNs out of dict
        for k,v in shell_dict.iteritems():
            if (v == 'NaN'):
                shell_dict[k] = 0

        if (type == 'overall'):
            pos = 0
        elif (type == 'inner'):
            pos = 1
        elif (type == 'outer'):
            pos = 2

        try:
            #connect to the database
            connection,cursor = self.get_db_connection()

            if not (isr_id):
                cursor.execute("INSERT INTO integrate_shell_results () VALUES ()")
                isr_id = cursor.lastrowid

            #regardless of failure level
            command = '''UPDATE integrate_shell_results SET shell_type=%s,
                                                             high_res=%s,
                                                             low_res=%s,
                                                             completeness=%s,
                                                             multiplicity=%s,
                                                             i_sigma=%s,
                                                             cc_half=%s,
                                                             r_merge=%s,
                                                             r_merge_anom=%s,
                                                             r_meas=%s,
                                                             r_meas_pm=%s,
                                                             r_pim=%s,
                                                             r_pim_pm=%s,
                                                             anom_completeness=%s,
                                                             anom_multiplicity=%s,
                                                             anom_correlation=%s,
                                                             anom_slope=%s,
                                                             total_obs=%s,
                                                             unique_obs=%s WHERE isr_id=%s'''

            insert_values = [ type,
                              shell_dict['bins_high'][pos],
                              shell_dict['bins_low'][pos],
                              shell_dict['completeness'][pos],
                              shell_dict['multiplicity'][pos],
                              shell_dict['isigi'][pos],
                              shell_dict['cc-half'][pos],
                              shell_dict['rmerge_norm'][pos],
                              shell_dict['rmerge_anom'][pos],
                              shell_dict['rmeas_norm'][pos],
                              shell_dict['rmeas_anom'][pos],
                              shell_dict['rpim_norm'][pos],
                              shell_dict['rpim_anom'][pos],
                              shell_dict['anom_completeness'][pos],
                              shell_dict['anom_multiplicity'][pos],
                              shell_dict['anom_correlation'][pos],
                              shell_dict['anom_slope'][0],
                              shell_dict['total_obs'][pos],
                              shell_dict['unique_obs'][pos],
                              isr_id ]

            #deposit the result
            self.logger.debug(command)
            self.logger.debug(insert_values)
            cursor.execute(command,insert_values)
            self.closeConnection(connection,cursor)
            return(isr_id)

        except:
            self.logger.exception('Error in addXia2ShellResult')
            self.closeConnection(connection,cursor)
            return(0)

    def addSimpleMergeResult(self,dirs,info,settings,results):
        """
        Add data to the merge_results table
        """
        self.logger.debug('Database::addSimpleMergeResult DRD:%s' % dirs['data_root_dir'])

        #Check for request_id - if this is a reprocess event
        if (settings.has_key('request')):
            request_id = settings['request']['cloud_request_id']
        else:
            request_id = 0

        #get the lock
        self.LOCK.acquire()

        try:
            #Check to see if there is a previous result with this process_id
            merge_result_id,result_id = self.getTypeResultId(process_id=info['process_id'])
            if (merge_result_id):
                merge_result_dict = self.getResultById(merge_result_id, 'merge')
            else:
                #make a new entry to then update
                merge_result_id,result_id = self.makeNewResult(rtype='merge',
                                                               process_id=info['process_id'])
                merge_result_dict = False
        except:
            self.logger.exception("Error in addSimpleMergeResult acquisition of result ids")

        #Release the lock
        self.LOCK.release()

        try:
            self.logger.debug("Enter try")
            #connect to the database
            connection,cursor = self.get_db_connection()

            #Information stored regardless of failure level
            command = '''UPDATE merge_results SET timestamp=NOW(),
                                                  result_id=%s,
                                                  process_id=%s,
                                                  data_root_dir=%s,
                                                  settings_id=%s,
                                                  request_id=%s,
                                                  repr=%s,
                                                  work_dir=%s,
                                                  set1=%s,
                                                  set2=%s,
                                                  wavelength=%s'''

            insert_values = [ result_id,
                              info['process_id'],
                              dirs['data_root_dir'],
                              settings['setting_id'],
                              settings["request"]["cloud_request_id"],
                              info["repr"],
                              dirs['work'],
                              info['original']['result_id'],
                              info['secondary']['result_id'],
                              info['original']['wavelength']]

            #FILES
            try:
                tmp_command = ''',
                                                  merge_status=%s,
                                                  summary=%s,
                                                  details=%s,
                                                  plots=%s,
                                                  merge_file=%s,
                                                  mtz_file=%s,
                                                  download_file=%s'''

                tmp_insert_values = [ "SUCCESS",
                                      os.path.join(dirs['work'],results['short']),
                                      os.path.join(dirs['work'],results['long']),
                                      os.path.join(dirs['work'],results['plots']),
                                      results['merge_file'],
                                      results['mtz_file'],
                                      results['download_file'] ]


                #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                command += tmp_command
                insert_values += tmp_insert_values

            except:
                self.logger.exception('Error in writing files section of merge_results table')
                #a failed run
                tmp_command = ''',
                                          merge_status=%s,
                                          parsed=%s,
                                          details=%s
                                          plots=%s,
                                          merge_file=%s,
                                          download_file=%s'''

                tmp_insert_values = ['FAILED',
                                     'None',
                                     'None',
                                     'None',
                                     'None',
                                     'None']

                #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                command += tmp_command
                insert_values += tmp_insert_values

            #SPACEGROUP, CELL and anomalous
            try:
                if (results['status'] in ('SUCCESS','WORKING','FAILED')):
                    cell = results['summary']['scaling_unit_cell'][:]
                    tmp_command = ''',
                                                          spacegroup=%s,
                                                          a=%s,
                                                          b=%s,
                                                          c=%s,
                                                          alpha=%s,
                                                          beta=%s,
                                                          gamma=%s'''

                    tmp_insert_values = [ results['summary']['scale_spacegroup'],
                                          cell[0],
                                          cell[1],
                                          cell[2],
                                          cell[3],
                                          cell[4],
                                          cell[5]]

                    #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                    command += tmp_command
                    insert_values += tmp_insert_values

            except:
                self.logger.exception('Error in writing spacegroup and cell info section of merge_results table')

            #merge_shell_results section
            try:
                if (results['status'] in ('SUCCESS','WORKING','FAILED')):

                    overall_shell_id = self.addMergeShellResult(shell_dict=results['summary'],
                                                                    type='overall')
                    inner_shell_id   = self.addMergeShellResult(shell_dict=results['summary'],
                                                                    type='inner')
                    outer_shell_id   = self.addMergeShellResult(shell_dict=results['summary'],
                                                                    type='outer')

                    command += ''',
                                                          shell_overall=%s,
                                                          shell_inner=%s,
                                                          shell_outer=%s'''

                    insert_values += [ overall_shell_id,
                                       inner_shell_id,
                                       outer_shell_id ]

            except:
                self.logger.exception('Error in writing merge_shell_results section of merge_result table')

            #finish up the commands
            command += ' WHERE merge_result_id=%s'
            insert_values.append(merge_result_id)

            #deposit the result
            self.logger.debug(command)
            self.logger.debug(insert_values)
            cursor.execute(command,insert_values)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addMergeResult')
            self.closeConnection(connection,cursor)
            return(False)

        try:
            #get the result's pair_result_dict
            new_merge_result_dict = self.make_dicts('SELECT * FROM merge_results WHERE merge_result_id=%s',(merge_result_id,))[0]

            #update the result in results table
            cursor.execute('UPDATE results SET setting_id=%s,process_id=%s,data_root_dir=%s,timestamp=%s WHERE result_id=%s',
                           (new_merge_result_dict['settings_id'],new_merge_result_dict['process_id'],new_merge_result_dict['data_root_dir'],new_merge_result_dict['timestamp'],result_id))
            self.closeConnection(connection,cursor)
            return(new_merge_result_dict)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addMergeResult - results updating subsection')
            self.closeConnection(connection,cursor)
            return(False)

    def addMergeShellResult(self,shell_dict,type,msr_id=None):
        """
        Add a shell result from merging and return the msr_id
        """
        self.logger.debug('addMergeShellResult %s' % type)
        self.logger.debug(shell_dict)

        if (type == 'overall'):
            pos = 0
        elif (type == 'inner'):
            pos = 1
        elif (type == 'outer'):
            pos = 2

        try:
            #connect to the database
            connection,cursor = self.get_db_connection()

            if not (msr_id):
                cursor.execute("INSERT INTO merge_shell_results () VALUES ()")
                msr_id = cursor.lastrowid

            #regardless of failure level
            command = ''' UPDATE merge_shell_results SET shell_type=%s,
                                                         high_res=%s,
                                                         low_res=%s,
                                                         completeness=%s,
                                                         multiplicity=%s,
                                                         i_sigma=%s,
                                                         r_merge=%s,
                                                         r_meas=%s,
                                                         r_meas_pm=%s,
                                                         r_pim=%s,
                                                         r_pim_pm=%s,
                                                         partial_bias=%s,
                                                         anom_completeness=%s,
                                                         anom_multiplicity=%s,
                                                         anom_correlation=%s,
                                                         anom_slope=%s,
                                                         total_obs=%s,
                                                         unique_obs=%s WHERE msr_id=%s'''

            insert_values = [ type,
                              shell_dict['bins_high'][pos],
                              shell_dict['bins_low'][pos],
                              shell_dict['completeness'][pos],
                              shell_dict['multiplicity'][pos],
                              shell_dict['isigi'][pos],
                              shell_dict['rmerge'][pos],
                              shell_dict['rmeas_norm'][pos],
                              shell_dict['rmeas_anom'][pos],
                              shell_dict['rpim_norm'][pos],
                              shell_dict['rpim_anom'][pos],
                              shell_dict['bias'][pos],
                              shell_dict['anom_completeness'][pos],
                              shell_dict['anom_multiplicity'][pos],
                              shell_dict['anom_correlation'][pos],
                              shell_dict['anom_slope'][0],
                              shell_dict['total_obs'][pos],
                              shell_dict['unique_obs'][pos],
                              msr_id ]

            #deposit the result
            self.logger.debug(command)
            self.logger.debug(insert_values)
            cursor.execute(command,insert_values)
            self.closeConnection(connection,cursor)
            return(msr_id)

        except:
            self.logger.exception('Error in addMergeShellResult')
            self.closeConnection(connection,cursor)
            return(0)

    def traceRunFromMerge(self,merge_id):
        """
        Acquire run numbers for a given merge_results_id
        """
        self.logger.debug('Database::traceRunFromMerge merge_result_id:%d' % merge_id)

        #Get all the result ids - down to when all the result_ids are from integrate_results
        integrate_ids = []
        merge_ids = [merge_id,]
        for m_id in merge_ids:
            my_dict = self.getResultById(merge_id, "merge")
            sets = (my_dict['set1'],my_dict['set2'])
            for set in sets:
                my_type = self.getTypeByResultId(set)
                if (my_type == 'integrate'):
                    integrate_ids.append(set)
                elif (my_type == 'merge'):
                    merge_ids.append(set)
        self.logger.debug(integrate_ids)

        #now get the runs for the integrates
        run_ids = []
        for integrate_id in integrate_ids:
            run_ids.append(self.make_dicts("SELECT run_id FROM integrate_results WHERE result_id=%s", (integrate_id,),'DATA')[0]['run_id'])
        self.logger.debug(run_ids)
        #
        return(run_ids)

    def addIntegrateResult1(self,dirs,info,settings,results):
        """
        Add data to the integrate_results table
        """
        self.logger.debug('Database::addIntegrateResult DRD:%s' % dirs['data_root_dir'])

        #Determine the type of run this is
        if settings.has_key('request'):
            my_type = settings['request']['request_type']
        else:
            my_type ='original'

        try:
            #connect to the database
            connection,cursor = self.get_db_connection()

            #regardless of failure level
            command_front = """INSERT INTO integrate_results ( process_id,
                                                          run_id,
                                                          data_root_dir,
                                                          settings_id,
                                                          repr,
                                                          template,
                                                          date,
                                                          work_dir,
                                                          type,
                                                          images_dir,
                                                          image_start,
                                                          image_end"""

            command_back = """) VALUES ( %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s"""

            insert_values = [ info['image_data']['process_id'],
                              info['run_data']['run_id'],
                              dirs['data_root_dir'],
                              settings['setting_id'],
                              os.path.basename(dirs['work']),
                              info['image_data']['repr'],
                              info['image_data']['date'],
                              dirs['work'],
                              my_type,
                              info['image_data']['directory'],
                              info['run_data']['start'],
                              info['run_data']['total']+info['run_data']['start']-1 ]

            #FILES
            try:
                if (results['status'] == 'Error'):
                    tmp_command_front = """,
                                                          integrate_status,
                                                          parsed,
                                                          plots,
                                                          xia_log"""

                    tmp_command_back = """,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s"""

                    tmp_insert_values = ['FAILED','None','None',results['files']['xia_log']]

                else:
                    tmp_command_front = """,
                                                          integrate_status,
                                                          parsed,
                                                          plots,
                                                          xia_log,
                                                          xscale_log,
                                                          scala_log,
                                                          unmerged_sca_file,
                                                          sca_file,
                                                          mtz_file,
                                                          merge_file,
                                                          wavelength"""

                    tmp_command_back = """,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s"""

                    tmp_insert_values = [ results['status'],
                                          os.path.join(dirs['work'],results['parsed']),
                                          os.path.join(dirs['work'],results['plots']),
                                          results['files']['xia_log'],
                                          results['files']['xscale_log'],
                                          results['files']['scala_log'],
                                          results['files']['unmerged'],
                                          results['files']['scafile'],
                                          results['files']['mtzfile'],
                                          results['files']['mergable'],
                                          info['image_data']['wavelength'] ]

                #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                command_front += tmp_command_front
                command_back  += tmp_command_back
                insert_values += tmp_insert_values

            except:
                self.logger.exception('Error in writing files section of integrate_result table')

            #SPACEGROUP and CELL info
            try:
                if (results['status'] == 'SUCCESS'):
                    cell = results['summary']['cell'].split()
                    #change the format of the time for database entry
                    proc_time = ''
                    for i in results['summary']['procTime'].split():
                        proc_time += i[:2]
                        if i[2] != 's':
                            proc_time += ':'
                    #handle rD values
                    if not results['summary'].has_key('rD_analysis'):
                        results['summary']['rD_analysis'] = 0
                        results['summary']['rD_conclusion'] = 0

                    tmp_command_front = """,
                                                          spacegroup,
                                                          a,
                                                          b,
                                                          c,
                                                          alpha,
                                                          beta,
                                                          gamma,
                                                          twinscore,
                                                          proc_time,
                                                          rd_analysis,
                                                          rd_conclusion"""

                    tmp_command_back = """,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s,
                                                                            %s"""

                    tmp_insert_values = [ results['summary']['spacegroup'],
                                          cell[0],
                                          cell[1],
                                          cell[2],
                                          cell[3],
                                          cell[4],
                                          cell[5],
                                          results['summary']['twinScore'],
                                          proc_time,
                                          results['summary']['rD_analysis'],
                                          results['summary']['rD_conclusion'] ]

                    #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                    command_front += tmp_command_front
                    command_back  += tmp_command_back
                    insert_values += tmp_insert_values

            except:
                self.logger.exception('Error in writing spacegroup and cell info section of integrate_result table')


            #integrate_shell_results section
            try:
                if (results['status'] == 'SUCCESS'):
                    overall_shell_id = self.addIntegrateShellResult(results['summary']['overall'],   'overall')
                    inner_shell_id   = self.addIntegrateShellResult(results['summary']['innerShell'],'inner')
                    outer_shell_id   = self.addIntegrateShellResult(results['summary']['outerShell'],'outer')

                    command_front += """,
                                                          shell_overall,
                                                          shell_inner,
                                                          shell_outer"""

                    command_back += """,
                                                                            %s,
                                                                            %s,
                                                                            %s"""

                    insert_values += [ overall_shell_id,
                                       inner_shell_id,
                                       outer_shell_id ]

            except:
                self.logger.exception('Error in writing integrate_shell_results section of integrate_result table')

            #finish up the commands
            command_back += ")"

            #deposit the result
            self.logger.debug(command_front+command_back)
            self.logger.debug(insert_values)
            cursor.execute(command_front+command_back,insert_values)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addIntegrateResult')
            self.closeConnection(connection,cursor)
            return(False)

        try:
            #get the result's pair_result_dict
            integrate_result_dict = self.make_dicts('SELECT * FROM integrate_results WHERE integrate_result_id=%s',(cursor.lastrowid,))[0]

            #register the result in results table
            cursor.execute('INSERT INTO results (type,id,setting_id,process_id,data_root_dir) VALUES (%s, %s, %s, %s, %s, %s)',('integrate',integrate_result_dict['integrate_result_id'],integrate_result_dict['settings_id'],integrate_result_dict['process_id'],integrate_result_dict['sample_id'],integrate_result_dict['data_root_dir']))

            #add the result_id to the current dict
            integrate_result_dict['result_id'] = cursor.lastrowid;

            #update the integrate_results table with the result_id
            cursor.execute("UPDATE integrate_results SET result_id=%s WHERE integrate_result_id=%s",(integrate_result_dict['result_id'],integrate_result_dict['integrate_result_id']))
            self.closeConnection(connection,cursor)
            return(integrate_result_dict)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addIntegrateResult - results updating subsection')
            self.closeConnection(connection,cursor)
            return(False)

    def addIntegrateShellResult1(self,shell_dict,type):
        """
        Add a shell result from integration and return the isr_id
        """
        self.logger.debug('addIntegrateShellResult %s' % type)
        self.logger.debug(shell_dict)

        try:
            #connect to the database
            connection,cursor = self.get_db_connection()

            if (type != 'overall'):
                 shell_dict['wilsonB'] = '0'

            #regardless of failure level
            command = """INSERT INTO integrate_shell_results ( shell_type,
                                                                high_res,
                                                                low_res,
                                                                completeness,
                                                                multiplicity,
                                                                i_sigma,
                                                                r_merge,
                                                                r_meas,
                                                                r_meas_pm,
                                                                r_pim,
                                                                r_pim_pm,
                                                                wilson_b,
                                                                partial_bias,
                                                                anom_completeness,
                                                                anom_multiplicity,
                                                                anom_correlation,
                                                                anom_slope,
                                                                total_obs,
                                                                unique_obs ) VALUES ( %s,
                                                                                        %s,
                                                                                        %s,
                                                                                        %s,
                                                                                        %s,
                                                                                        %s,
                                                                                        %s,
                                                                                        %s,
                                                                                        %s,
                                                                                        %s,
                                                                                        %s,
                                                                                        %s,
                                                                                        %s,
                                                                                        %s,
                                                                                        %s,
                                                                                        %s,
                                                                                        %s,
                                                                                        %s,
                                                                                        %s)"""

            insert_values = [ type,
                              shell_dict['high_res'],
                              shell_dict['low_res'],
                              shell_dict['completeness'],
                              shell_dict['multiplicity'],
                              shell_dict['I/sigma'],
                              shell_dict['Rmerge'],
                              shell_dict['Rmeas(I)'],
                              shell_dict['Rmeas(I+/-)'],
                              shell_dict['Rpim(I)'],
                              shell_dict['Rpim(I+/-)'],
                              shell_dict['wilsonB'],
                              shell_dict['partialBias'],
                              shell_dict['anomComp'],
                              shell_dict['anomMult'],
                              shell_dict['anomCorr'],
                              shell_dict['anomSlope'],
                              shell_dict['totalObs'],
                              shell_dict['totalUnique'] ]

            #deposit the result
            self.logger.debug(command)
            self.logger.debug(insert_values)
            cursor.execute(command,insert_values)

            #now get the isr_id to return
            isr_id = cursor.lastrowid
            self.closeConnection(connection,cursor)
            return(isr_id)

        except:
            self.logger.exception('Error in addIntegrateShellResult')
            self.closeConnection(connection,cursor)
            return(0)

    ##########################
    # Methods for MR results #
    ##########################
    def addMrResult(self,dirs,info,settings,results):
        """
        Add data to the mr_results table.

        dirs - dict containing directory information for the agent
               used for work and data_root_dir
        info - dict containing information used by the agent
               used for sample_id and run_id
        settings - dict containing settings from the site
                   importantly this contains the original request
                   multiple uses
        results - dict containing result information from the agent
        """

        self.logger.debug('Database::addMrResult')
        self.logger.debug(dirs)
        self.logger.debug(info)
        self.logger.debug(settings)
        self.logger.debug(results)

        #Catch non-standard entries
        my_repr = os.path.basename(dirs['work'])
        #debugging
        #self.logger.debug("Result process_id %d"%settings['process_id'])
        #Acquire the lock to avoid pesky problem with too rapid results
        self.LOCK.acquire()
        try:
            #Check to see if there is a previous result with this process_id
            mr_result_id,result_id = self.getTypeResultId(process_id=settings['process_id'])
            #A little debugging
            #self.logger.debug("mr_result_id: %s   result_id: %s" % (str(mr_result_id),str(result_id)))
            #If this is a new entry for an established process, get the old info
            if (mr_result_id):
                self.logger.debug("Getting mr result dict")
                mr_result_dict = self.getResultById(mr_result_id, 'mr')
            #First time entry - make a new result
            else:
                self.logger.debug("Creating new result.")
                #make a new entry to then update
                mr_result_id,result_id = self.makeNewResult(rtype='mr',
                                                            process_id=settings['process_id'])
                mr_result_dict = False
        except:
            sel.flogger.exception("Error in addMrResult result ids acquisition")

        #Release Lock
        self.LOCK.release()
        self.logger.debug('Database::addMrResult3')
        try:
            #Handle the individual results
            successful = False
            mr_results = results['Cell analysis results']
            for spacegroup in mr_results.keys():
                if mr_results[spacegroup]['AutoMR results']['AutoMR nosol'] == 'False':
                    successful = True
                    #Add the solution
                    self.logger.debug("Adding solution for %s"%spacegroup)
                    self.addMrSolution(mr_result_id=mr_result_id,
                                       spacegroup=spacegroup,
                                       result_dict=mr_results[spacegroup]['AutoMR results'])
                    #Add flag to merge or integrate results table for solved status
                    self.addYesSolved(settings['request']['original_result_id'])
            #self.logger.debug('Database::addMrResult4')
            #decide the run status
            if (results['status'] == "SUCCESS"):
                if successful:
                    results['status'] = "SUCCESS"
                else:
                    results['status'] = "COMPLETE"

            #connect to the database
            connection,cursor = self.get_db_connection()
            #self.logger.debug('Database::addMrResult5')
            #Information stored regardless of failure level
            command = '''UPDATE mr_results SET  timestamp=NOW(),
                                                result_id=%s,
                                                process_id=%s,
                                                settings_id=%s,
                                                request_id=%s,
                                                source_data_id=%s,
                                                data_root_dir=%s,
                                                work_dir=%s,
                                                repr=%s,
                                                version=version+1,
                                                mr_status=%s,
                                                summary_html=%s WHERE mr_result_id=%s'''

            insert_values = [ result_id,
                              settings['process_id'],
                              settings['setting_id'],
                              settings['request']['cloud_request_id'],
                              settings['request']['original_result_id'],
                              dirs['data_root_dir'],
                              dirs['work'],
                              my_repr,
                              results['status'],
                              results['Output files']['Cell summary html'],
                              mr_result_id]
            #self.logger.debug('Database::addMrResult6')
            #deposit the result
            self.logger.debug(command)
            self.logger.debug(insert_values)
            cursor.execute(command,insert_values)

            #now get the full dict that has just been added
            new_mr_result_dict = self.make_dicts('SELECT * FROM mr_results WHERE mr_result_id=%s',(mr_result_id,))[0]

        except:
            self.logger.exception('ERROR : unknown exception in Database::addMrResult')
            self.closeConnection(connection,cursor)
            return(False)

        #Update the results table
        try:
            self.logger.debug("Entering the results updating section mr_result_id:%d"%mr_result_id)
            #update the result in results table
            cursor.execute('UPDATE results SET setting_id=%s,process_id=%s,data_root_dir=%s,display=%s,timestamp=%s WHERE result_id=%s',
                           (new_mr_result_dict['settings_id'],new_mr_result_dict['process_id'],new_mr_result_dict['data_root_dir'],'show',new_mr_result_dict['timestamp'],result_id))

        except:
            self.logger.exception('ERROR : unknown exception in Database::addMrResult - results updating subsection')
            self.closeConnection(connection,cursor)
            return(False)
        #self.logger.debug('Database::addMrResult7')
        self.closeConnection(connection,cursor)
        return(new_mr_result_dict)

    def addMrSolution(self,mr_result_id,spacegroup,result_dict):
        """
        Add molecular replacement solution

        mr_result_id - index of the parent MrResult
        spacegroup - the spacegroup passed in from caller - there seems to be an error or different convention in the trial result
        result_dict - dict containing info on this solution to parent MR
        """

        self.logger.debug('Database::addMrSolution spacegroup:%s'%spacegroup)

        #find if there is a previous entry for this result
        query1 = "SELECT * FROM mr_trial_results WHERE mr_result_id=%s AND spacegroup=%s"
        tmp_dict = self.make_dicts(query=query1,
                                  params=(mr_result_id,spacegroup))
        #connect to the database
        connection,cursor = self.get_db_connection()

        if (len(tmp_dict) > 0):
            query2 = """UPDATE mr_trial_results SET gain=%s,
                                                    rfz=%s,
                                                    tfz=%s,
                                                    archive=%s WHERE  mr_result_id=%s AND spacegroup=%s"""
            insert_values = (result_dict['AutoMR gain'],
                             result_dict['AutoMR rfz'],
                             result_dict['AutoMR tfz'],
                             result_dict['AutoMR tar'],
                             mr_result_id,
                             spacegroup)  #result_dict['AutoMR sg'])

        else:
            query2 = """INSERT INTO mr_trial_results (mr_result_id,
                                                      gain,
                                                      rfz,
                                                      tfz,
                                                      spacegroup,
                                                      archive) VALUES (%s,
                                                                       %s,
                                                                       %s,
                                                                       %s,
                                                                       %s,
                                                                       %s)"""
            insert_values = (mr_result_id,
                             result_dict['AutoMR gain'],
                             result_dict['AutoMR rfz'],
                             result_dict['AutoMR tfz'],
                             spacegroup,
                             result_dict['AutoMR tar'])

        #commit the data to the database
        cursor.execute(query2,insert_values)
        self.closeConnection(connection,cursor)

    def getMrTrialResult(self,mr_result_id):
        """
        Get molecular replacement solutions

        mr_result_id - index of the parent MrResult
        request_dict - dicts containing info on solutions to parent MR
        """

        self.logger.debug('Database::getMrTrialResult %s' % mr_result_id)

        #find all solutions for this result
        query = "SELECT * FROM mr_trial_results WHERE mr_result_id=%s"
        request_dict = self.make_dicts(query=query,
                                  params=(mr_result_id,))

        return(request_dict)

    ###########################
    # Methods for SAD results #
    ###########################
    def addSadResult(self,dirs,info,settings,results):
        """
        Add data to the sad_results table.

        dirs - dict containing directory information for the agent
               used for work and data_root_dir
        info - dict containing information used by the agent
               used for sample_id and run_id
        settings - dict containing settings from the site
                   importantly this contains the original request
                   multiple uses
        results - dict containing result information from the agent
        """

        self.logger.debug('Database::addSadResult')
        self.logger.debug(dirs)
        self.logger.debug(info)
        self.logger.debug(settings)
        self.logger.debug(results)

        #Catch non-standard entries
        my_repr = os.path.basename(dirs['work'])

        #Check to see if there is a previous result with this process_id
        #Acquire lock
        self.LOCK.acquire()

        try:
            sad_result_id,result_id = self.getTypeResultId(process_id=settings['process_id'])
            self.logger.debug("sad_result_id: %s   result_id: %s" % (str(sad_result_id),str(result_id)))
            if (sad_result_id):
                self.logger.debug("Getting sad result dict")
                sad_result_dict = self.getResultById(sad_result_id, 'sad')
            else:
                self.logger.debug("Creating new result.")
                #make a new entry to then update
                sad_result_id,result_id = self.makeNewResult(rtype='sad',
                                                             process_id=settings['process_id'])
                sad_result_dict = False
        except:
            self.logger.exception("Error in addSadResult result id acquisition")

        #release lock
        self.LOCK.release()
        try:
            #connect to the database
            connection,cursor = self.get_db_connection()

            #Information stored regardless of failure level
            command = '''UPDATE sad_results SET timestamp=NOW(),
                                                result_id=%s,
                                                process_id=%s,
                                                settings_id=%s,
                                                request_id=%s,
                                                source_data_id=%s,
                                                data_root_dir=%s,
                                                work_dir=%s,
                                                repr=%s,
                                                version=version+1,
                                                sad_status=%s'''

            insert_values = [ result_id,
                              settings['process_id'],
                              settings['setting_id'],
                              settings['request']['cloud_request_id'],
                              settings['request']['original_result_id'],
                              dirs['data_root_dir'],
                              dirs['work'],
                              my_repr,
                              results['sad_status']]

            #ShelxC section
            try:
                if (results.has_key('Shelx results')):
                    #If this is an update to a run
                    if (sad_result_dict):
                        shelxc_result_id = self.addShelxcResult(shelx_results=results['Shelx results'],
                                                         sad_result_id=sad_result_id,
                                                         shelxc_result_id=sad_result_dict['shelxc_result_id'])
                    else:
                        shelxc_result_id = self.addShelxcResult(shelx_results=results['Shelx results'],
                                                         sad_result_id=sad_result_id)

                    if (shelxc_result_id):
                        command += ''',
                                                shelxc_result_id=%s'''
                        insert_values += [shelxc_result_id]

            except:
                self.logger.exception('Error in writing shelxc_results section of sad_results table')

            #ShelxD section
            try:
                if (results.has_key('Shelx results')):
                    #If this is an update to a run
                    if (sad_result_dict):
                        shelxd_result_id = self.addShelxdResult(shelx_results    = results['Shelx results'],
                                                                sad_result_id    = sad_result_id,
                                                                shelxd_result_id = sad_result_dict['shelxd_result_id'])
                    else:
                        shelxd_result_id = self.addShelxdResult(shelx_results = results['Shelx results'],
                                                                sad_result_id = sad_result_id)
                    if (shelxd_result_id):
                        command += ''',
                                                shelxd_result_id=%s'''
                        insert_values += [shelxd_result_id,]
                    #Add flag to merge or integrate results table for solved status
                    if (results['Shelx results']['shelx_no_solution'] == 'False'):
                        self.addYesSolved(settings['request']['original_result_id'])


            except:
                self.logger.exception('Error in writing shelxd_results section of sad_results table')

            #ShelxE section
            try:
                if (results.has_key('Shelx results')):
                    #If this is an update to a run
                    if (sad_result_dict):
                        shelxe_result_id = self.addShelxeResult(shelx_results=results['Shelx results'],
                                                         sad_result_id=sad_result_id,
                                                         shelxe_result_id=sad_result_dict['shelxe_result_id'])
                    else:
                        shelxe_result_id = self.addShelxeResult(shelx_results=results['Shelx results'],
                                                         sad_result_id=sad_result_id)

                    if (shelxe_result_id):
                        command += ''',
                                                shelxe_result_id=%s,
                                                shelx_tar=%s'''
                        insert_values += [shelxe_result_id,
                                          results['Shelx results']['shelx_tar']]

            except:
                self.logger.exception('Error in writing shelxe_results section of sad_results table')

            #Autosol section
            try:
                if results.has_key('AutoSol results'):
                    if(results.get('AutoSol results') not in ['None', None, "FAILED"]):
                        #If this is an update to a run
                        if (sad_result_dict):
                            autosol_result_id = self.addAutosolResult(autosol_results=results['AutoSol results'],
                                                                      sad_result_id=sad_result_id,
                                                                      autosol_result_id=sad_result_dict['autosol_result_id'])
                        else:
                            autosol_result_id = self.addAutosolResult(autosol_results=results['AutoSol results'],
                                                                      sad_result_id=sad_result_id)

                        if(autosol_result_id):
                            command += ''',
                                                    autosol_result_id=%s'''

                            insert_values += [autosol_result_id]

            except:
                self.logger.exception('Error in writing Autosol_results section of sad_results table')

            #Cell analysis section
            try:
                if(results.has_key('Cell analysis results')):
                  if(not results['Cell analysis results'] in ('FAILED',None,'None')):
                    self.addCellAnalysisResults(cell_analysis_results=results['Cell analysis results'],
                                                sad_result_id=sad_result_id)
            except:
                self.logger.exception('Error in writing Cell analysis section of sad_results table')

            #FILES
            try:
                tmp_command = ''',
                                                shelx_html=%s,
                                                shelx_plots=%s,
                                                autosol_html=%s,
                                                download_file=%s'''

                tmp_insert_values = [results['Output files']['Shelx summary html'],
                                     results['Output files']['Shelx plots html'],
                                     results['Output files']['Autosol html'],
                                     results['Output files']['Autosol tar']]

                #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                command += tmp_command
                insert_values += tmp_insert_values

            except:
                self.logger.exception('Error in writing files section of sad_result table')

            #finish up the commands
            command += ' WHERE sad_result_id=%s'
            insert_values.append(sad_result_id)

            #deposit the result
            self.logger.debug(command)
            self.logger.debug(insert_values)
            cursor.execute(command,insert_values)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addSadResult')
            self.closeConnection(connection,cursor)
            return(False)

        try:
            self.logger.debug("Entering the results updating section sad_result_id:%d"%sad_result_id)
            #get the result's sad_result dict
            new_sad_result_dict = self.make_dicts('SELECT * FROM sad_results WHERE sad_result_id=%s',(sad_result_id,))[0]
            self.logger.debug(new_sad_result_dict)
            #update the result in results table
            cursor.execute('UPDATE results SET setting_id=%s,process_id=%s,data_root_dir=%s,timestamp=%s WHERE result_id=%s',
                           (new_sad_result_dict['settings_id'],new_sad_result_dict['process_id'],new_sad_result_dict['data_root_dir'],new_sad_result_dict['timestamp'],result_id))
            self.closeConnection(connection,cursor)
            return(new_sad_result_dict)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addSadResult - results updating subsection')
            self.closeConnection(connection,cursor)
            return(False)

    def addShelxcResult(self,shelx_results,sad_result_id,shelxc_result_id=None):
        """
        Add a ShelxC result from sad_results and return the shelxc_result_id
        """

        self.logger.debug('addShelxcResult shelxc_result_id:%s' % str(shelxc_result_id))

        try:
            #connect to the database
            connection,cursor = self.get_db_connection()

            if not (shelxc_result_id):
                cursor.execute("INSERT INTO shelxc_results () VALUES ()")
                shelxc_result_id = cursor.lastrowid

            #regardless of failure level
            command = '''UPDATE shelxc_results SET sad_result_id=%s,
                                                resolutions=%s,
                                                completeness=%s,
                                                dsig=%s,
                                                isig=%s,
                                                data=%s,
                                                timestamp=NOW() WHERE shelxc_result_id=%s'''

            insert_values = [sad_result_id,
                             json.dumps(shelx_results['shelxc_res']).replace(' ',''),
                             json.dumps(shelx_results['shelxc_comp']).replace(' ',''),
                             json.dumps(shelx_results['shelxc_dsig']).replace(' ',''),
                             json.dumps(shelx_results['shelxc_isig']).replace(' ',''),
                             json.dumps(shelx_results['shelxc_data']).replace(' ',''),
                             shelxc_result_id]

            #deposit the result
            self.logger.debug(command)
            self.logger.debug(insert_values)
            cursor.execute(command,insert_values)
            self.closeConnection(connection,cursor)
            return(shelxc_result_id)

        except:
            self.logger.exception('Error in addShelxcResult')
            self.closeConnection(connection,cursor)
            return(0)

    def addShelxdResult(self,shelx_results,sad_result_id,shelxd_result_id=None):
        """
        Add a ShelxD result from sad_results and return the shelxd_result_id
        """
        self.logger.debug('addShelxdResult shelxd_result_id:%s' % str(shelxd_result_id))
        #self.logger.debug(shell_dict)

        try:
            #connect to the database
            connection,cursor = self.get_db_connection()

            if not (shelxd_result_id):
                cursor.execute("INSERT INTO shelxd_results () VALUES ()")
                shelxd_result_id = cursor.lastrowid

            #regardless of failure level
            command = '''UPDATE shelxd_results SET sad_result_id=%d,
                                                best_occ='%s',
                                                trials=%d,
                                                cca=%f,
                                                cca_max=%f,
                                                cca_min=%f,
                                                cca_mean=%f,
                                                cca_stddev=%f,
                                                ccw=%f,
                                                ccw_max=%f,
                                                ccw_min=%f,
                                                ccw_mean=%f,
                                                ccw_stddev=%f,
                                                fom=%f,
                                                fom_max=%f,
                                                fom_min=%f,
                                                fom_mean=%f,
                                                fom_stddev=%f,
                                                timestamp=NOW() WHERE shelxd_result_id=%d'''

            #Get the stats for the three arrays that have been passed in
            cca_stats = self.getArrayStats(in_array=shelx_results['shelxd_cca'],
                                           mode='float')
            ccw_stats = self.getArrayStats(in_array=shelx_results['shelxd_ccw'],
                                           mode='float')
            fom_stats = self.getArrayStats(in_array=shelx_results['shelxd_fom'],
                                           mode='float')

            insert_values = (sad_result_id,
                             json.dumps(shelx_results['shelxd_best_occ']).replace(' ',''),
                             len(shelx_results['shelxd_try']),
                             float(shelx_results['shelxd_best_cc']),
                             cca_stats[0],
                             cca_stats[1],
                             cca_stats[2],
                             cca_stats[3],
                             float(shelx_results['shelxd_best_ccw']),
                             ccw_stats[0],
                             ccw_stats[1],
                             ccw_stats[2],
                             ccw_stats[3],
                             float(shelx_results['shelxd_fom'][int(shelx_results['shelxd_best_try'])-1]),
                             fom_stats[0],
                             fom_stats[1],
                             fom_stats[2],
                             fom_stats[3],
                             shelxd_result_id)

            #deposit the result
            self.logger.debug(command)
            self.logger.debug(insert_values)
            compiled_command = command % insert_values
            self.logger.debug(compiled_command)
            #cursor.execute(command,insert_values)
            cursor.execute(compiled_command)
            self.closeConnection(connection,cursor)
            return(shelxd_result_id)

        except:
            self.logger.exception('Error in addShelxdResult')
            self.closeConnection(connection,cursor)
            return(0)

    def addShelxeResult(self,shelx_results,sad_result_id,shelxe_result_id=None):
        """
        Add a ShelxE result from sad_results and return the shelxe_result_id
        """
        self.logger.debug('addShelxeResult shelxe_result_id:%s' % str(shelxe_result_id))
        #self.logger.debug(shell_dict)

        try:
            #connect to the database
            connection,cursor = self.get_db_connection()

            if not (shelxe_result_id):
                cursor.execute("INSERT INTO shelxe_results () VALUES ()")
                shelxe_result_id = cursor.lastrowid

            #Is there a solution?
            if (shelx_results['shelxe_nosol'] == 'False'):
                solution = 'True'
            elif (shelx_results['shelxe_nosol'] == 'True'):
                solution = 'False'

            #regardless of failure level
            command = '''UPDATE shelxe_results SET sad_result_id=%s,
                                                solution=%s,
                                                resolution=%s,
                                                number_sites=%s,
                                                inverted=%s,
                                                cc_norm=%s,
                                                cc_inv=%s,
                                                contrast_norm=%s,
                                                contrast_inv=%s,
                                                connect_norm=%s,
                                                connect_inv=%s,
                                                mapcc_norm=%s,
                                                mapcc_inv=%s,
                                                timestamp=NOW() WHERE shelxe_result_id=%s'''

            insert_values = [sad_result_id,
                             solution,
                             json.dumps(shelx_results['shelxc_res'][:len(shelx_results['shelxc_res'])]).replace(' ',''),
                             len(shelx_results['shelxe_sites']),
                             shelx_results['shelxe_inv_sites'],
                             shelx_results['shelxe_cc'][0],
                             shelx_results['shelxe_cc'][1],
                             shelx_results['shelxe_contrast'][19], #[(len(shelx_results['shelxe_contrast'])/2)-1],
                             shelx_results['shelxe_contrast'][-1],
                             shelx_results['shelxe_con'][19], #[(len(shelx_results['shelxe_con'])/2)-1],
                             shelx_results['shelxe_con'][-1],
                             shelx_results['shelxe_mapcc'][19], #[(len(shelx_results['shelxe_mapcc'])/2)-1],
                             shelx_results['shelxe_mapcc'][-1],
                             shelxe_result_id]

            #deposit the result
            self.logger.debug(command)
            self.logger.debug(insert_values)
            cursor.execute(command,insert_values)

            #Now add the sites
            if (shelx_results.has_key('shelxe_sites')):
                #delete sites for this shelxe_result_id
                command = "DELETE FROM shelxe_sites WHERE shelxe_result_id=%s"
                cursor.execute(command,(shelxe_result_id,))

                for site in shelx_results['shelxe_sites']:
                    self.addShelxeSite(shelx_site=site,
                                       sad_result_id=sad_result_id,
                                       shelxe_result_id=shelxe_result_id)
            self.closeConnection(connection,cursor)
            return(shelxe_result_id)

        except:
            self.logger.exception('Error in addShelxeResult')
            self.closeConnection(connection,cursor)
            return(0)

    def addShelxeSite(self,shelx_site,sad_result_id,shelxe_result_id):
        """
        Add a ShelxE site from sad_results
        """
        self.logger.debug('addShelxeSite shelxe_result_id:%s' % str(shelxe_result_id))

        #split the site
        my_site = shelx_site.split()

        try:
            #connect to the database
            connection,cursor = self.get_db_connection()

            command = '''INSERT INTO shelxe_sites (shelxe_result_id,
                                                   sad_result_id,
                                                   site_number,
                                                   x,
                                                   y,
                                                   z,
                                                   occxz,
                                                   density) VALUES (%s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s,
                                                                    %s)'''

            insert_values = [shelxe_result_id,
                             sad_result_id,
                             my_site[0],
                             my_site[1],
                             my_site[2],
                             my_site[3],
                             my_site[4],
                             my_site[5]]

            #deposit the result
            self.logger.debug(command)
            self.logger.debug(insert_values)
            cursor.execute(command,insert_values)
            self.closeConnection(connection,cursor)
            return(True)

        except:
            self.logger.exception('Error in addShelxeResult')
            self.closeConnection(connection,cursor)
            return(False)

    def addAutosolResult(self,autosol_results,sad_result_id,autosol_result_id=None):
        """
        Add an Autosol result from sad_results and return the autosol_result_id
        """

        self.logger.debug('addAutosolResult autosol_result_id:%s' % str(autosol_result_id))

        try:
            #connect to the database
            connection,cursor = self.get_db_connection()

            if not (autosol_result_id):
                cursor.execute("INSERT INTO autosol_results () VALUES ()")
                autosol_result_id = cursor.lastrowid

            #regardless of failure level
            command = '''UPDATE autosol_results SET sad_result_id=%s,
                                                directory=%s,
                                                spacegroup=%s,
                                                wavelength=%s,
                                                ha_type=%s,
                                                fprime=%s,
                                                f2prime=%s,
                                                sites_start=%s,
                                                sites_refined=%s,
                                                res_built=%s,
                                                side_built=%s,
                                                number_chains=%s,
                                                model_map_cc=%s,
                                                fom=%s,
                                                den_mod_r=%s,
                                                bayes_cc=%s,
                                                r=%s,
                                                rfree=%s,
                                                timestamp=NOW() WHERE autosol_result_id=%s'''

            insert_values = [sad_result_id,
                             autosol_results['directory'],
                             autosol_results['sg'],
                             autosol_results['wavelength'],
                             autosol_results['ha_type'],
                             autosol_results["f'"],
                             autosol_results['f"'],
                             autosol_results['sites_start'],
                             autosol_results['sites_refined'],
                             autosol_results['res_built'],
                             autosol_results['side_built'],
                             autosol_results['num_chains'],
                             autosol_results['model-map_cc'],
                             autosol_results['fom'],
                             '0',#autosol_results['den_mod_r'],
                             autosol_results['bayes-cc'],
                             autosol_results['r/rfree'].split('/')[0],
                             autosol_results['r/rfree'].split('/')[1],
                             autosol_result_id]

            #deposit the result
            self.logger.debug(command)
            self.logger.debug(insert_values)
            cursor.execute(command,insert_values)
            self.closeConnection(connection,cursor)
            return(autosol_result_id)

        except:
            self.logger.exception('Error in addAutosolResult')
            self.closeConnection(connection,cursor)
            return(0)


    ###########################
    # Methods for MAD results #
    ###########################
    def addMadResult(self,dirs,info,settings,results):
        """
        Add data to the sad_results table.

        dirs - dict containing directory information for the agent
               used for work and data_root_dir
        info - dict containing information used by the agent
               used for sample_id and run_id
        settings - dict containing settings from the site
                   importantly this contains the original request
                   multiple uses
        results - dict containing result information from the agent
        """

        self.logger.debug('Database::addMadResult')
        self.logger.debug(dirs)
        self.logger.debug(info)
        self.logger.debug(settings)
        self.logger.debug(results)

        #Catch non-standard entries
        my_repr = os.path.basename(dirs['work'])

        #Check to see if there is a previous result with this process_id
        #Acquire lock
        self.LOCK.acquire()

        try:
            mad_result_id,result_id = self.getTypeResultId(process_id=settings['process_id'])
            self.logger.debug("mad_result_id: %s   result_id: %s" % (str(mad_result_id),str(result_id)))
            if (mad_result_id):
                self.logger.debug("Getting mad result dict")
                mad_result_dict = self.getResultById(mad_result_id, 'mad')
            else:
                self.logger.debug("Creating new result.")
                #make a new entry to then update
                mad_result_id,result_id = self.makeNewResult(rtype='mad',
                                                             process_id=settings['process_id'])
                mad_result_dict = False
        except:
            self.logger.exception("Error in addMadResult result id acquisition")

        #release lock
        self.LOCK.release()

        try:
            #connect to the database
            connection,cursor = self.get_db_connection()

            #Information stored regardless of failure level
            command = '''UPDATE mad_results SET timestamp=NOW(),
                                                result_id=%s,
                                                process_id=%s,
                                                settings_id=%s,
                                                request_id=%s,
                                                source_data_id=%s,
                                                data_root_dir=%s,
                                                work_dir=%s,
                                                repr=%s,
                                                version=version+1,
                                                mad_status=%s'''

            insert_values = [ result_id,
                              settings['process_id'],
                              settings['setting_id'],
                              settings['request']['cloud_request_id'],
                              settings['request']['original_result_id'],
                              dirs['data_root_dir'],
                              dirs['work'],
                              my_repr,
                              results['sad_status']]                            # sic

            #ShelxC section
            try:
                if (results.has_key('Shelx results')):
                    #If this is an update to a run
                    if (mad_result_dict):
                        shelxc_result_id = self.addShelxcResult(shelx_results=results['Shelx results'],
                                                                sad_result_id=mad_result_id,
                                                                shelxc_result_id=mad_result_dict['shelxc_result_id'])
                    else:
                        shelxc_result_id = self.addShelxcResult(shelx_results=results['Shelx results'],
                                                                sad_result_id=mad_result_id)

                    if (shelxc_result_id):
                        command += ''',
                                                shelxc_result_id=%s'''
                        insert_values += [shelxc_result_id]

            except:
                self.logger.exception('Error in writing shelxc_results section of mad_results table')

            #ShelxD section
            try:
                if (results.has_key('Shelx results')):
                    #If this is an update to a run
                    if (mad_result_dict):
                        shelxd_result_id = self.addShelxdResult(shelx_results    = results['Shelx results'],
                                                                sad_result_id    = mad_result_id,
                                                                shelxd_result_id = mad_result_dict['shelxd_result_id'])
                    else:
                        shelxd_result_id = self.addShelxdResult(shelx_results = results['Shelx results'],
                                                                sad_result_id = mad_result_id)
                    if (shelxd_result_id):
                        command += ''',
                                                shelxd_result_id=%s'''
                        insert_values += [shelxd_result_id,]
                    #Add flag to merge or integrate results table for solved status
                    if (results['Shelx results']['shelx_no_solution'] == 'False'):
                        self.addYesSolved(settings['request']['original_result_id'])


            except:
                self.logger.exception('Error in writing shelxd_results section of mad_results table')

            #ShelxE section
            try:
                if (results.has_key('Shelx results')):
                    #If this is an update to a run
                    if (mad_result_dict):
                        shelxe_result_id = self.addShelxeResult(shelx_results=results['Shelx results'],
                                                                sad_result_id=mad_result_id,
                                                                shelxe_result_id=mad_result_dict['shelxe_result_id'])
                    else:
                        shelxe_result_id = self.addShelxeResult(shelx_results=results['Shelx results'],
                                                                sad_result_id=mad_result_id)

                    if (shelxe_result_id):
                        command += ''',
                                                shelxe_result_id=%s,
                                                shelx_tar=%s'''
                        insert_values += [shelxe_result_id,
                                          results['Shelx results']['shelx_tar']]

            except:
                self.logger.exception('Error in writing shelxe_results section of mad_results table')

            #Autosol section
            try:
                if results.has_key('AutoSol results'):
                    self.logger.debug(results.get('AutoSol results'))
                    if(results.get('AutoSol results') not in ['None', None, "FAILED"]):
                        #If this is an update to a run
                        if (mad_result_dict):
                            autosol_result_id = self.addAutosolResult(autosol_results=results['AutoSol results'],
                                                                      sad_result_id=mad_result_id,
                                                                      autosol_result_id=mad_result_dict['autosol_result_id'])
                        else:
                            autosol_result_id = self.addAutosolResult(autosol_results=results['AutoSol results'],
                                                                      sad_result_id=mad_result_id)

                        if(autosol_result_id):
                            command += ''',
                                                    autosol_result_id=%s'''

                            insert_values += [autosol_result_id]

            except:
                self.logger.exception('Error in writing Autosol_results section of mad_results table')

            #Cell analysis section
            try:
                if(results.has_key('Cell analysis results')):
                  if(not results['Cell analysis results'] in ('FAILED',None,'None')):
                    self.addCellAnalysisResults(cell_analysis_results=results['Cell analysis results'],
                                                sad_result_id=mad_result_id)
            except:
                self.logger.exception('Error in writing Cell analysis section of mad_results table')

            #FILES
            try:
                tmp_command = ''',
                                                shelx_html=%s,
                                                shelx_plots=%s,
                                                autosol_html=%s,
                                                download_file=%s'''

                tmp_insert_values = [results['Output files']['Shelx summary html'],
                                     results['Output files']['Shelx plots html'],
                                     results['Output files']['Autosol html'],
                                     results['Output files']['Autosol tar']]

                #now add the tmps to the more permenant variables - this should avoid some funkiness on wierd failures
                command += tmp_command
                insert_values += tmp_insert_values

            except:
                self.logger.exception('Error in writing files section of mad_result table')

            #finish up the commands
            command += ' WHERE mad_result_id=%s'
            insert_values.append(mad_result_id)

            #deposit the result
            self.logger.debug(command)
            self.logger.debug(insert_values)
            cursor.execute(command,insert_values)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addMadResult')
            self.closeConnection(connection,cursor)
            return(False)

        try:
            self.logger.debug("Entering the results updating section sad_result_id:%d" % mad_result_id)
            #get the result's sad_result dict
            new_mad_result_dict = self.make_dicts('SELECT * FROM mad_results WHERE mad_result_id=%s',(mad_result_id,))[0]
            self.logger.debug(new_mad_result_dict)
            #update the result in results table
            cursor.execute('UPDATE results SET setting_id=%s,process_id=%s,data_root_dir=%s,timestamp=%s WHERE result_id=%s',
                           (new_mad_result_dict['settings_id'],new_mad_result_dict['process_id'],new_mad_result_dict['data_root_dir'],new_mad_result_dict['timestamp'],result_id))
            self.closeConnection(connection,cursor)
            return(new_mad_result_dict)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addMadResult - results updating subsection')
            self.closeConnection(connection,cursor)
            return(False)



    def addCellAnalysisResults(self,cell_analysis_results,sad_result_id=False,result_id=False):
        """
        Add the Cell Analysis Results from sad_results or stats_results and return the cell_analysis_id.
        """
        self.logger.debug('addCellAnalysisResults result_id:%s  result_id:%s' % (str(sad_result_id),str(result_id)))

        try:
            #connect to the database
            connection,cursor = self.get_db_connection()

            for pdb,cell_analysis_result in cell_analysis_results.iteritems():

                if (cell_analysis_result['AutoMR results']['AutoMR nosol'] == 'False'):
                    command = "INSERT INTO cell_analysis_results ( "
                    id = 0
                    if sad_result_id:
                        command += "sad_result_id, "
                        id = sad_result_id
                    elif result_id:
                        command += "result_id, "
                        id = result_id
                    command += '''                                   pdb_id,
                                                                     name,
                                                                     automr_sg,
                                                                     automr_rfz,
                                                                     automr_tfz,
                                                                     automr_gain,
                                                                     automr_tar,
                                                                     automr_adf,
                                                                     automr_peaks ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''

                    insert_values = [id,
                                     pdb,
                                     cell_analysis_result['Name'][0],
                                     cell_analysis_result['AutoMR results']['AutoMR sg'],
                                     cell_analysis_result['AutoMR results']['AutoMR rfz'],
                                     cell_analysis_result['AutoMR results']['AutoMR tfz'],
                                     cell_analysis_result['AutoMR results']['AutoMR gain'],
                                     cell_analysis_result['AutoMR results']['AutoMR tar'],
                                     cell_analysis_result['AutoMR results']['AutoMR adf'],
                                     cell_analysis_result['AutoMR results']['AutoMR peak']]

                    #add flag to solved column in either integrate_results or merge_results
                    self.addYesSolved(result_id,sad_result_id)

                elif (cell_analysis_result['AutoMR results']['AutoMR nosol'] == 'True'):
                    command = '''INSERT INTO cell_analysis_results ( sad_result_id,
                                                                     pdb_id,
                                                                     name ) VALUES (%s,%s,%s)'''
                    insert_values = [sad_result_id,
                                     pdb,
                                     cell_analysis_result['Name'][0]]

                #deposit the result
                self.logger.debug(command)
                self.logger.debug(insert_values)
                cursor.execute(command,insert_values)

                #add flag to solved column in either integrate_results or merge_results

            self.closeConnection(connection,cursor)
            return(True)

        except:
            self.logger.exception('Error in addCellAnalysisResults')
            self.closeConnection(connection,cursor)
            return(False)

    def addStatsResults(self,info,results):
        """
        Add the Stats Results return the stats_id
        """
        self.logger.debug('addStatsResults')

        #Check to see if there is a previous result with this process_id
        tmp,result_id = self.getTypeResultId(process_id=info['process_id'])
        self.logger.debug("result_id: %s" % (str(result_id),))

        if result_id:

            #Cell analysis section
            try:
                if(results.has_key('Cell analysis results')):
                  if(not results['Cell analysis results'] in ('FAILED',None,'None')):
                    self.addCellAnalysisResults(cell_analysis_results=results['Cell analysis results'],
                                                result_id=result_id)
            except:
                self.logger.exception('Error in writing Cell analysis section of cell_analysis_results table')

            #The stats_results section
            try:
                #connect to the database
                connection,cursor = self.get_db_connection()

                command = '''INSERT INTO stats_results (result_id,
                                                        process_id,
                                                        cell_sum,
                                                        xtriage_sum,
                                                        xtriage_plots,
                                                        molrep_sum,
                                                        molrep_img,
                                                        precession_sum,
                                                        precession_img0,
                                                        precession_img1,
                                                        precession_img2) VALUES (%s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s,
                                                                                 %s)'''
                insert_values = (result_id,
                                 info["process_id"],
                                 results["Cell summary html"],
                                 results["Xtriage summary html"],
                                 results["Xtriage plots html"],
                                 results["Molrep summary html"],
                                 results["Molrep results"]["Molrep jpg"],
                                 results["LabelitPP summary html"],
                                 results["LabelitPP results"]["HK0 jpg"],
                                 results["LabelitPP results"]["H0L jpg"],
                                 results["LabelitPP results"]["0KL jpg"])

                #deposit the result
                self.logger.debug(command)
                self.logger.debug(insert_values)
                cursor.execute(command,insert_values)
                stats_result_id = cursor.lastrowid

                """
                #Now update the table with the result_id
                command2 = "UPDATE stats_results,results SET stats_results.result_id = results.result_id WHERE results.process_id = %s"
                self.logger.debug(command2%str(info["process_id"]))
                cursor.execute(command2,(info["process_id"],))
                """

                #get the result's stats_result dict
                new_stats_result_dict = self.make_dicts('SELECT * FROM stats_results WHERE stats_result_id=%s',(stats_result_id,))[0]
                self.closeConnection(connection,cursor)
                return(new_stats_result_dict)

            except:
                self.logger.exception('Error in addStatsResults')
                self.closeConnection(connection,cursor)
                return(False)
        else:
            self.logger.debug("ERROR in addStatsResults - no result_id!!")
            self.closeConnection(connection,cursor)
            return(False)

    def getArrayStats(self,in_array,mode='float'):
        """
        return the max,min,mean and std_dev of an input array
        """
        self.logger.debug('Database::getArrayStats')

        if (mode == 'float'):
            narray = numpy.array(in_array,dtype=float)

        try:
            return(narray.max(),narray.min(),narray.mean(),narray.std())
        except:
            return(0,0,0,0)

    def addOrphanResult(self,type,root,id,date):
        """
        Add the orphan result - a result with no trip assigned - to the orphan_results table
            type = single,pair,run
            root = data_root_dir
            id   = the id of the entry in its corresponding result table
        """
        self.logger.debug('Database::addOrphanResult')
        self.logger.debug(type)
        self.logger.debug(root)
        self.logger.debug(id)
        self.logger.debug(date)

        #connect to the database
        connection,cursor = self.get_db_connection()

        try:
            #deposit the result
            cursor.execute("""INSERT INTO orphan_results ( type,
                                                           data_root_dir,
                                                           result_id,
                                                           date) VALUES ( %s,
                                                                          %s,
                                                                          %s,
                                                                          %s )""", ( type,
                                                                                     root,
                                                                                     id,
                                                                                     date ))
            self.closeConnection(connection,cursor)
            return(True)

        except:
            self.logger.exception('ERROR : unknown exception in Database::addOrphanResult')
            self.closeConnection(connection,cursor)
            return(False)

    def getTypeResultId(self,process_id):
        """
        Retrieve a type_result_id and result_id given a process_id

        process_id - a unique index from rapd_data.processes
        """

        self.logger.debug('Database::getTypeResultId  process_id:%d' % process_id)

        query = "SELECT result_id,id FROM results WHERE process_id=%s"
        my_dict = self.make_dicts(query, (process_id,))

        if (len(my_dict)>0):
            return(my_dict[0]['id'],my_dict[0]['result_id'])
        else:
            return(False,False)

    def getTypeByResultId(self,result_id,full=False):
        """
        Retrieve a type given a result_id

        result_id - a unique index from rapd_data.results
        """

        self.logger.debug('Database::getTypeByResultId  result_id:%d' % result_id)

        query = "SELECT * FROM results WHERE result_id=%s"
        my_dict = self.make_dicts(query, (result_id,), "DATA")

        if (len(my_dict)>0):
            if full:
                return(my_dict[0])
            else:
                return(my_dict[0]['type'])
        else:
            return(False)


    def getResultById(self,id,type=None):
        """
        Retrieve a dict for a result given a type and id number
        """
        self.logger.debug('Database::getResultById id:%d type:%s' % (id,type))

        specials_dict = False
        #construct query and then make launch
        if (type == "integrate"):
            query = "SELECT integrate_results.*, runs.image_prefix, runs.run_number, runs.distance FROM integrate_results JOIN runs ON integrate_results.run_id=runs.run_id  WHERE integrate_result_id=%s"
        else:
            query = "SELECT * FROM "+type+"_results WHERE "+type+"_result_id=%s"
        #now query the database
        my_dict = self.make_dicts(query,(id,))[0]

        if (type == "integrate"):
            specials_dict = self.getBeamcenterFromRunId(my_dict['run_id'])
            if (specials_dict) :
                specials_dict["wavelength"] = self.getWavelengthFromRunId(my_dict["run_id"])
                self.logger.debug(str(specials_dict))
            else:
                pass

        if specials_dict:
            my_dict.update(specials_dict)

        #fix the timestamps for json transport
        my_dict['timestamp'] = my_dict['timestamp'].isoformat()
        if my_dict.has_key('proc_time'):
            my_dict['proc_time'] = None
        if my_dict.has_key('date'):
            try:
                my_dict['date'] = my_dict['date'].isoformat()
            except AttributeError:
                my_dict['date'] = None
        if my_dict.has_key('date1'):
            try:
                my_dict['date1'] = my_dict['date1'].isoformat()
            except AttributeError:
                my_dict['date1'] = None
        if my_dict.has_key('date2'):
            try:
                my_dict['date2'] = my_dict['date2'].isoformat()
            except AttributeError:
                my_dict['date2'] = None

        #return
        return(my_dict)

    def getResultByWorkDir(self,work_dir,type):
        """
        Retrieve a dict for a result given the work_dir and type
        """
        self.logger.debug('Database::getResultByWorkDir %s' % work_dir)

        query    = 'SELECT * FROM '+type+'_results WHERE work_dir=%s'
        my_dicts = self.make_dicts(query, (work_dir,))

        if (len(my_dicts) > 0):
            return(my_dicts[0])
        else:
            return(False)

    def getResultByRepr(self,repr,type):
        """
        Retrieve a dict for a result given the repr and type
        """
        self.logger.debug('Database::getResultByRepr %s %s' %(repr,type))

        query =  'SELECT * FROM '+type+'_results WHERE repr=%s'
        my_dicts =  self.make_dicts(query, (repr,))

        if (len(my_dicts) > 0):
            return(my_dicts)
        else:
            return(False)

    def getResultsByDataRootDir(self,data_root_dir,type):
        """
        Retrieve a dict for a result given the data_root_dir and type
        """
        self.logger.debug('Database::getResultsByDataRootDir %s %s' % (data_root_dir,type))

        query    = 'SELECT * FROM '+type+'_results WHERE data_root_dir=%s'
        my_dicts = self.make_dicts(query, (data_root_dir,))

        if (len(my_dicts) > 0):
            return(my_dicts)
        else:
            return(False)

    def getResultsByDate(self,start_date,end_date,type):
        """
        Retrieve a dict for all results given a date range and type
        """
        self.logger.debug('Database::getResultsByDates %s %s %s' % (start_date,end_date,type))

        query    = 'SELECT * FROM '+type+'_results WHERE timestamp>%s AND timestamp<%s'
        my_dicts = self.make_dicts(query, (start_date,end_date))

        if (len(my_dicts) > 0):
            return(my_dicts)
        else:
            return(False)

    def getResultsByFullname(self,fullname,type="single"):
        """
        Retrieve results for an image by fullname
        """
        self.logger.debug('Database::getResultsByFullname %s %s' % (fullname,type))
        if (type == "single"):
            query = "SELECT r.* FROM "+type+"_results AS r JOIN images AS i ON (r.image_id = i.image_id) WHERE i.fullname=%s"

        if (type == "strategy"):
            query = "SELECT s.*,r.best_norm_atten FROM single_results AS r JOIN images AS i ON (r.image_id = i.image_id) JOIN strategy_wedges AS s ON (r.single_result_id = s.id) WHERE i.fullname=%s AND s.strategy_type='normal'"

        my_dicts = self.make_dicts(query, (fullname,))

        if (len(my_dicts) > 0):
            dict = my_dicts[-1]
            dict["basename"] = os.path.basename(fullname)
            for k,v in dict.iteritems():
                if (not v):
                    dict[k] = 0
            return(dict)
        else:
            return(False)

    def getWavelengthFromRunId(self,run_id):
        """
        Retrieve a wavelength value given a run_id
        This is used when setting up the SAD runs
        """
        self.logger.debug('Database::getWavelengthFromRunId run_id=%d' % (run_id))

        #connect to the database
        connection,cursor = self.get_db_connection()

        try:
            query = "SELECT wavelength FROM images WHERE run_id=%s LIMIT 1"
            cursor.execute(query,(run_id,))
            wavelength = cursor.fetchone()[0]
        except:
            self.logger.exception('Error in getWavelengthFromRunId')
            wavelength = False

        print "1"
        self.closeConnection(connection,cursor)
        print "2"

        return(wavelength)

    def getBeamcenterFromRunId(self,run_id):
        """
        Retrieve beamcenter values given a run_id
        """
        self.logger.debug('Database::getBeamcenterFromRunId run_id=%d' % (run_id))

        try:
            query = "SELECT beam_center_x,beam_center_y,calc_beam_center_x,calc_beam_center_y FROM images WHERE run_id=%s LIMIT 1"
            my_dict = self.make_dicts(query,(run_id,))[0]
        except:
            self.logger.exception('Error in getBeamcenterFromRunId')
            my_dict = False

        return(my_dict)

    def updateIntegrateResults(self,status,result_id,files):
        """
        Update the integrate_results table for a given id. The status is True/False for Success/Failure and
        the files are xia_log,xscale_log,scala_log,unmerged_scale_file,sca_file,mtz_file
        """
        self.logger.debug('Database::updateIntegrateResults %s' % status)

        #connect to the database
        connection,cursor = self.get_db_connection()
        try:
            if status == True:
                query = '''UPDATE integrate_results SET integrate_status  = %s,
                                                        xia_log           = %s,
                                                        xscale_log        = %s,
                                                        scala_log         = %s,
                                                        unmerged_sca_file = %s,
                                                        sca_file          = %s,
                                                        mtz_file          = %s WHERE integrate_result_id=%s'''
                self.logger.debug(query,('SUCCESS',files[0],files[1],files[2],files[3],files[4],files[5],result_id))
                cursor.execute(query,('SUCCESS',files[0],files[1],files[2],files[3],files[4],files[5],result_id))
            else:
                query = "UPDATE integrate_results SET integrate_status=%s, xia_log=%s WHERE integrate_result_id=%s"
                self.logger.debug(query,('FAILED',files,result_id))
                cursor.execute(query,('FAILED',files,result_id))
        except:
            pass
        self.closeConnection(connection,cursor)

    def updateIntegrateDatafiles(self,result_id,files):
        """
        Update the integrate_results table for a given id.
        the files are unmerged_scale_file,sca_file,mtz_file
        """
        self.logger.debug('Database::updateIntegrateDatafiles %s %s %s' % (files[0],files[1],files[2]))

        #connect to the database
        connection,cursor = self.get_db_connection()
        try:
            query = '''UPDATE integrate_results SET unmerged_sca_file = %s,
                                                    sca_file          = %s,
                                                    mtz_file          = %s WHERE integrate_result_id=%s'''
            self.logger.debug(query,(files[0],files[1],files[2],result_id))
            cursor.execute(query,(files[0],files[1],files[2],result_id))
        except:
            pass
        self.closeConnection(connection,cursor)

    def removeResult(self,result_id,type):
        """
        Given a passed-in result_id and type, remove from results and the specific result-type table as well
        """
        self.logger.debug('Database::removeResult %d, %s' % (result_id,type))

        #connect to the database
        connection,cursor = self.get_db_connection()

        try:
            #delete from type-specific table
            query = "DELETE FROM "+type+"_results WHERE "+type+"_result_id=%s"
            #print query % result_id
            cursor.execute(query,(result_id,))
            #delete from results table
            query = "DELETE FROM results WHERE id=%s AND type=%s"
            cursor.execute(query,(result_id,type))
        except:
            self.logger.exception('Error in removeResult result_id %d %s' % (result_id,type))
        self.closeConnection(connection,cursor)


    ##################################################################################################################
    # Functions for trips                                                                                            #
    ##################################################################################################################
    def updateTrip(self,trip_id,date):
        """
        Update the trip with date information passed in
        """
        self.logger.debug('Database::updateTrip  trip_id: %d  date: %s' % (trip_id,date))

        #connect
        connection,cursor = self.connect_to_user()

        try:
            cursor.execute('UPDATE trips SET trip_start=%s  WHERE trip_id=%s AND (trip_start  IS NULL OR trip_start>%s)',(date,trip_id,date))
            cursor.execute('UPDATE trips SET trip_finish=%s WHERE trip_id=%s AND (trip_finish IS NULL OR trip_finish<%s)',(date,trip_id,date))
        except:
            self.logger.exception('Error in updateTrip')
        self.closeConnection(connection,cursor)

    def getTrips(self,data_root_dir=False,result_id=False):
        """
        Retrive row(s) from the trips directory.

        Use either data_root_dir or result_id to find trips
        Returns a list of trips details in dicts, False if no matching trips
        """

        self.logger.debug('Database::getTrips dir:%s result_id:%s' % (data_root_dir,str(result_id)))

        #query the database
        try:
            #Finding a trip based on data_root_dir
            if (data_root_dir):
                query = 'SELECT * FROM trips WHERE data_root_dir=%s'
                data = data_root_dir
            #find a trip based on result_id
            elif (result_id):
                query = "SELECT * FROM rapd_users.trips JOIN rapd_data.results ON (rapd_users.trips.data_root_dir = rapd_data.results.data_root_dir) WHERE rapd_data.results.result_id=%s"
                data = result_id
            #query the database
            self.logger.debug(query%data)
            trip_dict = self.make_dicts(query,(data,),'USERS')
        except:
            self.logger.exception('Error in getTrips')
            trip_dict = False

        return(trip_dict)

    def getTripsByUser(self,username):
        """
        Determine if the given username has any assigned trips
        Returns a list of trips details in dicts, False if no matching trips
        """
        self.logger.debug('Database::getTripsByUser')

        #query the database
        try:
            query1 = 'SELECT * FROM trips WHERE username=%s'
            trip_dict = self.make_dicts(query1,(username,),'USERS')
        except:
            self.logger.exception('Error in getTripsByUser')
            trip_dict = False

        return(trip_dict)



    ############################################################################
    # Functions for runs                                                       #
    ############################################################################
    def add_run(self, site_tag, run_data):
        """
        Add a new run to the MySQL database

        Keyword arguments
        run_data -- dict containing run information
        site_tag -- unique identifier for the run origin site
        """
        self.logger.debug("Database.add_run %s %s", site_tag, run_data)

        try:
            # Connect
            connection, cursor = self.get_db_connection()

            # Save into database
            self.logger.debug("Adding run from into database directory:%s image_prefix:%s" % (run["directory"], run["prefix"]))
            cursor.execute("""INSERT INTO runs (anomalous,
                                                directory,
                                                distance,
                                                energy,
                                                image_prefix,
                                                kappa,
                                                number_images,
                                                omega,
                                                osc_axis,
                                                osc_start,
                                                osc_width,
                                                phi,
                                                run_number,
                                                site_tag
                                                start_image_number,
                                                time,
                                                transmission,
                                                two_theta) VALUES (%s,
                                                                   %s,
                                                                   %s,
                                                                   %s,
                                                                   %s,
                                                                   %s,
                                                                   %s,
                                                                   %s,
                                                                   %s,
                                                                   %s,
                                                                   %s,
                                                                   %s,
                                                                   %s,
                                                                   %s,
                                                                   %s,
                                                                   %s,
                                                                   %s,
                                                                   %s)""",
                                             (run_data.get("anomalous", None),
                                              run_data.get("directory", None),
                                              run_data.get("distance", None),
                                              run_data.get("energy", None),
                                              run_data.get("image_prefix", None),
                                              run_data.get("kappa", None),
                                              run_data.get("number_images", None),
                                              run_data.get("omega", None),
                                              run_data.get("osc_axis", None),
                                              run_data.get("osc_start", None),
                                              run_data.get("osc_width", None),
                                              run_data.get("phi", None),
                                              run_data.get("run_number", None),
                                              site_tag,
                                              run_data.get("start_image_number", 0),
                                              run_data.get("time", 0.0),
                                              run_data.get("transmission", 0.0),
                                              run_data.get("two_theta", 0.0)))
            run_id = cursor.lastrowid
            self.closeConnection(connection,cursor)
            return(run_id)

        except pymysql.IntegrityError, (errno, strerror):
            if errno == 1062:
                self.logger.debug("Run is already in the database")
                self.closeConnection(connection, cursor)

                # Get the run_id and return it
                return self.getRunIdByInfo(run_data=run)
            else:
                self.logger.exception("ERROR : unknown IntegrityError exception in rapd_mysql_adapter.add_run")
                return False

        except:
            self.logger.exception("ERROR : unknown exception in rapd_mysql_adapter.add_run")
            self.closeConnection(connection, cursor)
            return False

    def get_run_data(self,
                     site_tag=None,
                     run_data=None,
                     minutes=0,
                     order="descending"):
        """
        Return information for runs that fit the data within the last minutes
        window. If minutes=0, no time limit.

        Match is performed on the directory, prefix, starting image number and
        total number of images.

        Keyword arguments
        site_tag -- string describing site (default None)
        run_data -- dict of run information (default None)
        minutes -- time window to look back into the data (default 0)
        order -- the order in which to sort the results, must be None, descending
                 or ascending (default descending)
        """

        self.logger.debug("site_tag:%s run_data:%s minutes:%d", site_tag, run_data, minutes)

        # Order
        if order == "descending":
            order_param = "DESC"
        elif order == "ascending":
            order_param = "ASC"
        else:
            raise Exception("get_run_data order argument must be None, ascending, or descending")

        # No limit on the results
        if minutes == 0:
            query = "SELECT * FROM runs WHERE site_tag=%s AND directory=%s AND image_prefix=%s AND start_image_number=%s AND number_images=%s ORDER BY timestamp %s"
            params = (site_tag,
                      run_data.get("directory", None),
                      run_data.get("prefix", None),
                      run_data.get("start_image_number", None),
                      run_data.get("number_images", None),
                      order_param)

        # Limit to a time window
        else:
            # query = "SELECT * FROM runs WHERE site_tag=%s AND directory=%s AND image_prefix=%s AND run_number=%s AND start_image_number=%s AND number_images=%s AND timestamp > NOW()-INTERVAL %s MINUTE ORDER BY timestamp %s"
            # params = (site_tag,
            #           run_data.get("directory", None),
            #           run_data.get("image_prefix", None),
            #           run_data.get("run_number", None),
            #           run_data.get("start_image_number", None),
            #           run_data.get("number_images", None),
            #           minutes,
            #           order_param)
            query = "SELECT * FROM runs WHERE site_tag=%s AND directory=%s "#AND image_prefix=%s AND run_number=%s AND start_image_number=%s AND number_images=%s AND timestamp > NOW()-INTERVAL %s MINUTE ORDER BY timestamp %s"
            params = ("1", "2")
            # params = (site_tag,
            #           run_data.get("directory", None))
                    #   run_data.get("image_prefix", None))
                    #   run_data.get("run_number", None),
                    #   run_data.get("start_image_number", None),
                    #   run_data.get("number_images", None),
                    #   minutes,
                    #   order_param)

        self.logger.debug(query)
        self.logger.debug(query, params)
        self.logger.debug(params)

        return {}

        # Query the database
        result_dicts = self.make_dicts(query=query,
                                       params=params)

        # If no return, return a False
        if len(result_dicts) == 0:
            return False
        else:
            return result_dicts

    def getRunIdByInfo(self, run_data):
        """
        Return a run_id from data in a dict
        """
        self.logger.debug('getRunIdByInfo run_data:%s' % str(run_data))

        if (not run_data.has_key("run_number")):
            run_data["run_number"] = run_data['image_prefix'].split('_')[-1]

        query = "SELECT * FROM runs WHERE directory=%s AND run_number=%s AND image_prefix=%s AND start=%s AND total=%s"
        self.logger.debug("SELECT * FROM runs WHERE directory=%s AND run_number=%s AND image_prefix=%s AND start=%s AND total=%s" % (run_data['directory'],run_data['run_number'],run_data['prefix'],run_data['start'],run_data['total']))
        my_dicts = self.make_dicts(query,(run_data['directory'],run_data['run_number'],run_data['prefix'],run_data['start'],run_data['total']))
        if (len(my_dicts) > 0):
            return(my_dicts[0]['run_id'])
        else:
            return(False)

    def inRun(self,image_id):
        """
        Determine is an image is in a run.
        Return the run_id if the image is in run, False if not
        """
        self.logger.debug('Database::inRun %d' % image_id)

        #get a dict from images table for this image
        query1 = 'select fullname,directory,image_prefix,run_number,image_number,run_id from images where image_id=%s'
        image_dict = self.make_dicts(query1,(image_id,))

        if image_dict:
            image_dict = image_dict[0]

            self.logger.debug('Data retrieved from the mysql database for matching images:')
            self.logger.debug(image_dict)

            #connect to mysql server
            connection,cursor = self.get_db_connection()

            #now search the runs table for a compatible run
            query2 = 'select run_id,total from runs where directory=%s AND image_prefix=%s AND run_number=%s AND %s>=start AND %s<= start+total'
            params = (image_dict['directory'],image_dict['image_prefix'],image_dict['run_number'],image_dict['image_number'],image_dict['image_number'])
            self.logger.debug(query2%params)
            cursor.execute(query2,params)

            try:
                run_id,total = cursor.fetchone()
            except:
                run_id = False
                total = False

            if run_id:
                #self.logger.debug('%s is in a run\n' % image_dict['fullname'])
                #mark the image with the run_id
                cursor.execute("UPDATE images SET run_id=%s WHERE image_id=%s",(run_id,image_id))
                self.closeConnection(connection, cursor)
                #return True
                return(run_id,total)
            else:
                self.logger.debug('%s is NOT in a run\n' % image_dict['fullname'])
                self.closeConnection(connection,cursor)
                return(False,False)
        else:
            return(False,False)

    def getRunPosition(self,image_number,run_id):
        """
        Return the position of an image in a run, starting with 1
        """
        self.logger.debug('Database::getRunPosition  image_number: %d  run_id: %d' % (image_number,run_id))

        try:
            #connect
            connection,cursor = self.get_db_connection()

            #get the run information
            query1 = 'select start FROM runs WHERE run_id=%s'
            cursor.execute(query1,(run_id))
            sql_ret = cursor.fetchone()

            if sql_ret:
                start = sql_ret[0]
                position = int(image_number) - start + 1
                self.closeConnection(connection,cursor)
                return(position)
        except:
            self.logger.exception('Error in Database::getRunPosition')
            self.closeConnection(connection,cursor)
            return(0)


    def inRunPosition(self,image_number,run_id,position=1):
        """
        Determine if an image is in a specific position in a run
        First in run is the default
        """
        self.logger.debug('Database::inRunPosition  image_number: %d  run_id: %d  position: %d' % (image_number,run_id,position))

        #connect
        connection,cursor = self.get_db_connection()

        #get the run information
        query1 = 'select start FROM runs WHERE run_id=%s'
        cursor.execute(query1,(run_id))
        sql_ret = cursor.fetchone()
        self.closeConnection(connection,cursor)
        if sql_ret:
            start = sql_ret[0]
            #determine the image_number for the posiiton
            if (int(image_number) == (position-start+1)):
                return(True)
            else:
                return(False)
        else:
            return(False)

    def lastInRun(self,image_number,run_id):
        """
        Determine if an image is the last in a run as entered by marcollect
        Return True if yes and False if no
        """
        self.logger.debug('Database::lastInRun')

        #connect to mysql server
        connection,cursor = self.get_db_connection()

        #get the start and total images of the run in question
        query1 = 'select start,total FROM runs WHERE run_id=%s'
        cursor.execute(query1,(run_id))
        results = cursor.fetchone()
        if results:
            final = results[1]+results[0]-1
        else:
            final = 0

        self.logger.debug('Final image in run is number %d' % final)
        self.closeConnection(connection,cursor)
        if image_number == final:
            self.logger.debug('Final image!')
            return(True)
        else:
            self.logger.debug('Not final image')
            return(False)

    def getRunByRunId(self,run_id):
        """
        Returns a dict for the run which run_id belongs to
        """
        self.logger.debug('Database::getRunByRunId  run_id: %d' % run_id)

        try:
            query1   = 'SELECT * FROM runs WHERE run_id=%s'
            run_dict = self.make_dicts(query1, (run_id,))[0]
            #change the datetimes to JSON encodable
            run_dict['timestamp'] = run_dict['timestamp'].isoformat()
            return(run_dict)
        except:
            self.logger.exception('Error in getRunByRunId')
            return(False)

    def getRunWedges(self,run_id=-1):
        """
        Returns a list of wedges from a given run
        """
        self.logger.debug('Database::getRunWedges  run_id: %d' % run_id)

        #find all solutions for this result
        query = "SELECT isr.* FROM integrate_shell_results AS isr JOIN integrate_results AS ir ON (isr.isr_id = ir.shell_overall OR isr.isr_id = ir.shell_inner OR isr.isr_id = ir.shell_outer) WHERE ir.run_id=%s"
        request_list = self.make_dicts(query,(run_id,))

        if (len(request_list) > 0):
            return(request_list)
        else:
            return(False)

    def runAborted(self,run_dict):
        """
        Modifies the database entry for an aborted run based on images in the database
        and returns the image_id of the ending image for the run
        """
        self.logger.debug('Database::runAborted  run_id: %d' % run_dict['run_id'])

        #get cursor
        connection,cursor = self.get_db_connection()

        try:
            #get the images associated with the run
            query1 = 'SELECT image_id,image_number FROM images WHERE run_id=%s ORDER BY image_number DESC LIMIT 1'
            cursor.execute(query1,(run_dict['run_id']))
            image = cursor.fetchone()
            image_id, image_number = image

            #now modify the run such that total reflects the maximum image number collected
            new_total = image_number - run_dict['start'] + 1
            cursor.execute("UPDATE runs SET total=%s WHERE run_id=%s",(new_total,run_dict['run_id']))
            self.closeConnection(connection,cursor)
            #return
            return(image_id)

        except:
            self.logger.exception('Error in runAborted')
            self.closeConnection(connection,cursor)
            #return
            return(False)

    def editRun(self,mode,run_data):
      """
      Modify a run in the MySQL database
      mode can be
        total : change the total column
      """
      self.logger.debug('Database::editRun')

      if mode == 'total':
        db_query = "SELECT * FROM runs WHERE directory='%s' AND run_number='%s' AND image_prefix='%s' AND start=%d;" % (run_data['directory'],run_data['run_number'],run_data['prefix'],run_data['start'])

      self.logger.debug(db_query)
      my_dicts = self.make_dicts(db_query)
      if len(my_dicts) > 1:
        self.logger.debug('Error - cannot determine the proper run to modify')
        return False
      else:
        db_update = "UPDATE runs SET total=%d WHERE run_id=%d" % (run_data["total"],my_dicts[0]["run_id"])
        #get cursor
        connection,cursor = self.get_db_connection()
        cursor.execute(db_update)
        self.closeConnection(connection,cursor)
        my_dicts[0]["total"] = run_data["total"]
        return my_dicts[0]


    ##################################################################################################################
    # Cloud Functions                                                                                                #
    ##################################################################################################################
    def getMinikappaRequest(self):
        """
        Return the most recent minikappa request
        This refers to rapd_cloud.minikappa table
        """
        #print 'getMinikappaRequest'
        #Get ALL requests, sort by most recent
        try:
            query1  = 'SELECT * FROM minikappa WHERE status="request" ORDER BY timestamp DESC'
            request_dict = self.make_dicts(query1,(),'CLOUD')
            #request_dict['timestamp'] = request_dict['timestamp'].isoformat()
        except:
            request_dict = False

        if (request_dict):
            #the most recent request will be used
            request_return = request_dict[0]
            request_return['timestamp'] = request_return['timestamp'].isoformat()
            #mark all entries for the given site as 'read'
            site = request_return['site']
            for request in request_dict:
                if (request['site'] == site_id):
                    self.markMinikappaRequest(request['minikappa_id'],'read')
            #return the most recent request
            return(request_return)
        else:
            return(False)

    def markMinikappaRequest(self,minikappa_id,mark):
        """
        Modify entry in rapd_cloud.minikappa to mark
        """
        self.logger.debug('Database::markMinikappaRequest %d  %s' % (minikappa_id,mark))

        connection,cursor = self.connect_to_cloud()
        cursor.execute("UPDATE minikappa SET status=%s WHERE minikappa_id=%s",(mark,minikappa_id))
        self.closeConnection(connection,cursor)

    def getDatacollectionRequest(self):
        """
        Return the most recent minikappa request
        This refers to rapd_cloud.minikappa table
        """
        #print 'getDatacollectionRequest'
        #Get ALL requests, sort by most recent
        try:
            query1  = 'SELECT * FROM datacollection WHERE status="request" ORDER BY timestamp DESC'
            request_dict = self.make_dicts(query1,(),'CLOUD')
        except:
            request_dict = False

        if (request_dict):
            #the most recent request will be used
            request_return = request_dict[0]
            request_return['timestamp'] = request_return['timestamp'].isoformat()
            #mark all entries for the given site as 'read'
            site = request_return['site']
            for request in request_dict:
                if (request['site'] == site):
                    self.markDatacollectionRequest(request['datacollection_id'],'read')
            #return the most recent request
            return(request_return)
        else:
            return(False)

    def markDatacollectionRequest(self,datacollection_id,mark):
        """
        Modify entry in rapd_cloud.datacollection to mark
        """
        self.logger.debug('Database::markDatacollectionRequest %d  %s' % (datacollection_id,mark))

        connection,cursor = self.connect_to_cloud()
        cursor.execute("UPDATE datacollection SET status=%s WHERE datacollection_id=%s",(mark,datacollection_id))
        self.closeConnection(connection,cursor)

    def getCloudRequest(self):
        """
        Return the oldest cloud request
        """
        # query for oldest download request
        # self.logger.debug('Database.getCloudRequest')
        try:
            query1  = 'SELECT * FROM cloud_requests WHERE status="request" ORDER BY cloud_request_id LIMIT 1'
            request_dict = self.make_dicts(query1,(),'CLOUD')[0]
            request_dict['timestamp'] = request_dict['timestamp'].isoformat()
        except:
            request_dict = False

        #see if we have a request
        return(request_dict)

    def markCloudRequest(self,cloud_request_id,mark):
        """
        Modify entry in cloud_requests to mark
        """
        self.logger.debug('Database::markCloudRequest %d  %s' % (cloud_request_id,mark))

        connection,cursor = self.connect_to_cloud()
        cursor.execute("UPDATE cloud_requests SET status=%s WHERE cloud_request_id=%s",(mark,cloud_request_id))
        self.closeConnection(connection,cursor)

    def addCloudCurrent(self,request):
        """
        Add an entry to the rapd_cloud.cloud_current table
        This keeps track of jobs currently on the cloud
        """
        self.logger.debug('Database::addCloudCurrent')

        connection,cursor = self.connect_to_cloud()
        cursor.execute("INSERT cloud_current (cloud_request_id,request_timestamp) VALUES (%s,%s)",(request['cloud_request_id'],request['timestamp']))
        self.closeConnection(connection,cursor)

    def removeCloudCurrent(self,cloud_request_id):
        """
        Remove an entry from the rapd_cloud.cloud_current table
        This keeps track of jobs currently on the cloud
        """
        self.logger.debug('Database::addCloudCurrent')

        connection,cursor = self.connect_to_cloud()
        cursor.execute("DELETE FROM cloud_current WHERE cloud_request_id='%s'",(cloud_request_id,))
        self.closeConnection(connection,cursor)

    def enterCloudComplete(self,cloud_request_id,request_timestamp,request_type,data_root_dir,ip_address='0.0.0.0',start_timestamp=0,result_id=0,archive=False):
        """
        Create an entry in the rapd_cloud.cloud_complete table
        """
        self.logger.debug('Database::enterCloudComplete')

        try:
            connection,cursor = self.connect_to_cloud()
            cursor.execute("""INSERT INTO cloud_complete (cloud_request_id,
                                                          request_timestamp,
                                                          start_timestamp,
                                                          result_id,
                                                          request_type,
                                                          data_root_dir,
                                                          ip_address,
                                                          status,
                                                          archive) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(cloud_request_id,
                                                                                                           request_timestamp,
                                                                                                           start_timestamp,
                                                                                                           result_id,
                                                                                                           request_type,
                                                                                                           data_root_dir,
                                                                                                           ip_address,
                                                                                                           'new',
                                                                                                           archive))
            self.closeConnection(connection,cursor)
        except:
            self.logger.exception("Error in enterCloudComplete")

        #remove the entry in cloud_current
        self.removeCloudCurrent(cloud_request_id = cloud_request_id)

    def getDownimageInfo(self, request):
        """
        Returns (source_dir,(images,), work_dir) for a given download request
        """
        self.logger.debug('Database::getDownimageInfo')

        if request['original_type'] == 'single':
            query1    = 'SELECT fullname,work_dir,repr FROM single_results WHERE single_result_id=%s'
            my_dict   = self.make_dicts(query1,(request['original_id'],),'DATA')[0]
            my_return = (os.path.dirname(my_dict['fullname']), (os.path.basename(my_dict['fullname']),), my_dict['work_dir'])

        elif request['original_type'] == 'pair':
            query1    = 'SELECT fullname_1,fullname_2,work_dir,repr FROM pair_results WHERE pair_result_id=%s'
            my_dict   = self.make_dicts(query1,(request['original_id'],),'DATA')[0]
            my_return = (os.path.dirname(my_dict['fullname_1']), (os.path.basename(my_dict['fullname_1']),os.path.basename(my_dict['fullname_2'])), my_dict['work_dir'])

        elif request['original_type'] == 'integrate':
            query1    = 'SELECT images_dir,template,work_dir,images_dir,image_start,image_end,repr FROM integrate_results WHERE integrate_result_id=%s'
            my_dict   = self.make_dicts(query1,(request['original_id'],),'DATA')[0]
            image_files = []
            for i in range(my_dict['image_start'],my_dict['image_end']+1):
                image_files.append(os.path.basename(my_dict['template']).replace('###',(str(i).zfill(3))))

            my_return = (my_dict['images_dir'], image_files, my_dict['work_dir'],my_dict['repr'])

        else:
            my_return = (False,False,False)

        return(my_return)

    def getDownSadInfo(self,request):
        """
        Returns (download_file,repr) for a given download request
        """
        self.logger.debug('Database::getDownSadInfo')

        if (request['request_type'] == 'downsad'):
            query1 = 'SELECT sad_status,download_file,repr FROM sad_results WHERE sad_result_id=%s'
        elif (request['request_type'] == 'downshelx'):
            query1 = 'SELECT sad_status,shelx_tar as download_file,repr FROM sad_results WHERE sad_result_id=%s'

        try:
            my_dict = self.make_dicts(query1,(request['original_id'],),'DATA')[0]
            self.logger.debug(my_dict)
            return((my_dict['download_file'],my_dict['repr']))
        except:
            self.logger.debug('ERROR in Database::getDownSadInfo')
            return(False)

    def getDownMadInfo(self, request):
        """
        Returns (download_file,repr) for a given download request
        """
        self.logger.debug('Database::getDownMadInfo', request)

        if (request['request_type'] == 'downmad'):
            query1 = 'SELECT mad_status,download_file,repr FROM mad_results WHERE mad_result_id=%s'
        elif (request['request_type'] == 'downmadshelx'):
            query1 = 'SELECT mad_status,shelx_tar as download_file,repr FROM mad_results WHERE mad_result_id=%s'

        try:
            my_dict = self.make_dicts(query1,(request['original_id'],),'DATA')[0]
            self.logger.debug(my_dict)
            return((my_dict['download_file'],my_dict['repr']))
        except:
            self.logger.debug('ERROR in Database::getDownMadInfo')
            return(False)

    def getDownMrInfo(self,request):
        """
        Returns (download_file,repr) for a given MR download request.
        """

        self.logger.debug('Database::getDownMrInfo')

        try:
            query1 = "SELECT mr_trial_results.archive as archive, mr_results.repr as repr FROM mr_trial_results JOIN mr_results ON (mr_results.mr_result_id = mr_trial_results.mr_result_id) WHERE mr_results.result_id=%s AND mr_trial_results.spacegroup=%s"
            my_dict = self.make_dicts(query1,(request['original_result_id'],request['option1']))[0]
            self.logger.debug(my_dict)
            return((my_dict['archive'],my_dict['repr']))
        except:
            self.logger.exception("Exception in getDownMrInfo")
            return(False)

    def getDownIntegrateInfo(self,request):
        """
        Returns (download_file,repr) for a given integration or merge cell analysis download request.
        """

        self.logger.debug('Database::getDownIntegrateInfo')

        try:
            query0 = "SELECT type FROM results WHERE result_id=%s"
            src_type = self.make_dicts(query0,(request['original_result_id'],))[0]['type']

            query1 = "SELECT cell_analysis_results.automr_tar as archive, "+src_type+"_results.repr as repr FROM cell_analysis_results JOIN "+src_type+"_results ON ("+src_type+"_results.result_id = cell_analysis_results.result_id) WHERE cell_analysis_results.result_id = %s AND cell_analysis_results.pdb_id=%s"
            my_dict = self.make_dicts(query1,(request['original_result_id'],request['option1']))[0]
            self.logger.debug(my_dict)
            return((my_dict['archive'],my_dict['repr']))
        except:
            self.logger.exception("Exception in getDownIntegrateInfo")
            return(False)

    def getDownSadCellInfo(self,request):
        """
        Returns (download_file,repr) for a given SAD Cell Analysis download request.
        """

        self.logger.debug('Database::getDownSadCellInfo')

        try:
            query1 = "SELECT cell_analysis_results.automr_tar as archive, sad_results.repr as repr FROM cell_analysis_results JOIN sad_results ON (sad_results.sad_result_id = cell_analysis_results.sad_result_id) WHERE sad_results.result_id=%s AND cell_analysis_results.pdb_id=%s"
            my_dict = self.make_dicts(query1,(request['original_result_id'],request['option1']))[0]
            self.logger.debug(my_dict)
            return((my_dict['archive'],my_dict['repr']))
        except:
            self.logger.exception("Exception in getDownSadCellInfo")
            return(False)

    def getDownprocInfo(self,request):
        """
        Returns ([source_dirs], [source files], work_dir) for a given download request
        """
        self.logger.debug('Database::getDownprocInfo')

        try:
            #query the database for the information on where files are
            if (request['original_type'] == "integrate"):
                query1 = 'SELECT  integrate_status,work_dir,xia_log,xscale_log,scala_log,unmerged_sca_file,sca_file,mtz_file,download_file,pipeline,repr FROM integrate_results WHERE integrate_result_id=%s'
            elif (request['original_type'] == "merge"):
                query1 = 'SELECT merge_status,work_dir,download_file,repr FROM merge_results WHERE merge_result_id=%s'
            my_dict = self.make_dicts(query1,(request['original_id'],),'DATA')[0]
            self.logger.debug(my_dict)

            #now construct a series of directory and file pairs
            dirs  = []
            files = []

            if (request['original_type'] == "integrate"):
                if (my_dict['pipeline'] == 'fastint'):
                    if my_dict['integrate_status'] in ('SUCCESS','ANALYSIS'):
                        return((my_dict['download_file'],my_dict['repr']))
                    else:
                        return(False)

                elif (my_dict['pipeline'] == 'xia2'):
                    if my_dict['integrate_status'] == 'SUCCESS':
                        #the directories
                        dirs.append(os.path.dirname(my_dict['xia_log']))
                        dirs.append(os.path.dirname(my_dict['xscale_log']))
                        dirs.append(os.path.dirname(my_dict['scala_log']))
                        dirs.append(os.path.dirname(my_dict['unmerged_sca_file']))
                        dirs.append(os.path.dirname(my_dict['sca_file']))
                        dirs.append(os.path.dirname(my_dict['mtz_file']))
                        #the files
                        files.append(os.path.basename(my_dict['xia_log']))
                        files.append(os.path.basename(my_dict['xscale_log']))
                        files.append(os.path.basename(my_dict['scala_log']))
                        files.append(os.path.basename(my_dict['unmerged_sca_file']))
                        files.append(os.path.basename(my_dict['sca_file']))
                        files.append(os.path.basename(my_dict['mtz_file']))
                        #
                        return((dirs,files,my_dict['work_dir'],my_dict['repr']))
                    else:
                        #the directories
                        dirs.append(os.path.dirname(my_dict['xia_log']))
                        #the files
                        files.append(os.path.basename(my_dict['xia_log']))
                        #
                        return((dirs,files,my_dict['work_dir'],my_dict['repr']))
            elif (request['original_type'] == "merge"):
                if (my_dict['merge_status'] == 'SUCCESS'):
                    return((my_dict['download_file'],my_dict['repr']))
                else:
                    return(False)
        except:
            self.logger.debug('ERROR in Database::getDownprocInfo')
            return(False)

    def getCloudClearance(self):

        """
        Check the state of the cloud and the allowed processes and return True if job is allowed, False if not
        """
        self.logger.debug('Database::getCloudClearance')

        try:
            #connect to the DB
            connection,cursor = self.connect_to_cloud()

            #Check the number of currently running remote processes if it's older than 2 hours, it's probably erroneous
            cursor.execute('SELECT * FROM cloud_current WHERE TIMESTAMPDIFF(SECOND,timestamp,NOW()) < 600')
            current_cloud_processes = cursor.rowcount;
            self.logger.debug(current_cloud_processes)

            #Get the allowed concurrent remote processes
            cursor.execute('SELECT remote_concurrent_allowed from cloud_state')
            allowed_cloud_processes = cursor.fetchone()[0]
            self.logger.debug(allowed_cloud_processes)
            self.closeConnection(connection,cursor)
            if (current_cloud_processes >= allowed_cloud_processes):
                return(False)
            elif (current_cloud_processes < allowed_cloud_processes):
                return(True)
        except:
            self.logger.exception('Error in getCloudClearance')
            self.closeConnection(connection,cursor)
            return(False)

    def addToCloudQueue(self):
        """
        Add to the rapd_cloud.cloud_state.current_queue so that we can control the access of remote processes to the cloud
        """
        self.logger.debug('Database::addToCloudQueue')

        try:
            #connect to the DB
            connection,cursor = self.connect_to_cloud()

            #increment the entry
            cursor.execute('UPDATE cloud_state set current_queue = current_queue + 1')
            self.closeConnection(connection,cursor)
            return(True)

        except:
            self.logger.exception('Error in addToCloudQueue')
            self.closeConnection(connection,cursor)
            return(False)

    def subtractFromCloudQueue(self):
        """
        Subtract from the rapd_cloud.cloud_state.current_queue so that we can control the access of remote processes to the cloud
        """
        self.logger.debug('Database::subtractFromCloudQueue')

        try:
            #connect to the DB
            connection,cursor = self.connect_to_cloud()

            #increment the entry
            cursor.execute('UPDATE cloud_state set current_queue = current_queue - 1 WHERE current_queue > 0')
            self.closeConnection(connection,cursor)
            return(True)

        except:
            self.logger.exception('Error in subtractFromCloudQueue')
            self.closeConnection(connection,cursor)
            return(False)

    ##################################################################################################################
    # Status logging functions                                                                                       #
    ##################################################################################################################
    def update_controller_status(self,
                                 controller_ip=None,
                                 data_root_dir=None,
                                 site_id=None,
                                 dataserver_ip=None,
                                 cluster_ip=None):
        """
        Log the controller as an update to the status_controller table in rapd_data
        """
        self.logger.debug("Database::update_controller_status")

        #connect to database
        connection, cursor = self.get_db_connection()

        #construct and run query
        try:
            cursor.execute('INSERT INTO status_controller (controller_ip,data_root_dir,site,dataserver_ip,cluster_ip) VALUES (%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE data_root_dir=%s,site=%s,dataserver_ip=%s,cluster_ip=%s,timestamp=CURRENT_TIMESTAMP ', (controller_ip, data_root_dir, site_id, dataserver_ip, cluster_ip, data_root_dir, site_id, dataserver_ip, cluster_ip))
        except:
            self.logger.exception('Trouble writing the status of the controller into the database')
        self.closeConnection(connection, cursor)

    def updateClusterStatus(self,cluster_ip=None):
        """
        Log the controller as an update to the status_cluster table in rapd_data
        """
        self.logger.debug('Database::updateClusterStatus')

        #connect to database
        connection,cursor = self.get_db_connection()

        #construct and run query
        try:
            cursor.execute('INSERT INTO status_cluster (ip_address) VALUES (%s) ON DUPLICATE KEY UPDATE timestamp=CURRENT_TIMESTAMP ',(cluster_ip))
        except:
            self.logger.exception('Trouble writing the status of the cluster into the database')
        self.closeConnection(connection,cursor)

    def bc_test(self):
        import math
        #connect to database
        connection,cursor = self.get_db_connection()

        cursor.execute('''SELECT single_results.labelit_res,single_results.labelit_mosaicity,single_results.labelit_rmsd,
                            single_results.timestamp,single_results.labelit_x_beam,single_results.labelit_y_beam,
                            images.distance
                            from single_results
                            join images on (single_results.image_id = images.image_id)
                            where images.site="24_ID_C" and single_results.labelit_res is not null
                            order by single_results.timestamp''')
        for row in cursor.fetchall():
            if (0.5 < (1-0.7*math.e**(-4/row[0])-1.5*row[2]-0.2*row[1])):
                print ('%s  %6.2f %4.2f  %4.2f' % (str(row[3]),row[6],row[4],row[5]))
        self.closeConnection(connection,cursor)

    ##################################################################################################################
    #PDB Functions                                                                                                   #
    ##################################################################################################################
    def getPdbById(self,pdbs_id):
        """
        Return the entry defined by the input pdbs_id as a dict
        """
        self.logger.debug('Database::getPdbById pdbs_id:%d' % pdbs_id)

        query = "SELECT * FROM pdbs WHERE pdbs_id = %s"

        try:
            my_dict = self.make_dicts(query=query,
                                     params=(pdbs_id,),
                                     db='DATA')[0]
            return(my_dict)
        except:
            self.logger.debug('ERROR in Database::getPdbById')
            return(False)

    def updatePdbLocation(self,pdbs_id,location):
        """
        Update an entry in rapd_data.pdbs to have a new location entry
        """
        self.logger.debug('Database::updatePdbLocation pdbs_id:%d  location:%s' % (pdbs_id,location))

        #connect to database
        connection,cursor = self.get_db_connection()
        #construct query
        query = "UPDATE pdbs SET location=%s WHERE pdbs_id=%s"
        params = (location,pdbs_id)
        #run query
        cursor.execute(query,params)
        self.closeConnection(connection,cursor)
        return(True)


    ##################################################################################################################
    # Database utility functions                                                                                     #
    ##################################################################################################################
    def Decode(self,item):
        import base64
        return(base64.b64decode(item))

    def make_dicts(self, query, params=(), db="DATA"):
        """
        Got the idea for this from Programming Python p 1241
        """
        # Get the connection
        connection,cursor = self.get_db_connection()
        # if (db == 'DATA'):
        #     connection,cursor = self.get_db_connection()
        # elif (db == 'USERS'):
        #     connection,cursor = self.connect_to_user()
        # elif (db == 'CLOUD'):
        #     connection,cursor = self.connect_to_cloud()

        # Execute the query
        if (len(params)==0):
            cursor.execute(query)
        else:
            cursor.execute(query,params)

        # Assemble the dict(s) into an array
        colnames = [desc[0] for desc in cursor.description]
        rowdicts = [dict(zip(colnames,row)) for row in cursor.fetchall()]
        self.closeConnection(connection,cursor)

        # Return the array of dicts
        return rowdicts



if __name__ == '__main__':

    print 'rapd_mysql_adapter.py.__main__'
