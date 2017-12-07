"""
This file is part of RAPD

Copyright (C) 2009-2017, Cornell University
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
rapd_beamlinespecific has a number of functions that need to be overloaded for
each specific beamline
"""

import datetime
import os
import pymongo
import pysent
import re
import redis.exceptions as redis_exceptions
import threading
import time
import uuid

from utils.text import json
from bson.objectid import ObjectId

#
# The default settings for each beamline; Your modifications of rapd_site.py should
# have created the correct information in the imports here
#
from rapd_site import secret_settings, secret_settings_general


#the extra time the RunWatcher will wait for an image file to appear
IMAGE_WAIT = 20

#
# Methods for watching for new run & image information
#
# RAPD is developed with an ADSC CCD detector system
# You will have to create your own ImageMonitor and import it here
# if you do not use ADSC detectors
#
from detectors.rapd_pilatus import PilatusMonitor
from detectors.rapd_adsc import Q315_Monitor, Hf4m_Monitor
from rapd_console import ConsoleRunMonitor
#
# Methods for connecting to the beamline control system
#
# RAPD is developed with CONSOLE as the beamline control system (by Malcolm Capel)
# This is currently use to monitor for aborts during data collection and to
# get information in case of errors in the header of the image
#
from rapd_console import ConsoleRedisMonitor, ConsoleRedisMonitor2
from rapd_cluster import PerformAction



class Remote(object):
    """Serves as a connection to the remote beamline control system"""

    mongo = None
    mongo_remote = None
    redis = None

    def __init__(self, beamline="E", logger=None):
        """
        Keyword arguments:
        beamline -- tag denoting the beamline to connect to C, E, or T at necat
        logger -- an instance of logger
        """

        if logger:
            logger.info("Remote.__init__  beamline=%s" % beamline)

        #Store variables
        self.beamline = beamline
        self.logger = logger

        # Initialize the database connections
        self.init_db()

    def init_db(self):
        """Initialize the database connections"""

        if self.logger:
            self.logger.debug("Remote.init_db")

        #Establish connection to redis database
        try:
            self.redis = pysent.RedisManager(sentinel_host="remote.nec.aps.anl.gov",
                                             sentinel_port=26379,
                                             master_name="remote_master")

        except (redis_exceptions.ConnectionError, TypeError) as error:
            self.redis = False
            if self.logger:
                self.logger.exception("Remote.__init__  beamline=%s cannot conn\
ect to redis db at %s" % (self.beamline, secret_settings_general.get("remote_redis_ip")))
                self.logger.exception(error)

        #Establish connection to Mongo database
        try:
            settings = secret_settings[self.beamline]
            self.mongo = pymongo.MongoClient(
                settings["mongo-connection-string"])
            self.mongo_remote = self.mongo.remote
        except:
            self.logger.exception("Remote.__init__  beamline=%s cannot conn\
ect to MongoDB at %s" % (self.beamline, settings["mongo-connection-string"]))

    def add_image(self, image_metadata):
        """Add an image to the remote system

        Keyword argument:
        image_metadata -- dict containing image metadata
        """
        if self.logger:
            self.logger.debug("Remote.add_image image:%s" %
                              image_metadata.get("fullname"))
            self.logger.debug(image_metadata)

        # Add useful info to the metadata for
        image_metadata["name"] = os.path.basename(image_metadata["fullname"])
        image_metadata["_id"] = str(uuid.uuid1())

        # Filter for no image_id key
        if not "image_id" in image_metadata:
            image_metadata["image_id"] = 0

        #Publish image_metadata for subscribers
        try:
            self.logger.debug("Publishing %s %s" % (image_metadata["fullname"], json.dumps(image_metadata)))
            self.redis.publish(image_metadata["fullname"],
                               json.dumps(image_metadata))
        # TODO - handle redis exceptions
        except:
            if self.logger:
                self.logger.exception("Error publishing image metadata to Redis")

        # Save to Mongo
        try:
            self.mongo_remote.image_metadata.update(
                {"_id":image_metadata["_id"]},
                image_metadata,
                upsert=True,
                multi=False)
        # TODO - handle mongoDB exceptions
        except:
            if self.logger:
                self.logger.exception("Error writing image metadata to MongoDB")

        return image_metadata["_id"]

    def update_run_progress(self, run_position=0, image_name="", run_data=None):
        """Publish run status to the Redis database for Remote project's benefit
        The run_data looks like this:
        {'status': 'STARTED', 'distance': 650.0, 'phi': 0.0, 'run_number': 1,
         'kappa': 0.0, 'width': 0.5, 'beamline': 'C', 'file_source': 'PILATUS',
         'twotheta': 0.0, 'start': 1, 'prefix': 'I5_GABA',
         'time': 0.20000000000000001,
         'directory': '/gpfs8/users/GU/Lodowski_C_Nov14/images/nick/H4_GABA/0_0',
         'total': 220, 'omega': 100.0, 'axis': 'omega'}
        """
        if self.logger:
            self.logger.debug('Remote.update_run_progress')

        if image_name.endswith('.cbf'):
            my_repr = re.sub(r'\d{4}\.cbf', r'####.cbf', image_name)
        elif image_name.endswith('.img'):
            my_repr = re.sub(r'\d{3}\.img', r'###.img', image_name)

        if run_data == None:
            run_data = {}

        assembled_data = {'beamline'      : self.beamline,
                          'run_id'        : run_data.get('run_id', 0),
                          'run_position'  : run_position,
                          'run_start'     : run_data.get('start', 1),
                          'run_total'     : run_data.get('total', 0),
                          'directory'     : run_data.get('directory', ''),
                          'current_image' : image_name,
                          'omega_start'   : run_data.get('omega', 0.0),
                          'omega_delta'   : run_data.get('width', 0.0),
                          'exposure'      : run_data.get('time', 0.0),
                          'distance'      : run_data.get('distance', 0.0),
                          'date'          : datetime.datetime.now().isoformat(),
                          'repr'          : my_repr}

        # Publish data through redis
        if self.logger:
            self.logger.debug("Publishing run_update_%s %s" % (self.beamline, json.dumps(assembled_data)))
        self.redis.publish("run_update_%s" % self.beamline, json.dumps(assembled_data))

        # Save to Mongo
        try:
            self.mongo_remote.run_data.update(
                {"run_id":run_data.get('run_id')},
                assembled_data,
                upsert=True,
                multi=False)
        # TODO - handle mongoDB exceptions
        except:
            if self.logger:
                self.logger.exception("Error writing run_data to MongoDB")

    def update_image_stats(self, result_db, wedges_db):
        """Publish image statistics to the Redis database for Remote project's
        benefit
        """
        if self.logger:
            self.logger.debug('Remote.update_image_stats')
            self.logger.debug(result_db)
            self.logger.debug(wedges_db)

        # Data will go in here
        indexing_data = {}
        wedge = {}

        # If the indexing worked
        if result_db['labelit_status'] == 'SUCCESS':
            indexing_data.update({'status'       : 'indexed',
                                  'beamline'     : self.beamline,
                                  'fullname'     : result_db.get('fullname', 0),
                                  'image_id'     : result_db.get('image_id', 0),
                                  'pointgroup'   : result_db.get('labelit_spacegroup'),
                                  'a'            : result_db.get('labelit_a'),
                                  'b'            : result_db.get('labelit_b'),
                                  'c'            : result_db.get('labelit_c'),
                                  'alpha'        : result_db.get('labelit_alpha'),
                                  'beta'         : result_db.get('labelit_beta'),
                                  'gamma'        : result_db.get('labelit_gamma'),
                                  'resolution'   : result_db.get('distl_labelit_res'),
                                  'mosaicity'    : result_db.get('labelit_mosaicity'),
                                  'overloads'    : result_db.get('distl_overloads')})

            # If we have a normal strategy
            if result_db["best_norm_status"] == "SUCCESS":
                # Get the normal strategy wedge
                for wedge in wedges_db:
                    if wedge['strategy_type'] == 'normal':
                        break
                indexing_data.update({'status'               : 'normal',
                                      'normal_omega_start'   : wedge.get('phi_start', -1),
                                      'normal_omega_step'    : wedge.get('delta_phi', -1),
                                      'normal_number_images' : wedge.get('number_images', -1)
                                     })

                # If we have an anomalous strategy
                if result_db['best_anom_status'] == 'SUCCESS':
                    # Get the anomalous strategy wedge
                    for wedge in wedges_db:
                        if  wedge['strategy_type'] == 'anomalous':
                            break
                    indexing_data.update({'status'               : 'all',
                                          'anom_omega_start'   : wedge.get('phi_start', -1),
                                          'anom_omega_step'    : wedge.get('delta_phi', -1),
                                          'anom_number_images' : wedge.get('number_images', -1)
                                         })

        # No indexing solution
        else:
            indexing_data.update({'status'   : 'failure',
                                  'beamline' : self.beamline,
                                  'fullname' : result_db.get('fullname', 0),
                                  'image_id' : result_db.get('image_id', 0)
                                 })


        # Publish to redis connectioni
        if self.logger:
            self.logger.debug("Publishing image_stats_%s %s" % (self.beamline, json.dumps(indexing_data)))
        self.redis.publish("image_stats_%s" % self.beamline, json.dumps(indexing_data))

        # Save to Mongo
        try:
            self.mongo_remote.autoindex_data.insert(indexing_data)
        # TODO - handle mongoDB exceptions
        except:
            if self.logger:
                self.logger.exception("Error writing run_data to MongoDB")


    def update_run_stats(self, result_db, wedges):
        """
        Publish run statistics to the Redis database for Remote project's benefit
        """

        if self.logger:
            self.logger.debug('Remote.update_run_stats')
            self.logger.debug(result_db)
            self.logger.debug(wedges)

        # Derive the session_id
        session_id = result_db["data_root_dir"].split("_")[-1]

        #
        integration_data = {}
        # Assign the basic data
        integration_data.update({'status'       : result_db.get('integrate_status').lower(),
                                 'beamline'     : self.beamline,
                                 'run_id'       : result_db.get('run_id', -1),
                                 'spacegroup'   : result_db.get('spacegroup', 'P0'),
                                 'a'            : result_db.get('a', -1),
                                 'b'            : result_db.get('b', -1),
                                 'c'            : result_db.get('c', -1),
                                 'alpha'        : result_db.get('alpha', -1),
                                 'beta'         : result_db.get('beta', -1),
                                 'gamma'        : result_db.get('gamma', -1),
                                 'image_start'  : result_db.get('image_start', -1),
                                 'image_end'    : result_db.get('image_end', -1)})

        # Organize the wedges
        if wedges:
            for wedge in wedges:
                wtag = wedge.get('shell_type')
                if wtag in ('overall', 'outer', 'inner'):
                    integration_data.update(
                        {'res_low_'+wtag           : wedge.get('low_res', -1),
                         'res_high_'+wtag          : wedge.get('high_res', -1),
                         'completeness_'+wtag      : wedge.get('completeness', -1),
                         'multiplicity_'+wtag      : wedge.get('multiplicity', -1),
                         'i_sigi_'+wtag            : wedge.get('i_sigma', -1),
                         'rmeas_'+wtag             : wedge.get('r_meas', -1),
                         'rpim_'+wtag              : wedge.get('r_pim', -1),
                         'anom_completeness_'+wtag : wedge.get('anom_completeness', -1),
                         'anom_multiplicity_'+wtag : wedge.get('anom_multiplicity', -1),
                         'anom_rmeas_'+wtag        : wedge.get('r_meas_pm', -1),
                         'anom_rpim_'+wtag         : wedge.get('r_pim_pm', -1),
                         'anom_corr_'+wtag         : wedge.get('anom_correlation', -1),
                         'anom_slope_'+wtag        : wedge.get('anom_slope', -1),
                         'ref_total_'+wtag         : wedge.get('total_obs', -1),
                         'ref_unique_'+wtag        : wedge.get('unique_obs', -1)
                        })

        if self.logger:
            self.logger.debug('Sending integration_data to remote')
            self.logger.debug(integration_data)

        # Publish to redis connection
        #self.redis.publish('run_stats_'+self.beamline,data)

        # Save the data to redis
        j_data = json.dumps(integration_data)
        # Publish to redis connections
        self.redis.publish('run_stats_'+self.beamline, j_data)

        # Save to Mongo
        try:
            self.logger.debug('Saving to mongoDB')
            self.mongo_remote.integration_data.update(
                {"run_id":result_db.get("run_id", -1)},
                integration_data,
                upsert=True,
                multi=False)
        # TODO - handle mongoDB exceptions
        except:
            if self.logger:
                self.logger.exception("Error writing run_data to MongoDB")

    def add_quick_analysis_result(self, result_data):
        """Process a new quickanalysis result"""

        if self.logger:
            self.logger.info('Remote.add_quick_analysis_result')
            self.logger.info(result_data)

        # Add the image to the remote client
        node, image_uuid = self.add_image(result_data)

        # Assemble results to be published
        assemble = {'raster_uuid': result_data.get('raster_uuid', ''),
                    'image_uuid': image_uuid,
                    'node': node,
                    'status': 'success',
                    'beamline': self.beamline,
                    'crystal_image': result_data.get('crystal_image', ''),
                    'fullname': result_data.get('fullname', ''),
                    'image_id': result_data.get('image_id', 0),
                    'image_number': result_data.get('image_number', 0),
                    'md2_x': result_data.get('md2_x', 0),
                    'md2_y': result_data.get('md2_y', 0),
                    'md2_z': result_data.get('md2_z', 0)
                   }

        # Publish to redis connection
        results = json.dumps(assemble)
        json_assemble = json.dumps(assemble)
        a_key = 'quickanalysis_result:'+assemble.get('raster_uuid')+':'+ \
                str(assemble.get('image_number'))

        self.redis.publish('quickanalysis_result_%s' % self.beamline, results)

        # Save data in redis database
        self.redis.set(a_key, json_assemble)
        self.redis.expire(a_key, 8000000)  # Expire in a month

class ImageMonitor(threading.Thread):
    """Monitor the beamline for new images"""

    adsc_monitor_reconnect_attempts = 0
    console_monitor_reconn_attempts = 0
    adsc_monitor = None
    console_monitor = None
    console_monitor_2 = None
    pilatus_monitor = None

    def __init__(self, beamline="C", notify=None, logger=None):
        if logger:
            logger.info('ImageMonitor::__init__  beamline:%s' % beamline)

        #init the thread
        threading.Thread.__init__(self)

        self.beamline = beamline
        self.notify = notify
        self.logger = logger

        self.start()

    def run(self):
        self.logger.debug('ImageMonitor::run %s',
            secret_settings[self.beamline]["file_source"])

        if self.beamline == "C":
            self.pilatus_monitor = PilatusMonitor(beamline=self.beamline,
                                                  notify=self.notify,
                                                  reconnect=None,
                                                  logger=self.logger)

            self.console_monitor = ConsoleRedisMonitor(beamline=self.beamline,
                                                       notify=self.notify,
                                                       logger=self.logger)

        elif self.beamline == "E":

            # Configure for the Q315
            if secret_settings[self.beamline]['file_source'] == 'Q315':
                #The Image monitor which checks xf_status and marcollect from adsc
                self.adsc_monitor = Q315_Monitor(beamline=self.beamline,
                                                 notify=self.notify,
                                                 reconnect=self.adsc_reconnect,
                                                 logger=self.logger)

                #The console monitor which checks marcollect from console
                self.console_monitor = ConsoleRunMonitor(beamline=self.beamline,
                                                         notify=self.notify,
                                                         reconnect=self.console_reconnect,
                                                         logger=self.logger)

                #The console connection via redis
                self.console_monitor_2 = ConsoleRedisMonitor2(beamline=self.beamline,
                                                              notify=self.notify,
                                                              logger=self.logger)

            # Configure for the HF4M
            elif secret_settings[self.beamline]['file_source'] == 'HF4M':
                self.adsc_monitor = Hf4m_Monitor(beamline=self.beamline,
                                                 notify=self.notify,
                                                 reconnect=None,
                                                 logger=self.logger)

                self.console_monitor = ConsoleRedisMonitor(beamline=self.beamline,
                                                           notify=self.notify,
                                                           logger=self.logger)

    def adsc_reconnect(self):
        """
        Reconnection method for the ADSC_MONITOR
        """
        self.adsc_monitor_reconnect_attempts += 1
        self.logger.warning('ImageMonitor::adsc_reconnect try %d' % \
                            self.adsc_monitor_reconnect_attempts)
        if self.adsc_monitor_reconnect_attempts < 1000:
            self.adsc_monitor = False
            time.sleep(10)
            if secret_settings[self.beamline]['file_source'] == 'Q315':
                self.adsc_monitor = Q315_Monitor(beamline=self.beamline,
                                                 notify=self.notify,
                                                 reconnect=self.adsc_reconnect,
                                                 logger=self.logger)

            elif secret_settings[self.beamline]['file_source'] == 'HF4M':
                self.adsc_monitor = Hf4m_Monitor(beamline=self.beamline,
                                                 notify=self.notify,
                                                 reconnect=None,
                                                 logger=self.logger)
        else:
            self.adsc_monitor = False
            self.logger.warning('Too many ADSC monitor connection attempts - exiting')
            exit()

    def console_reconnect(self):
        """
        Reconnection method for the CONSOLE_MONITOR
        """

        self.console_monitor_reconn_attempts += 1
        self.logger.warning('ImageMonitor::console_reconnect try %d' % \
                            self.console_monitor_reconn_attempts)
        if self.console_monitor_reconn_attempts < 1000:
            self.console_monitor = False
            time.sleep(10)
            self.console_monitor = ConsoleRunMonitor(beamline=self.beamline,
                                                     notify=self.notify,
                                                     reconnect=self.console_reconnect,
                                                     logger=self.logger)
        else:
            self.console_monitor = False
            self.logger.warning('Too many Console monitor connection attempts - exiting')
            exit()



class BeamManager(object):
    """Class for maintaining proper beam center formula - not used"""

    images = []
    times = {}
    expire_in = 600

    def __init__(self, database, settings, my_secret_settings, toplevel_dir,
                 beamline="E", ip_address="127.0.0.1", socket=3001, logger=None):
        if logger:
            logger.info('BeamManager.__init__  beamline=%s'%beamline)

        self.database = database
        self.settings = settings
        self.secret_settings = my_secret_settings
        self.secret_settings['toplevel_dir'] = toplevel_dir
        self.beamline = beamline
        self.address = (ip_address, socket)
        self.logger = logger

        #get the current beam data for this beamline
        self.beamcenter_data = self.get_beam_formula()

    # manage incoming beamcenter images
    def new_beamcenter_image(self, image_data):
        """Process a new beamcenter image"""

        # Record time of image arrival
        my_time = time.time()

        #Correct the beamcenter before sending...
        if not float(self.settings['x_beam']):
            #beam position is not overridden in settings by user - check site settings
            if self.settings["use_beam_formula"]:
                #we are going to use the beam formula
                #new polynomial equation
                image_data['x_beam'] = self.settings['beam_center_x_m6'] * \
                                       float(image_data['distance'])**6 + \
                                       self.settings['beam_center_x_m5'] * \
                                       float(image_data['distance'])**5 + \
                                       self.settings['beam_center_x_m4'] * \
                                       float(image_data['distance'])**4 + \
                                       self.settings['beam_center_x_m3'] * \
                                       float(image_data['distance'])**3 + \
                                       self.settings['beam_center_x_m2'] * \
                                       float(image_data['distance'])**2 + \
                                       self.settings['beam_center_x_m1'] * \
                                       float(image_data['distance']) + \
                                       self.settings['beam_center_x_b']
                image_data['y_beam'] = self.settings['beam_center_y_m6'] * \
                                       float(image_data['distance'])**6 + \
                                       self.settings['beam_center_y_m5'] * \
                                       float(image_data['distance'])**5 + \
                                       self.settings['beam_center_y_m4'] * \
                                       float(image_data['distance'])**4 + \
                                       self.settings['beam_center_y_m3'] * \
                                       float(image_data['distance'])**3 + \
                                       self.settings['beam_center_y_m2'] * \
                                       float(image_data['distance'])**2 + \
                                       self.settings['beam_center_y_m1'] * \
                                       float(image_data['distance']) + \
                                       self.settings['beam_center_y_b']
                self.logger.debug('Using calculated beam center of X: %6.2f  Y: \
%6.2f' % (image_data['x_beam'], image_data['y_beam']))

        # store the data in image
        self.images.append(image_data)
        self.times[image_data['image_id']] = my_time

        # filter images for time expiry
        for image_metadata in self.images:
            if my_time - self.times[image_metadata['image_id']] > 600:
                self.times.__delitem__(image_metadata['image_id'])
                self.images.remove(image_metadata)

        # figure out pairs
        if 'pair' in image_data['fullname'].lower():
            if len(self.images) > 1:
                if self._is_pair(-1, -2):
                    self._launch_beamcenter()
        else:
            self._launch_beamcenter()


    def _launch_beamcenter(self):
        """
        Prepare for and then launch the beamcenter agent
        """

        #construct the working directory
        my_toplevel_dir = self.secret_settings['toplevel_dir']
        my_typelevel_dir = 'beamcenter'
        my_datelevel_dir = datetime.date.today().isoformat()
        my_work_dir_candidate = os.path.join(my_toplevel_dir, my_typelevel_dir, my_datelevel_dir)
        #make sure this is an original directory
        if os.path.exists(my_work_dir_candidate):
            #we have already
            self.logger.debug('%s has already been used, will add qualifier' % \
                              my_work_dir_candidate)
            for i in range(1, 10000):
                if not os.path.exists('_'.join((my_work_dir_candidate, str(i)))):
                    my_work_dir_candidate = '_'.join((my_work_dir_candidate, str(i)))
                    self.logger.debug('%s will be used for this image' % my_work_dir_candidate)
                    break
                else:
                    i += 1
        #now make the candidate the used dir
        my_work_dir = my_work_dir_candidate

        #package up the images into the format Jon wants
        my_info = {}
        last_key = ''
        for i, image_metadata in enumerate(self.images):
            if i == 0:
                last_key = str(image_metadata['distance'])
                my_info[last_key] = (image_metadata,)
            else:
                if self._is_pair(i-1, i):
                    my_info[last_key] += (image_metadata,)
                else:
                    if my_info.has_key(str(image_metadata['distance'])):
                        for number in range(1, 10000):
                            if not my_info.has_key(str(image_metadata['distance'])+'_'+str(number)):
                                last_key = str(image_metadata['distance'])+'_'+str(number)
                                my_info[last_key] = (image_metadata,)

        #now package directories into a dict for easy access by worker class
        my_dirs_plus = {'work':my_work_dir,
                        'info':my_info}

        #send it off to the cluster
        PerformAction(command=('BEAMCENTER', my_dirs_plus, None, self.settings, self.address),
                      settings=self.settings,
                      secret_settings=self.secret_settings,
                      logger=self.logger)

    def _is_pair(self, i, j):
        """
        Determine if two images are a pair
        """

        pair_image_1 = self.images[i]['fullname']
        pair_image_2 = self.images[j]['fullname']

        #pair is in the name
        if 'pair' in pair_image_1.lower() and 'pair' in pair_image_2.lower():
            #they are not the same name
            if pair_image_1 != pair_image_2:
                #before the image number they are the same
                if pair_image_1[:-8] == pair_image_2[:-8]:
                    #the same distance
                    if self.images[i]['distance'] == self.images[j]['distance']:
                        #different omega angles
                        if self.images[i]['phi'] != self.images[j]['phi']:
                            return True
                        else:
                            return False
                    else:
                        return False
                else:
                    return False
            else:
                return False
        else:
            return False

    def new_beam_center(self, beamcenter_data):
        """Process a new beam center formula from an agent return"""

        pass

    # center calculation methods
    # def get_beam(self, distance):
    #     return (self.get_x_beam(distance), self.get_y_beam(distance))

    # def get_x_beam(self, distance):
    #     """Get the current x beam coordinates"""
    #     return()
    #
    # def get_y_beam(self, distance):
    #     """Get the current y beam coordinates"""
    #     return()

    # database methods
    def get_beam_formula(self):
        """Get the beam center from the database"""

        if self.logger:
            self.logger.debug('get_beam_formula')
        return self.database.getBeamcenter(beamline=self.beamline)

    def put_beam_formula(self, beamcenter_data):
        """Put a beam center formula into the database"""

        return self.database.putBeamcenter(beamcenter_data=beamcenter_data)


#Compute Cluster functions
def checkCluster():
  """
  Quick check run at beginning of pipelines to see if job was subitted to computer cluster node (returns True) or
  run locally (returns False). The pipelines will use this to know whether to subprocess.Process subjobs or submit to
  compute cluster queueing system. This is the master switch for turning on or off a compute cluster.
  """
  import socket
  #Can create a list of names of your compute nodes for checking. Ours all start with 'compute-'.
  if socket.gethostname().startswith('compute-'):
    return(True)
  else:
    return(False)

def checkClusterConn(self):
  """
  Check if execution node can talk to head node through port 536. Used for testing to see if
  subjobs can submit jobs on compute cluster. All nodes should have ability to execute jobs.
  """
  if self.verbose:
    self.logger.debug('Utilities::checkClusterConn')
  try:
    command = 'qping -info gadolinium 536 qmaster 1'
    job = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    for line in job.stdout:
      self.logger.debug(line)

  except:
    self.logger.exception('**ERROR in Utils.checkClusterConn**')

def connectCluster(inp,job=True):
  """
  Used by rapd_agent_beamcenter.py or when a user wants to launch jobs from beamline computer,
  which is not a compute node on cluster, this will login to head node and launch job without
  having them have the login info. Can setup with password or ssh host keys.
  """
  import paramiko
  bc = False
  st = ''
  if job:
    command = 'qsub -j y -terse -cwd -b y '
    command += inp
    print command
    print 'Job ID:'
  else:
    command = inp
  #Use this to say job is beam center calculation.
  if inp.startswith('-pe'):
    bc = True
    #Remove previous beam center results from directory before launching new one.
    st = 'rm -rf bc.log phi*.dat\n'
  client = paramiko.SSHClient()
  client.load_system_host_keys()
  client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
  client.connect(hostname='gadolinium',username='necat')
  stdin,stdout,stderr = client.exec_command('cd %s\n%s%s'%(os.getcwd(),st,command))
  #stdin,stdout,stderr = client.exec_command('cd %s\n%s'%(os.getcwd(),command))
  for line in stdout:
    print line.strip()
    if bc:
      return(line.strip())
  client.close()

def processCluster(self,inp,output=False):
  """
  Submit job to cluster using DRMAA (when you are already on the cluster).
  Main script should not end with os._exit() otherwise running jobs could be orphanned.
  To eliminate this issue, setup self.running = multiprocessing.Event(), self.running.set() in main script,
  then set it to False (self.running.clear()) during postprocess to kill running jobs smoothly.
  """

  #if self.verbose:
    #self.logger.debug('Utilities::processCluster')

  import drmaa,time
  try:
    s = False
    jt = False
    running = True
    log = False
    queue = False
    smp = 1
    name = False
    #Check if self.running is setup... used for Best and Mosflm strategies
    #because you can't kill child processes launched on cluster easily.
    try:
      temp = self.running
    except AttributeError:
      running = False

    if len(inp) == 1:
      command = inp
    elif len(inp) == 2:
      command,log = inp
    elif len(inp) == 3:
      command,log,queue = inp
    elif len(inp) == 4:
      command,log,smp,queue = inp
    else:
      command,log,smp,queue,name = inp
    if queue == False:
      queue = 'all.q'
    #smp,queue,name = inp2
    #'-clear' can be added to the options to eliminate the general.q
    options = '-clear -shell y -p -100 -q %s -pe smp %s'%(queue,smp)
    s = drmaa.Session()
    s.initialize()
    jt = s.createJobTemplate()
    jt.workingDirectory=os.getcwd()
    jt.joinFiles=True
    jt.nativeSpecification=options
    jt.remoteCommand=command.split()[0]
    if len(command.split()) > 1:
      jt.args=command.split()[1:]
    if log:
      #the ':' is required!
      jt.outputPath=':%s'%log
    #submit the job to the cluster and get the job_id returned
    job = s.runJob(jt)
    #return job_id.
    if output:
      output.put(job)

    #cleanup the input script from the RAM.
    s.deleteJobTemplate(jt)

    #If multiprocessing.event is set, then run loop to watch until job or script has finished.
    if running:
      #Returns True if job is still running or False if it is dead. Uses CPU to run loop!!!
      decodestatus = {drmaa.JobState.UNDETERMINED: True,
                      drmaa.JobState.QUEUED_ACTIVE: True,
                      drmaa.JobState.SYSTEM_ON_HOLD: True,
                      drmaa.JobState.USER_ON_HOLD: True,
                      drmaa.JobState.USER_SYSTEM_ON_HOLD: True,
                      drmaa.JobState.RUNNING: True,
                      drmaa.JobState.SYSTEM_SUSPENDED: False,
                      drmaa.JobState.USER_SUSPENDED: False,
                      drmaa.JobState.DONE: False,
                      drmaa.JobState.FAILED: False,
                      }
      #Loop to keep hold process while job is running or ends when self.running event ends.
      while decodestatus[s.jobStatus(job)]:
        if self.running.is_set() == False:
          s.control(job,drmaa.JobControlAction.TERMINATE)
          self.logger.debug('job:%s terminated since script is done'%job)
          break
        #time.sleep(0.2)
        time.sleep(1)
    #Otherwise just wait for it to complete.
    else:
      s.wait(job, drmaa.Session.TIMEOUT_WAIT_FOREVER)
    #Exit cleanly, otherwise master node gets event client timeout errors after 600s.
    s.exit()

  except:
    self.logger.exception('**ERROR in Utils.processCluster**')
    #Cleanup if error.
    if s:
      if jt:
        s.deleteJobTemplate(jt)
      s.exit()
  finally:
    if name!= False:
      self.red.lpush(name,1)

def processClusterSercat(self,inp,output=False):
  """
  Submit job to cluster using DRMAA (when you are already on the cluster).
  Main script should not end with os._exit() otherwise running jobs could be orphanned.
  To eliminate this issue, setup self.running = multiprocessing.Event(), self.running.set() in main script,
  then set it to False (self.running.clear()) during postprocess to kill running jobs smoothly.
  """

  #if self.verbose:
    #self.logger.debug('Utilities::processCluster')

  import drmaa,time
  #try:
  s = False
  jt = False
  running = True
  log = False
  queue = False
  smp = 1
  name = False
  #Check if self.running is setup... used for Best and Mosflm strategies
  #because you can't kill child processes launched on cluster easily.
  try:
    temp = self.running
  except AttributeError:
    running = False

  print inp
  if len(inp) == 1:
    command = inp
  elif len(inp) == 2:
    command,log = inp
  elif len(inp) == 3:
    command,log,queue = inp
  elif len(inp) == 4:
    command,log,smp,queue = inp
  else:
    command,log,smp,queue,name = inp
  if queue == False:
    queue = 'all.q'
  #queues aren't used right now.

  #Setup path
  v = '-v PATH=/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/etc:\
/home/schuerjp/Programs/ccp4-7.0/ccp4-7.0/bin:\
/home/schuerjp/Programs/best:\
/home/schuerjp/Programs/RAPD/bin:\
/home/schuerjp/Programs/RAPD/share/phenix-1.10.1-2155/build/bin:\
/home/schuerjp/Programs/raddose-20-05-09-distribute-noexec/bin:\
/usr/local/bin:/bin:/usr/bin'
  #smp,queue,name = inp2
  #options = '%s -l nodes=1:ppn=%s -S /bin/tcsh'%(v,smp)
  options = '%s -l nodes=1:ppn=%s'%(v,smp)
  s = drmaa.Session()
  s.initialize()
  jt = s.createJobTemplate()
  jt.workingDirectory=os.getcwd()
  jt.joinFiles=True
  jt.nativeSpecification=options
  jt.remoteCommand=command.split()[0]
  if len(command.split()) > 1:
    jt.args=command.split()[1:]
  if log:
    #the ':' is required!
    jt.outputPath=':%s'%os.path.join(os.getcwd(),log)
  #submit the job to the cluster and get the job_id returned
  job = s.runJob(jt)
  #return job_id.
  if output:
    output.put(job)

  #cleanup the input script from the RAM.
  s.deleteJobTemplate(jt)

  #If multiprocessing.event is set, then run loop to watch until job or script has finished.
  if running:
    #Returns True if job is still running or False if it is dead. Uses CPU to run loop!!!
    decodestatus = {drmaa.JobState.UNDETERMINED: True,
                    drmaa.JobState.QUEUED_ACTIVE: True,
                    drmaa.JobState.SYSTEM_ON_HOLD: True,
                    drmaa.JobState.USER_ON_HOLD: True,
                    drmaa.JobState.USER_SYSTEM_ON_HOLD: True,
                    drmaa.JobState.RUNNING: True,
                    drmaa.JobState.SYSTEM_SUSPENDED: False,
                    drmaa.JobState.USER_SUSPENDED: False,
                    drmaa.JobState.DONE: False,
                    drmaa.JobState.FAILED: False,
                    }
    #Loop to keep hold process while job is running or ends when self.running event ends.
    while decodestatus[s.jobStatus(job)]:
      if self.running.is_set() == False:
        s.control(job,drmaa.JobControlAction.TERMINATE)
        self.logger.debug('job:%s terminated since script is done'%job)
        break
      #time.sleep(0.2)
      time.sleep(1)
  #Otherwise just wait for it to complete.
  else:
    s.wait(job, drmaa.Session.TIMEOUT_WAIT_FOREVER)

  #Exit cleanly, otherwise master node gets event client timeout errors after 600s.
  s.exit()
  """
  except:
    self.logger.exception('**ERROR in Utils.processCluster**')
    #Cleanup if error.
    if s:
      if jt:
        s.deleteJobTemplate(jt)
      s.exit()
  finally:
    if name!= False:
      self.red.lpush(name,1)
  """
def killChildrenCluster(self,inp):
  """
  Kill jobs on cluster. The JobID is sent in and job is killed. Must be launched from
  a compute node on the cluster. Used in pipelines to kill jobs when timed out or if
  a solution in Phaser is found in the first round and the second round jobs are not needed.
  """
  import os
  if self.verbose:
    self.logger.debug('Utilities::killChildrenCluster')
  try:
    command = 'qdel %s'%inp
    self.logger.debug(command)
    os.system(command)
  except:
    self.logger.exception('**Could not kill the jobs on the cluster**')

def stillRunningCluster(self,jobid):
  """
  Check to see if process and/or its children and/or children's children are still running. Must
  be launched from compute node.
  """
  import subprocess
  try:
    running = False
    if self.cluster_use:
      command = 'qstat'
    else:
      #command = 'rapd.python /gpfs5/users/necat/rapd/gadolinium/trunk/qstat.py'
      command = 'rapd.python /gpfs6/users/necat/Jon/Programs/CCTBX_x64/modules/rapd/src/qstat.py'
    output = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    for line in output.stdout:
      if len(line.split()) > 0:
        if line.split()[0] == jobid:
          running = True
    return(running)
  except:
    self.logger.exception('**ERROR in Utils.stillRunningCluster**')

if __name__ == '__main__':
    TEST_REMOTE = Remote('E')
    DATA = {'acc_time': '3011',
            'adc': 'slow',
            'adsc_number': '2810',
            'axis': 'phi',
            'beam_center_x': '157.853',
            'beam_center_y': '156.504',
            'beam_size_x': '0.07',
            'beam_size_y': '0.03',
            'beamline': '24_ID_C',
            'bin': '2x2',
            'byte_order': 'little_endian',
            'ccd': 'TH7899',
            'ccd_image_saturation': '65535',
            'collect_mode': 'SNAP',
            'crev': '0',
            'date': '2011-03-20T12:59:44',
            'detector_sn': '911',
            'dim': '2',
            'directory': '/gpfs5/users/GU/Baxter_Mar11/images/CWC/B13',
            'distance': '270.000',
            'flux': '236442000000.0',
            'fullname': '/gpfs5/users/GU/Baxter_Mar11/images/CWC/B13/PPARTB_B13_0_001.img',
            'gauss_x': '0.03',
            'gauss_y': '0.01',
            'header_bytes': ' 1024',
            'image_number': '001',
            'image_pedestal': '40',
            'image_prefix': 'PPARTB_B13',
            'md2_aperture': '70',
            'md2_net_exp': '2231',
            'md2_prg_exp': '1.000000',
            'osc_range': '1.000',
            'osc_start': '0.000',
            'phi': '0.000',
            'pixel_size': '0.10259',
            'puck': 'B',
            'ring_cur': '102.3',
            'ring_mode': '0+24x1, ~1.2% Coupling, Cogging.',
            'run_number': '0',
            'sample': '13',
            'size1': '3072',
            'size2': '3072',
            'thetadistance': '0',
            'time': '1.00',
            'transmission': '7.8814',
            'twotheta': '0.00',
            'twothetadist': '400.00',
            'type': 'unsigned_short',
            'calc_beam_center_x': '1',
            'calc_beam_center_y': '2',
            'unif_ped': '1500',
            'wavelength': '0.97918'}
    #print data
    TEST_REMOTE.add_image(image_metadata=DATA)
