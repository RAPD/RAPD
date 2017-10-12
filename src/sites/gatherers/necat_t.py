#!/usr/bin/env python

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
rapd_adscserver provides an xmlrpclib  server that watches xf_status and
marcollect on an adsc data collection computer to provide information back
to rapd_server via to rapd_adsc

This server is used at 24ID-E with an ADSC Q315 detector

If you are adapting rapd to your locality, you will need to check this 
carefully.
"""
"""
import socket
import os
import threading 
import time
import atexit
import re
import base64
#import redis
#import pysent
import logging, logging.handlers
#from collections import deque
#from SimpleXMLRPCServer import SimpleXMLRPCServer
#import MySQLdb, _mysql_exceptions
"""
# Standard imports
import argparse
import datetime
import importlib
import json
import logging
import logging.handlers
import os
#import pickle
#import shutil
import socket
import sys
import time
import uuid
import redis

# RAPD imports
import utils.commandline
import utils.lock
import utils.log
from utils.overwatch import Registrar
import utils.site
import utils.text as text

# Monitor Beamlines
#
class RedisRunMonitor_OLD():
    """Used by both beamlines"""
    def __init__(self,beamline="C",notify=None,logger=None):
        if logger:
            logger.info('ConsoleRedisMonitor.__init__')

        #init the thread
        threading.Thread.__init__(self)

        self.beamline = beamline
        self.notify = notify
        self.logger = logger

        self.Go = True

        self.current_run   = None
        self.current_dir   = None
        self.current_cpreq = None
        self.current_dpreq = None
        self.cpreqs = []
        self.dpreqs = []

        self.start()

    def run(self):

        if self.logger:
            self.logger.info('ConsoleRedisMonitor.run')

        # Create redis connections
        # Where beamline information is coming from
        redis_database = importlib.import_module('database.rapd_redis_adapter')
        
        bl_database = redis_database.Database(settings=self.site.SITE_ADAPTER_SETTINGS)
        self.bl_redis = bl_database.connect_redis_pool()
        pipe = self.bl_redis.pipeline()

        # Where information will be published to
        #self.pub = BLspec.connect_redis_manager_HA()
        self.pub_database = redis_database.Database(settings=self.site.CONTROL_DATABASE_SETTINGS)
        self.pub = self.pub_database.connect_redis_manager_HA()
        
        # For beamline T
        #self.pubsub = self.pub.pubsub()
        #self.pubsub.subscribe('run_info_T')

        try:
            # Initial check of the db on startup
            run_data = self.pub.hgetall("current_run_"+self.beamline)
            if (run_data):
                # alert the media
                self.pub.publish('newdir:'+self.beamline,self.current_dir)
                # save the info
                self.pub.set('datadir_'+self.beamline,self.current_dir)

            # Main loop
            count = 1
            saved_adsc_state = False
            while(self.Go):

                # Check the redis db for a new run
                if self.beamline == "C":
                    current_run, current_dir, current_adsc_state, test = pipe.get('RUN_INFO_SV').get("ADX_DIRECTORY_SV").get("ADSC_SV").set('RUN_INFO_SV','').execute()
                elif self.beamline == "E":
                    current_run, current_dir, current_adsc_state, test = pipe.get("RUN_INFO_SV").get("EIGER_DIRECTORY_SV").get("EIGER_SV").set('RUN_INFO_SV','').execute()
                elif self.beamline == "T":
                    #current_dir renamed below, but gets rid of error
                    current_dir, current_adsc_state = pipe.get("EIGER_DIRECTORY_SV").get("EIGER_SV").execute()
                    current_run = self.pub.rpop('run_info_T')
                    #print self.pub.llen('run_info_T')
                    #print self.pub.lrange('run_info_T', 0, -1)
                    #current_run = self.pubsub.get_message()['data']
                    #print current_run
                    if current_run == None:
                        current_run = ''
                    
                if (len(current_run) > 0):
                    if self.beamline == "E":
                        self.pub.lpush('run_info_T', current_run)
                        #self.pub.publish('run_info_T', current_run)

                    # Set variable
                    self.current_run = current_run

                    # Split it
                    cur_run = current_run.split("_") #runid,first#,total#,dist,energy,transmission,omega_start,deltaomega,time,timestamp

                    # Arbitrary wait for Console to update Redis database
                    time.sleep(0.01)

                    # Get extra run data
                    extra_data = self.getRunData()
                    
                    if self.beamline == "T":
                        current_dir = "/epu/rdma%s%s_%d_%06d" % (
                                      current_dir,
                                      extra_data['prefix'],
                                      int(cur_run[0]),
                                      int(cur_run[1]))

                    # Compose the run_data object
                    run_data = {'directory'   : current_dir,
                                'prefix'      : extra_data['prefix'],
                                'run_number'  : int(cur_run[0]),
                                'start'       : int(cur_run[1]),
                                'total'       : int(cur_run[2]),
                                'distance'    : float(cur_run[3]),
                                'twotheta'    : extra_data['twotheta'],
                                'phi'         : extra_data['phi'],
                                'kappa'       : extra_data['kappa'],
                                'omega'       : float(cur_run[6]),
                                'axis'        : 'omega',
                                "width"       : float(cur_run[7]),
                                "time"        : float(cur_run[8]),
                                "beamline"    : self.beamline,
                                "file_source" : beamline_settings[self.beamline]['file_source'],
                                "status"      : "STARTED"}

                    # Logging
                    self.logger.info(run_data)

                    #Save data into db
                    self.pub.hmset('current_run_'+self.beamline,run_data)
                    self.pub.publish('current_run_'+self.beamline,json.dumps(run_data))

                    #Signal the main thread
                    if (self.notify):
                        self.notify(("%s RUN" % beamline_settings[self.beamline]['file_source'],run_data))

                # Check if the data collection directory is new
                if (self.current_dir != current_dir):

                    self.logger.debug("New directory")

                    #save the new dir
                    self.current_dir = current_dir

                    #alert the media
                    self.logger.debug("Publish %s %s" % ('newdir:'+self.beamline,self.current_dir))
                    self.pub.publish('newdir:'+self.beamline,self.current_dir)

                    #save the info
                    self.pub.set('datadir_'+self.beamline,current_dir)

                # Watch for run aborting
                if (current_adsc_state == "ABORTED" and current_adsc_state != saved_adsc_state):

                    # Keep track of the detector state
                    saved_adsc_state = current_adsc_state

                    # Alert the media
                    if (self.notify):
                        self.notify(("%s_ABORT" % beamline_settings[self.beamline]['file_source'],None))
                else:
                    saved_adsc_state = current_adsc_state

                """
                #### Turned off, so I dont screw up IDE
                #send test data for rastersnap heartbeat
                if (count % 100 == 0):
                    #reset the counter
                    count = 1

                    # Logging
                    self.logger.info('Publishing filecreate:%s, %s' % (self.beamline, beamline_settings[self.beamline]['rastersnap_test_image']))

                    # Publish the test image
                    self.pub.publish('filecreate:%s'%self.beamline, beamline_settings[self.beamline]['rastersnap_test_image'])

                # Watch the crystal & distl params
                if (count % 60) == 0:
                    try:
                        crystal_request,distl_request,best_request = pipe.get("CP_REQUESTOR_SV").get("DP_REQUESTOR_SV").get("BEST_REQUESTOR_SV").execute()
                        if (distl_request):
                            #if (distl_request != self.current_dpreq):
                            if (distl_request not in self.dpreqs):
                                self.dpreqs.append(distl_request)
                                self.logger.debug(self.dpreqs)
                                self.current_dpreq = distl_request
                                if self.logger:
                                    self.logger.debug('ConsoleRedisMonitor New distl parameters request for %s' % distl_request)
                                if (self.notify):
                                    self.notify(("DISTL_PARMS_REQUEST",distl_request))
                        if (crystal_request):
                            #if (crystal_request != self.current_cpreq):
                            if (crystal_request not in self.cpreqs):
                                self.cpreqs.append(crystal_request)
                                self.current_cpreq = crystal_request
                                if self.logger:
                                    self.logger.debug('ConsoleRedisMonitor New crystal parameters request for %s' % crystal_request)
                                if (self.notify):
                                    self.notify(("CRYSTAL_PARMS_REQUEST",crystal_request))
                        if (best_request):
                            if (best_request != self.current_breq):
                                self.current_breq = best_request
                                if self.logger:
                                    self.logger.debug('ConsoleRedisMonitor New best parameters request')
                                if (self.notify):
                                    self.notify(("BEST_PARMS_REQUEST",best_request))
                    except:
                      self.logger.debug('ConsoleRedisMonitor Exception in querying for tracker requests')
                """
                # Increment the counter
                count += 1

                # Sleep before checking again
                time.sleep(0.1)


        except redis.exceptions.ConnectionError:
            if self.logger:
                self.logger.debug('ConsoleRedisMonitor failure to connect - will reconnect')
            time.sleep(10)
            reconnect_counter = 0
            while (reconnect_counter < 1000):
                try:
                    try:
                        self.red.ping()
                    except:
                        self.red = redis.Redis(beamline_settings[self.beamline]['redis_ip'])

                    try:
                        self.pub.ping()
                    except:
                        """
                        #self.pub = redis.Redis(beamline_settings[self.beamline]['remote_redis_ip'])
                        self.pub = pysent.RedisManager(sentinel_host="remote.nec.aps.anl.gov",
                                sentinel_port=26379,
                                master_name="remote_master")
                        """
                        self.pub = BLspec.connect_redis_manager_HA()

                    #test connections
                    self.red.ping()

                    if self.logger:
                        self.logger.debug('Reconnection to redis server successful')
                    break

                except:
                    reconnect_counter += 1
                    if self.logger:
                        self.logger.debug('Reconnection attempt %d failed, will try again' % reconnect_counter)
                    time.sleep(10)


    def getRunData(self):
        """
        Get the extra information for a run from the redis db
        """
        self.logger.info("getRunData")

        pipe = self.red.pipeline()
        pipe.get("DETECTOR_SV")
        #pipe.get({"C": "ADX_DIRECTORY_SV", "E": "EIGER_DIRECTORY_SV"}[self.beamline])
        pipe.get({"C": "ADX_DIRECTORY_SV", "E": "EIGER_DIRECTORY_SV", "T": "EIGER_DIRECTORY_SV"}[self.beamline]) # not used!!
        pipe.get("RUN_PREFIX_SV")
        pipe.get("DET_THETA_SV")        #two theta
        pipe.get("MD2_ALL_AXES_SV")     #for kappa and phi
        return_array = pipe.execute()

        # To handle E beamline "_5.1053_-_-" &
        #           C beamline" 183.1158    0.0000    0.0000"
        try:
            if '_' in return_array[4]:
                #print return_array[4]
                axes = [return_array[4].split('_')[1],'0','0']
            else:
                axes = return_array[4].split()
        except:
            pass

        if self.beamline == 'C':
            my_dict = {"detector"  : return_array[0],
                       "directory" : os.path.join(return_array[1],"0_0"),
                       "prefix"    : return_array[2],
                       "twotheta"  : float(return_array[3]),
                       "kappa"     : float(axes[1]),
                       "phi"       : float(axes[2])}
        elif self.beamline == 'E':
            my_dict = {"detector"  : return_array[0],
                       "directory" : return_array[1],
                       "prefix"    : return_array[2],
                       "twotheta"  : float(return_array[3]),
                       "kappa"     : 0.0,
                       "phi"       : 0.0}
        elif self.beamline == 'T':
            my_dict = {"detector"  : return_array[0],
                       #"directory" : os.path.join('/epu/rdma', return_array[1]),
                       "directory" : '%s%s'%('/epu/rdma', return_array[1]), #not used anyway
                       "prefix"    : return_array[2],
                       "twotheta"  : float(return_array[3]),
                       "kappa"     : 0.0,
                       "phi"       : 0.0}

        return(my_dict)

    def Stop(self):
        """
        Used to stop the loop
        """
        self.logger.debug('ConsoleRedisMonitor.Stop')

        self.Go = False
        # Added for T
        #if self.beamline == 'T':
        #    self.pubsub.unsubscribe()

class Gatherer(object):
    """
    Watches the beamline and signals images and runs over redis
    """

    # For keeping track of file change times
    run_time = 0
    image_time = 0

    # Host computer detail
    ip_address = None

    def __init__(self, site, overwatch_id=None):
        """
        Setup and start the NecatGatherer
        """

        # Get the logger Instance
        self.logger = logging.getLogger("RAPDLogger")

        # Passed-in variables
        self.site = site
        self.overwatch_id = overwatch_id

        self.logger.info("NecatGatherer.__init__")

        # Connect to redis
        self.connect()

        # Get our bearings
        self.set_host()

        # Running conditions
        self.go = True

        # Now run
        self.run()

    def run(self):
        """
        The while loop for watching the files
        """
        self.logger.info("NecatGatherer.run")

        # Set up overwatcher
        self.ow_registrar = Registrar(site=self.site,
                                      ow_type="gatherer",
                                      ow_id=self.overwatch_id)
        self.ow_registrar.register({"site_id":self.site.ID})

        # Get redis connection

        #self.logger.debug("  Will publish new images on filecreate:%s" % self.tag)
        #self.logger.debug("  Will push new images onto images_collected:%s" % self.tag)
        self.logger.debug("  Will publish new datasets on run_data:%s" % self.tag)
        self.logger.debug("  Will push new datasets onto run_data:%s" % self.tag)
        
        try:
            while self.go:
    
                # 5 rounds of checking
                #for ___ in range(5):
    
                # Check if the run info changed in beamline Redis DB.
                #current_run = self.bl_redis.get("RUN_INFO_SV")
                current_run = self.redis.rpop('run_info_T')
                if current_run not in (None, ""):
                    # Split it
                    #cur_run = current_run.split("_") #runid,first#,total#,dist,energy,transmission,omega_start,deltaomega,time,timestamp
                    #1_1_23_400.00_12661.90_30.00_45.12_0.20_0.50_
                    # Reset it back to an empty string if beamline is E.
                    #self.bl_redis.set("RUN_INFO_SV", "")
                    # get the additional beamline params and put into nice dict.
                    run_data = self.get_run_data(current_run)
                    # Get rid of trailing slash from beamline Redis.
                    dir = run_data['directory']
                    if dir[-1] == '/':
                        run_data['directory'] = dir[:-1]
                    
                    self.logger.debug("run_data:%s %s", self.tag, run_data)
                    # Put into exchangable format
                    run_data_json = json.dumps(run_data)
                    # Publish to Redis
                    self.redis.publish("run_data:%s" % self.tag, run_data_json)
                    # Push onto redis list in case no one is currently listening
                    self.redis.lpush("run_data:%s" % self.tag, run_data_json)
                        
                    """
                    if self.check_for_run_info():
                        run_data = self.get_run_data()
                        if run_data:
                            self.logger.debug("run_data:%s %s", self.tag, run_data)
                            # Put into exchangable format
                            run_data_json = json.dumps(run_data)
                            # Publish to Redis
                            red.publish("run_data:%s" % self.tag, run_data_json)
                            # Push onto redis list in case no one is currently listening
                            red.lpush("run_data:%s" % self.tag, run_data_json)
                    
                    # 20 image checks
                    for __ in range(20):
                        # Check if the image file has changed
                        if self.check_for_image_collected():
                            image_name = self.get_image_data()
                            if image_name:
                                self.logger.debug("image_collected:%s %s",
                                                  self.tag,
                                                  image_name)
                                # Publish to Redis
                                red.publish("image_collected:%s" % self.tag, image_name)
                                # Push onto redis list in case no one is currently listening
                                red.lpush("images_collected:%s" % self.tag, image_name)
                            break
                        else:
                            time.sleep(0.05)
                    """
                time.sleep(0.1)
                # Have Registrar update status
                self.ow_registrar.update({"site_id":self.site.ID})
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """
        Stop the loop
        """
        self.logger.debug("NecatGatherer.stop")

        #self.go = False
        self.redis_database.stop()
        self.bl_database.stop()

    def connect(self):
        """Connect to redis host"""
        # Connect to control redis for publishing run data info
        redis_database = importlib.import_module('database.rapd_redis_adapter')
        
        self.redis_database = redis_database.Database(settings=self.site.CONTROL_DATABASE_SETTINGS)
        self.redis = self.redis_database.connect_to_redis()

        # Connect to beamline Redis to monitor if run is launched
        self.bl_database = redis_database.Database(settings=self.site.SITE_ADAPTER_SETTINGS)
        self.bl_redis = self.bl_database.connect_redis_pool()
        #pipe = self.bl_redis.pipeline()

    def set_host(self):
        """
        Use os.uname to set files to watch
        """
        self.logger.debug("NecatGatherer.set_host")

        # Figure out which host we are on
        self.ip_address = socket.gethostbyaddr(socket.gethostname())[-1][0]
        self.logger.debug(self.ip_address)

        # Now grab the file locations, beamline from settings
        if self.site.GATHERERS.has_key(self.ip_address):
            #self.image_data_file, self.run_data_file, self.tag = self.site.GATHERERS[self.ip_address]
            self.tag = self.site.GATHERERS[self.ip_address]
            # Make sure we enforce uppercase for tag
            self.tag = self.tag.upper()
        else:
            print "ERROR - no settings for this host"
            self.tag = "test"
            # sys.exit(9)

    def get_run_data(self, run_info):
        """Put together info from run and pass it back."""
        # Split it
        cur_run = run_info.split("_") #runnumber,first#,total#,dist,energy,transmission,omega_start,deltaomega,time,timestamp
        
        pipe = self.bl_redis.pipeline()
        #pipe.get("DETECTOR_SV")
        pipe.get("EIGER_DIRECTORY_SV")
        pipe.get("RUN_PREFIX_SV")
        #pipe.get("DET_THETA_SV")        #two theta
        #pipe.get("MD2_ALL_AXES_SV")     #for kappa and phi
        return_array = pipe.execute()
        
        """
        run_data = {'directory'   : current_dir,
                                'prefix'      : extra_data['prefix'],
                                'run_number'  : int(cur_run[0]),
                                'start'       : int(cur_run[1]),
                                'total'       : int(cur_run[2]),
                                'distance'    : float(cur_run[3]),
                                'twotheta'    : extra_data['twotheta'],
                                'phi'         : extra_data['phi'],
                                'kappa'       : extra_data['kappa'],
                                'omega'       : float(cur_run[6]),
                                'axis'        : 'omega',
                                "width"       : float(cur_run[7]),
                                "time"        : float(cur_run[8]),
                                "beamline"    : self.beamline,
                                "file_source" : beamline_settings[self.beamline]['file_source'],
                                "status"      : "STARTED"}
        """
        # Standardize the run information
        run_data = {
            "anomalous":None,
            "beamline":self.tag,                                # Non-standard
            #"beam_size_x":float(raw_run_data.get("beamsize", 0.0)),     # Non-standard
            #"beam_size_y":float(raw_run_data.get("beamsize", 0.0)),     # Non-standard
            "directory":return_array[0],
            "distance":float(cur_run[3]),
            "energy":float(cur_run[4]),
            #"file_ctime":datetime.datetime.fromtimestamp(self.run_time).isoformat(),
            "image_prefix":return_array[1],
            "kappa":None,
            "number_images":int(cur_run[2]),
            "omega":None,
            "osc_axis":"phi",
            "osc_start":float(cur_run[6]),
            "osc_width":float(cur_run[7]),
            "phi": 0.0,
            "run_number":int(cur_run[0]),
            "site_tag":self.tag,
            "start_image_number":int(cur_run[1]),
            "time":float(cur_run[8]),
            "transmission":float(cur_run[5]),
            "twotheta":None
        }

        return run_data

    def get_run_data_OLD(self):
        """
        Return contents of run data file
        """

        if self.run_data_file:

            # Copy the file to prevent conflicts with other programs
            # Use the ramdisk if it is available
            if os.path.exists("/dev/shm"):
                tmp_dir = "/dev/shm/"
            else:
                tmp_dir = "/tmp/"

            tmp_file = tmp_dir+uuid.uuid4().hex
            shutil.copyfile(self.run_data_file, tmp_file)

            # Read in the pickled file
            f = open(tmp_file, "rb")
            raw_run_data = pickle.load(f)
            f.close()
            self.logger.debug(raw_run_data)

            # Remove the temporary file
            os.unlink(tmp_file)

            # Standardize the run information
            """
            The current fields saved into the sql datbase adapter are:
                directory,
                image_prefix,
                run_number,
                start_image_number,
                number_images,
                distance,
                phi,
                kappa,
                omega,
                osc_axis,
                osc_start,
                osc_width,
                time,
                transmission,
                energy,
                anomalous
            """
            run_data = {
                "anomalous":None,
                "beamline":raw_run_data.get("beamline", None),              # Non-standard
                "beam_size_x":float(raw_run_data.get("beamsize", 0.0)),     # Non-standard
                "beam_size_y":float(raw_run_data.get("beamsize", 0.0)),     # Non-standard
                "directory":raw_run_data.get("directory", None),
                "distance":float(raw_run_data.get("dist", 0.0)),
                "energy":float(raw_run_data.get("energy", 0.0)),
                "file_ctime":datetime.datetime.fromtimestamp(self.run_time).isoformat(),
                "image_prefix":raw_run_data.get("image_prefix", None),
                "kappa":None,
                "number_images":int(float(raw_run_data.get("Nframes", 0))),
                "omega":None,
                "osc_axis":"phi",
                "osc_start":float(raw_run_data.get("start", 0.0)),
                "osc_width":float(raw_run_data.get("width", 0.0)),
                "phi":float(raw_run_data.get("start", 0.0)),
                "run_number":None,
                "site_tag":self.tag,
                "start_image_number":int(float(raw_run_data.get("first_image", 0))),
                "time":float(raw_run_data.get("time", 0.0)),
                "transmission":float(raw_run_data.get("trans", 0.0)),
                "twotheta":None
            }

        else:
            run_data = False

        return run_data

def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """Data gatherer for NECAT T beamline"""
    parser = argparse.ArgumentParser(parents=[utils.commandline.base_parser],
                                     description=commandline_description)

    return parser.parse_args()

def main():
    """ The main process
    Setup logging and instantiate the gatherer"""

    # Get the commandline args
    commandline_args = get_commandline()

    # Get the environmental variables
    environmental_vars = utils.site.get_environmental_variables()

    site = commandline_args.site

    # If no commandline site, look to environmental args
    if site == None:
        if environmental_vars["RAPD_SITE"]:
            site = environmental_vars["RAPD_SITE"]

    # Determine the site
    site_file = utils.site.determine_site(site_arg=site)

    # Handle no site file
    if site_file == False:
        print text.error+"Could not determine a site file. Exiting."+text.stop
        sys.exit(9)

    # Import the site settings
    SITE = importlib.import_module(site_file)

  # Single process lock?
    utils.lock.file_lock(SITE.GATHERER_LOCK_FILE)

    # Set up logging
    if commandline_args.verbose:
        log_level = 10
    else:
        log_level = SITE.LOG_LEVEL
    logger = utils.log.get_logger(logfile_dir=SITE.LOGFILE_DIR,
                                  logfile_id="rapd_gatherer",
                                  #level=log_level
                                  )

    logger.debug("Commandline arguments:")
    for pair in commandline_args._get_kwargs():
        logger.debug("  arg:%s  val:%s" % pair)

    # Instantiate the Gatherer
    GATHERER = Gatherer(site=SITE,
                        overwatch_id=commandline_args.overwatch_id)

if __name__ == '__main__':

    main()
