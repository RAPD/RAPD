"""
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

__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

"""
rapd_console provides a connection to the beamline control systems at NECAT
"""

import os
import sys
import threading
import time
import json
import atexit
import logging, logging.handlers
from collections import deque
import redis
import pysent
from rapd_site import secret_settings as beamline_settings


class ConsoleFeeder(threading.Thread):
    def __init__(self,mode="DISTL_PARMS_REQUEST",db=None,bc=None,data=None,notify=None,logger=None):
        if logger:
            logger.debug("ConsoleFeeder.__init__")

        threading.Thread.__init__(self)

        self.mode = mode
        self.DATABASE = db
        self.BEAMLINE_CONNECTION = bc
        self.data = data
        self.logger = logger

        self.start()

    def run(self):
        if (self.mode == "DISTL_PARMS_REQUEST"):
            self.logger.debug("ConsoleFeeder DISTL_PARMS_REQUEST")
            counter = 0
            while (counter < 5):
                data = self.DATABASE.getResultsByFullname(fullname=self.data,type="single")
                if (data):
                    self.BEAMLINE_CONNECTION.putDistlParams(data)
                    break
                else:
                    self.logger.debug("Image not yet present %d" % counter)
                    counter += 1
                    time.sleep(60)

        elif (self.mode == "CRYSTAL_PARMS_REQUEST"):
            self.logger.debug("ConsoleFeeder CRYSTAL_PARMS_REQUEST")
            counter = 0
            while (counter < 5):
                data = self.DATABASE.getResultsByFullname(fullname=self.data,type="single")
                if (data):
                    self.BEAMLINE_CONNECTION.putCrystalParams(data)
                    break
                else:
                    self.logger.debug("Image not yet present %d" % counter)
                    counter += 1
                    time.sleep(60)

        elif (self.mode == "BEST_PARMS_REQUEST"):
            self.logger.debug("ConsoleFeeder BEST_PARMS_REQUEST")
            counter = 0
            while (counter < 5):
                data = self.DATABASE.getResultsByFullname(fullname=self.data,type="strategy")
                if (data):
                    self.BEAMLINE_CONNECTION.putStrategyParams(data)
                    break
                else:
                    self.logger.debug("Image not yet present %d" % counter)
                    counter += 1

#
# Monitor Beamlines
#
class ConsoleRedisMonitor(threading.Thread):
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

        #create redis connections
        # print beamline_settings[self.beamline]
        self.red = redis.Redis(beamline_settings[self.beamline]['redis_ip'])
        #self.pub = redis.Redis(beamline_settings[self.beamline]['remote_redis_ip'])
        self.pub = pysent.RedisManager(sentinel_host="remote.nec.aps.anl.gov",
                                  sentinel_port=26379,
                                  master_name="remote_master")
        pipe = self.red.pipeline()

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

                # self.logger.info('ConsoleRedisMonitor.running %d' % count)

                # check the redis db for a new run
                current_run,current_dir,current_adsc_state,test = pipe.get('RUN_INFO_SV').get("ADX_DIRECTORY_SV").get("ADSC_SV").set('RUN_INFO_SV','').execute()
                if (len(current_run) > 0):

                    # Set variable
                    self.current_run = current_run

                    # Split it
                    cur_run = current_run.split("_") #runid,first#,total#,dist,energy,transmission,omega_start,deltaomega,time,timestamp

                    # Arbitrary wait for Console to update Redis database
                    time.sleep(0.01)

                    # Get extra run data
                    extra_data = self.getRunData()

                    # Compose the run_data object
                    run_data = {'directory'   : extra_data['directory'],
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

                #send test data for rastersnap heartbeat
                if (count % 100 == 0):
                    #reset the counter
                    count = 1

                    # Logging
                    self.logger.info('Publishing filecreate:%s, %s' % (self.beamline, beamline_settings[self.beamline]['rastersnap_test_image']))

                    # Publish the test image
                    self.pub.publish('filecreate:%s'%self.beamline, beamline_settings[self.beamline]['rastersnap_test_image'])

                #watch the crystal & distl params
                if (count % 60 == 0):
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
                #increment the counter
                count += 1
                #sleep before checking again
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
                        self.pub = redis.Redis(beamline_settings[self.beamline]['remote_redis_ip'])
                        self.pub = pysent.RedisManager(sentinel_host="remote.nec.aps.anl.gov",
            									  sentinel_port=26379,
            									  master_name="remote_master")

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
        pipe.get("ADX_DIRECTORY_SV")
        pipe.get("RUN_PREFIX_SV")
        pipe.get("DET_THETA_SV")        #two theta
        pipe.get("MD2_ALL_AXES_SV")     #for kappa and phi
        return_array = pipe.execute()

        # To handle E beamline "_5.1053_-_-" &
        #           C beamline" 183.1158    0.0000    0.0000"
        try:
            if '_' in return_array[4]:
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
                       "kappa"     : float(axes[1]),
                       "phi"       : float(axes[2])}


        #print my_dict
        return(my_dict)

    def Stop(self):
        """
        Used to stop the loop
        """
        self.logger.debug('ConsoleRedisMonitor.Stop')

        self.Go = False

class ConsoleRunMonitor(threading.Thread):
    """
    Start a new thread which looks for changes to the file describing runs
    started from Console
    """
    def __init__(self,beamline='C',notify=None,reconnect=None,logger=None):
        logger.info('Console_Run_Monitor')

        #init the thread
        threading.Thread.__init__(self)

        self.beamline = beamline
        self.notify = notify
        self.reconnect = reconnect
        self.logger = logger

        #self.remotePool = redis.ConnectionPool(beamline_settings[self.beamline]['remote_redis_ip'])
        #self.pub = redis.Redis(beamline_settings[self.beamline]['remote_redis_ip'])
        self.pub = pysent.RedisManager(sentinel_host="remote.nec.aps.anl.gov",
                                  sentinel_port=26379,
                                  master_name="remote_master")
        #location of file to be checked
        try:
            self.marcollect = beamline_settings[beamline]['console_marcollect']
        except:
            self.logger.exception('Error in ConsoleRunMonitor::__init__')
            return

        #for keeping track of file change times
        self.mar_time = 0

        #running conditions
        self.Go = True
        atexit.register(self.Stop)

        #now run
        self.start()

    def run(self):
        """
        The while loop for watching the files
        """
        self.logger.info('Console_Run_Monitor::run')
        try:
            count = 0
            while(self.Go):
                if self.CheckMarcollect():
                    mlines  = self.GetMarcollect()
                    mparsed = self.ParseMarcollect(mlines)
                    if mparsed:
                        if self.notify:
                            self.notify(("CONSOLE RUN STATUS CHANGED", mparsed))
                #The count == 0 section is for providing a heartbeat function for console to know image analysis is functioning
                if (count == 0):
                    count += 1
                    # publish the test image
                    self.logger.info('Publishing filecreate:%s, %s' % (self.beamline,beamline_settings[self.beamline]['rastersnap_test_image']))
                    self.pub.publish('filecreate:%s'%self.beamline, beamline_settings[self.beamline]['rastersnap_test_image'])
                    """
                    if self.notify:
                        self.notify(("IMAGE STATUS CHANGED", {'status': 'SUCCESS', 'image_prefix': 'raster_snap_test', 'run_number': '1', 'image_name': beamline_settings[self.beamline]['rastersnap_test_image'], 'directory': os.path.dirname(beamline_settings[self.beamline]['rastersnap_test_image']), 'adsc_number': '1', 'image_number': '001'}))
                    """
                else:
                    count += 1
                    if (count == 10):
                        count = 0
                    time.sleep(1.0)
        except:
            self.logger.exception('Exception in main while loop of Console_Run_Monitor')
            time.sleep(10)
            self.run()

    def Stop(self):
        """
        Used to stop the loop
        """
        self.logger.debug('Console_Run_Monitor::Stop')

        self.Go = False

    def CheckMarcollect(self):
        """
        return True if marcollect has been changed, False if not
        """
        # self.logger.debug('CheckMarcollect %s' % str(self.mar_time))
        tries = 0
        while (tries < 5):
            try:
                statinfo = os.stat(self.marcollect)
                break
            except:
                if tries == 4:
                    return(False)
                tries += 1

        #the modification time has not changed
        if (self.mar_time == statinfo.st_mtime):
            return(False)
        #the file has changed
        else:
            self.mar_time = statinfo.st_mtime
            return(True)

    def GetMarcollect(self):
        """
        return contents of marcollect
        """
        self.logger.debug('Console_Run_Monitor::GetMarcollect')
        #copy the file to prevent conflicts with other programs
        os.system('cp '+self.marcollect+' /tmp/tmp_marcollect')
        #read in the lines of the file
        in_lines = open(self.marcollect,'r').readlines()
        #remove the temporary file
        os.system('rm -f /tmp/tmp_marcollect')
        return(in_lines)

    def ParseMarcollect(self,lines):
        """
        Parse the lines from the Console-generated file id_[c/e]_marcollect and return a dict that
        is somewhat intelligible
        """
        self.logger.debug('Console_Run_Monitor::ParseMarcollect')
        #self.logger.debug(lines)

        marcollect_items = ('beamline',
                            'connect',
                            'collect',
                            'distance',
                            'lift',
                            'mode',
                            'phi_start',
                            'kappa_start',
                            'omega_start',
                            'axis',
                            'wavelength',
                            'osc_width',
                            'n_images',
                            'image_number',
                            'de_zinger',
                            'directory',
                            'image_prefix',
                            'image_suffix',
                            'adc',
                            'bin',
                            'outfile_type',
                            'output_raw',
                            'no_transform',
                            'center',
                            'dk_before_run',
                            'repeat_dark',
                            'compress')

        try:
            out_dict = {}
            for i,line in enumerate(lines):
                sline = line.split()
                #Now put information into a dict - try to use standard format
                if (len(sline)>1):
                    out_dict[sline[0]] = sline[1]

            """
            {'directory'   : extra_data['directory'],    XX
            'prefix'      : extra_data['prefix'],        XX
            'run_number'  : int(cur_run[0]),             XX
            'start'       : int(cur_run[1]),             XX
            'total'       : int(cur_run[2]),             XX
            'distance'    : float(cur_run[3]),           XX
            'twotheta'    : extra_data['twotheta'],
            'phi'         : extra_data['phi'],           XX
            'kappa'       : extra_data['kappa'],         XX
            'omega'       : float(cur_run[6]),           XX
            'axis'        : 'omega',                     XX
            "width"       : float(cur_run[7]),           XX
            "time"        : float(cur_run[8]),           XX
            "beamline"    : self.beamline,               XX
            "file_source" : "PILATUS",                   XX
            "status"      : "STARTED"}                   XX
            """
            """
            beamline id_e
            connect remote_command
            collect
            distance 1000.0000
            lift 0.0000
            mode time
            time 1.0000
            phi_start 1.0000
            kappa_start 0.0000
            omega_start 0.0000
            axis phi
            wavelength 0.979184
            osc_width 1.0000
            n_images 40
            image_number 1
            de_zinger 0
            directory /gpfs5/users/GU/Dunham_Feb12/images/junk/
            image_prefix testdata_7
            image_suffix img
            adc 0
            bin 1
            outfile_type 0
            output_raw 0
            no_transform 0
            center 157.000000 157.000000
            dk_before_run 1
            repeat_dark 0
            compress none
            eoc
            """
            out_dict.update({"directory"   : out_dict["directory"].rstrip('/'),
                             "prefix"      : "_".join(out_dict["image_prefix"].split("_")[0:-1]),
                             "run_number"  : int(out_dict["image_prefix"].split("_")[-1]),
                             "start"       : int(out_dict["image_number"]),
                             "total"       : int(out_dict["n_images"]),
                             "phi"         : float(out_dict["phi_start"]),
                             "kappa"       : float(out_dict.get("kappa_start",0)),
                             "omega"       : float(out_dict["phi_start"]),
                             "axis"        : "omega",
                             "width"       : float(out_dict["osc_width"]),
                             "time"        : float(out_dict["time"]),
                             "beamline"    : out_dict["beamline"][-1].upper(),
                             "file_source" : "CONSOLE",
                             "status"      : "STARTED"})

            #self.logger.debug("Resulting dict")
            #self.logger.debug(out_dict)
            return(out_dict)

        except:
            self.logger.exception('Failure to parse marcollect - error in format?')
            return(False)

class ConsoleRedisMonitor2(threading.Thread):
    """Used by E beamline"""
    def __init__(self,beamline="E",notify=None,logger=None):
        if logger:
            logger.info('ConsoleRedisMonitor2.__init__')

        #init the thread
        threading.Thread.__init__(self)

        self.beamline = beamline
        self.notify = notify
        self.logger = logger

        self.Go = True

        self.current_cpreq = None
        self.current_dpreq = None
        self.current_breq  = None

        # Redis pools
        #self.consolePool = redis.ConnectionPool(beamline_settings[self.beamline]['redis_ip'])
        self.red = redis.Redis(beamline_settings[self.beamline]['redis_ip'])
        self.pipe = self.red.pipeline()
        self.start()

    def run(self):
        if self.logger:
            self.logger.info('ConsoleRedisMonitor2.run')

        #main loop
        count = 0
        red = redis.Redis(beamline_settings[self.beamline]['redis_ip'])

        while(self.Go):
            try:
                #watch the crystal & distl params
                crystal_request = red.get("CP_REQUESTOR_SV")
                distl_request = red.get("DP_REQUESTOR_SV")
                best_request = red.get("BEST_REQUESTOR_SV")

                if (distl_request):
                        if (distl_request != self.current_dpreq):
                            self.current_dpreq = distl_request
                            if self.logger:
                                self.logger.debug("ConsoleRedisMonitor New distl parameters request")
                            if (self.notify):
                                self.notify(("DISTL_PARMS_REQUEST",distl_request))
                if (crystal_request):
                    if (crystal_request != self.current_cpreq):
                        self.current_cpreq = crystal_request
                        if self.logger:
                            self.logger.debug('ConsoleRedisMonitor New crystal parameters request')
                        if (self.notify):
                            self.notify(("CRYSTAL_PARMS_REQUEST",crystal_request))
                if (best_request):
                    if best_request != self.current_breq:
                        self.current_breq = best_request
                        if self.logger:
                            self.logger.debug('ConsoleRedisMonitor New best parameters request')
                        if (self.notify):
                            self.notify(("BEST_PARMS_REQUEST",best_request))
            except redis.exceptions.ConnectionError:
                if self.logger:
                    self.logger.debug('ConsoleRedisMonitor failure to connect - will reconnect')
                time.sleep(10)
                reconnect_counter = 0
                while (reconnect_counter < 1000):
                    try:
                        #self.consolePool = redis.ConnectionPool(beamline_settings[self.beamline]['redis_ip'])
                        self.red = redis.Redis(beamline_settings[self.beamline]['redis_ip'])
                        self.red.ping()
                        if self.logger:
                            self.logger.debug('Reconnection to redis server successful')
                        break
                    except:
                        reconnect_counter += 1
                        if self.logger:
                            self.logger.debug('Reconnection attempt %d failed, will try again' % reconnect_counter)
                        time.sleep(10)

            #sleep before checking again
            time.sleep(3)

    def getRunData(self):
        """
        Get the extra information for a run from the redis db
        """
        #print "getRunData"

        pipe = self.red.pipeline()
        pipe.get("DETECTOR_SV")
        pipe.get("ADX_DIRECTORY_SV")
        pipe.get("RUN_PREFIX_SV")
        pipe.get("DET_THETA_SV")        #two theta
        pipe.get("MD2_ALL_AXES_SV")     #for kappa and phi
        return_array = pipe.execute()
        axes = return_array[4].split()

        my_dict = {"detector"  : return_array[0],
                   "directory" : os.path.join(return_array[1],"0_0"),
                   "prefix"    : return_array[2],
                   "twotheta"  : float(return_array[3]),
                   "kappa"     : float(axes[1]),
                   "phi"       : float(axes[2])}

        #print my_dict
        return(my_dict)

    def Stop(self):
        """
        Used to stop the loop
        """
        self.logger.debug('ConsoleRedisMonitor.Stop')

        self.Go = False

class ConsoleConnect:
    """
    Provides a connection to the Redis database used to communicate to Console
    """
    def __init__(self,beamline='C',logger=False):
        if (logger):
            logger.info('ConsoleConnect::__init__')

        #passed-in variables
        self.logger    = logger
        self.beamline  = beamline
        self.logger    = logger

    def getRedisConnection(self):
        """
        Returns a connection to the Redis database
        """
        return(redis.Redis(beamline_settings[self.beamline]['redis_ip']))

    #
    # Put methods
    #
    def putDistlParams(self,data):
        """
        Place requested data into Redis database
        """
        self.logger.debug('ConsoleConnect.putDistlParams')

        #open connection
        r = self.getRedisConnection()

        #construct data string
        data_string = "_".join((data["basename"].replace("_","="),
                                str(data["distl_res"]),
                                str(data["distl_labelit_res"]),
                                str(data["distl_overloads"]),
                                str(data["distl_total_spots"]),
                                str(data["distl_good_bragg_spots"]),
                                str(data["distl_spots_in_res"]),
                                str(data["distl_max_signal_strength"]),
                                str(data["distl_mean_int_signal"]),
                                str(data["distl_min_signal_strength"])))

        #put the data in
        pipe = r.pipeline()
        pipe.set("DISTL_PARMS_SV",data_string).set('DP_REQUESTOR_SV','').execute()
        del(pipe)
        self.logger.debug("%s Sent to Console in Distl" % data_string)

    def putCrystalParams(self,data):
        """
        Place requested data into Redis database
        """
        self.logger.debug('ConsoleConnect.putCrystalParams')

        #open connection
        r = self.getRedisConnection()

        #construct data string
        data_string = "_".join((data["basename"].replace("_","="),
                                str(data['labelit_a']),
                                str(data['labelit_b']),
                                str(data['labelit_c']),
                                str(data['labelit_alpha']),
                                str(data['labelit_beta']),
                                str(data['labelit_gamma']),
                                str(data['labelit_spacegroup'])))

        #put the data in
        pipe = r.pipeline()
        pipe.set("CRYSTAL_PARMS_SV",data_string).set("CP_REQUESTOR_SV","").execute()
        del(pipe)
        self.logger.debug("%s Sent to Console in Crystal" % data_string)

    def putStrategyParams(self,data):
        """
        Place requested data into Redis database
        """
        self.logger.debug('ConsoleConnect.putStrategyParams')

        #open connection
        r = self.getRedisConnection()

        #construct data string
        data_string = "_".join((str(data['phi_start']),
                               str(data['delta_phi']),
                               str(data['number_images']),
                               str(data['exposure_time']),
                               str(data['distance']),
                               str(data['best_norm_atten'])))

        #put the data in
        pipe = r.pipeline()
        pipe.set("BEST_PARMS_SV",data_string).set("CP_REQUESTOR_SV","").execute()
        del(pipe)

    def PutStac(self,timestamp='08/30/2010_14:13',omega=3.14,kappa=150.9,phi=26.5,width=90):
        """
        Sets the MK3 minikappa
            timestamp is format 08/26/2010_13:53
            omega
            kappa
            phi
            width (presumably of a collection wedge, but that's not really what we are doing)
        """
        self.logger.debug('ConsoleConnect.PutStac\n %s omega: %f kappa:%f phi:%f' % (timestamp,omega,kappa,phi))
        #Open Redis connection
        #r = redis.Redis(beamline_settings[self.beamline]['redis_ip'])
        r = self.getRedisConnection()
        #Update the date of the setting
        r.set('STAC_PRED_TS_SV',timestamp)
        #Update the setting
        r.set('STAC_PRED_SV','_'.join((str(omega),str(kappa),str(phi),str(width))))

    def PutDatacollection(self,timestamp='2010/08/30_14:13',omega_start=3.14,delta_omega=1.0,number_images=90,time=1.0,distance=450.0,transmission=7.0,kappa=150.9,phi=26.5):
        """
        Sends strategy information to console - both run information and minikappa settings
            timestamp is format YYYY/MM/DD_HH:MM
            omega_start
            delta_omega
            number_images
            time
            distance
            transmission
            kappa
            phi
        """
        if not kappa:
            kappa = 0.0
        if not phi:
            phi = 0.0

        self.logger.debug('''ConsoleConnect.PutDatacollection
        timestamp: %s
        omega_start: %f
        delta_omega: %f
        number_images: %d
        time: %f
        distance: %f
        transmission: %f
        kappa: %f
        phi:%f''' % (timestamp,omega_start,delta_omega,number_images,time,distance,transmission,kappa,phi))

        #Open Redis connection
        #r = redis.Redis(beamline_settings[self.beamline]['redis_ip'])
        r = self.getRedisConnection()
        #Update the date of the setting
        r.set('BEST_STRAT_TS_SV',timestamp)
        #Update the setting
        r.set('BEST_STRAT_SV','_'.join((str(omega_start),str(delta_omega),str(number_images),str(time),str(distance),str(transmission))))

    def PutImageStats(self,result_db,wedges_db):
        """Update Console Redis instance with statistics on an image"""
        if self.logger:
            self.logger.info('ConsoleConnect.PutImageStats')

        #Open Redis connection
        r = self.getRedisConnection()
        #Update the date of the setting
        if (result_db['labelit_status' == 'SUCCESS']):
            r.set('ST_CRYSPARAMS_SV','_'.join((result_db.fullname,
                                               str(result_db.labelit_a),
                                               str(result_db.labelit_b),
                                               str(result_db.labelit_c),
                                               str(result_db.labelit_alpha),
                                               str(result_db.labelit_beta),
                                               str(result_db.labelit_gamma))))
        #Update the setting
        wedge = ''
        if (result_db['best_norm_status']):
            # Get the right wedge
            for wedge in wedges_db:
                if (wedge['strategy_type'] == 'normal'):
                    break

            r.set('ST_STRATEGY_SV','_'.join((result_db.fullname,
                                             str(wedge['phi_start']),
                                             str(wedge['delta_phi']),
                                             str(wedge['number_images']))))

    #
    # Getters for the image info that sometimes goes missing
    #
    def get_image_data_adsc(self):
        """
        Returns a dict of beamline data for storage with the image
        """
        r = self.getRedisConnection()
        p = r.pipeline()
        #p.get("RING_CUR_SV")
        #p.get("RING_MODE_SV")
        p.get("ENERGY_SV")
        p.get("FLUX_SV")
        #p.get("MD2_AP_DIAM_SV")
        #p.get("PUCK_SV")
        #p.get("SAMP_SV")
        p.get("MD2_CENTERING_TABLE_XYZ_SV")
        #p.get("MD2_ALL_AXES_SV")
        beam_vals = p.execute()
        md2_pos = beam_vals[2].split()
        #md2_angles = beam_vals[8].split()

        return_dict = {'beamline'     : self.beamline,
                       #'ring_current' : float(beam_vals[0]),
                       #'ring_mode'    : beam_vals[1],
                       'energy'       : float(beam_vals[0]),
                       'flux'         : float(beam_vals[1]),
                       #'md2_aperture' : int(beam_vals[4].split()[0]),
                       #'puck'         : beam_vals[5],
                       #'sample'       : beam_vals[6],
                       #'phi'          : float(md2_angles[2]),
                       #'kappa'        : float(md2_angles[1]),
                       'md2_x'        : float(md2_pos[0]),
                       'md2_y'        : float(md2_pos[1]),
                       'md2_z'        : float(md2_pos[2])}

        #return the data
        return(return_dict)

    def GetImageData(self):
        """
        Returns a dict of beamline data for storage with the image
        """

        if (self.logger):
            self.logger.debug('GetImageData')

        r = self.getRedisConnection()
        """
        p = r.pipeline()
        p.get("RING_CUR_SV")
        p.get("RING_MODE_SV")
        p.get("ENERGY_SV")
        p.get("FLUX_SV")
        p.get("MD2_AP_DIAM_SV")
        p.get("PUCK_SV")
        p.get("SAMP_SV")
        p.get("MD2_CENTERING_TABLE_XYZ_SV")
        p.get("MD2_ALL_AXES_SV")
        p.get("SEGMENT_OFFSET_SV")
        self.logger.debug(p)
        beam_vals = p.execute()

        if (self.logger):
            self.logger.debug(str(beam_vals))
        """
        
        self.logger.debug('GetImageData - Have redis connection')

        self.logger.debug("Getting Ring current")
        try:
            #ring_current = float(beam_vals[0])
            ring_current = float(r.get("RING_CUR_SV"))
        except:
            ring_current = 0.0
            self.logger.debug("Ring current exception")

        try:
            self.logger.debug("Getting ring mode")
            #ring_mode = "" #str(beam_vals[1])
            ring_mode = str(r.get("RING_MODE_SV"))
        except:
            ring_mode = ''
            self.logger.debug("Ring mode exception")

        try:
            #energy = float(beam_vals[2])
            energy = float(r.get("ENERGY_SV"))
        except:
            energy = 0.0
            self.logger.debug("Energy exception")

        try:
            #flux = float(beam_vals[3])
            flux = float(r.get("FLUX_SV"))
        except:
            flux = 0.0
            self.logger.debug("Flux exception")

        try:
            self.logger.debug("Getting Aperture")
            #md2_aperture = int(beam_vals[4].split()[0])
            md2_aperture = int(r.get("MD2_AP_DIAM_SV").split()[0])
        except:
            md2_aperture = 0
            self.logger.debug("Aperture exception")

        try:
            #puck = str(beam_vals[5])
            puck = str(r.get("PUCK_SV"))
        except:
            puck = ''
            self.logger.debug("Puck exception")

        try:
            #sample = int(beam_vals[6])
            sample = int(r.get("SAMP_SV"))
        except:
            sample = 0
            self.logger.debug("Sample exception")

        try:
            #md2_angles = beam_vals[8].split()
            md2_angles = r.get("MD2_ALL_AXES_SV").split()
        except:
            beam_vals = [0.0, 0.0, 0.0]
            self.logger.debug("Axes exception")

        try:
            phi = float(md2_angles[2])
        except:
            phi = 0.0
            self.logger.debug("Phi exception")

        try:
            kappa = float(md2_angles[1])
        except:
            kappa = 0.0
            self.logger.debug("Kappa exception")

        try:
            #md2_pos = beam_vals[7].replace('_',' ').split()
            md2_pos = r.get("MD2_CENTERING_TABLE_XYZ_SV").replace('_',' ').split()
        except:
            md2_pos = [0.0, 0.0, 0.0]
            self.logger.debug("MD2 Position exception")

	      #scrub out problems with offest
        try:
            self.logger.debug("Getting vertical offset")
            vertical_offset = float(beam_vals[9])
            vertical_offset = float(get("SEGMENT_OFFSET_SV"))
        except:
            vertical_offset = 0
            self.logger.debug("Vertical offset exception")

        self.logger.debug('GetImageData - making dict')

        return_dict = {'beamline'        : self.beamline,
                       'ring_current'    : ring_current,
                       'ring_mode'       : ring_mode,
                       'energy'          : energy,
                       'flux'            : flux,
                       'md2_aperture'    : md2_aperture,
                       'puck'            : puck,
                       'sample'          : sample,
                       'phi'             : phi,
                       'kappa'           : kappa,
                       'md2_x'           : float(md2_pos[0]),
                       'md2_y'           : float(md2_pos[1]),
                       'md2_z'           : float(md2_pos[2]),
                       'vertical_offset' : vertical_offset }

        if (self.logger):
            self.logger.debug(str(return_dict))

        #return the data
        return(return_dict)

    def GetAttenThickness(self):
        """
        Returns attenuator thickness in microns as an int
        """
        self.logger.debug('ConsoleConnect.GetAttenThickness')

        try:
            #Connect to redis database
            r = self.getRedisConnection()
            #Grab the data we want
            thickness = int(r.get('ATTEN_SV'))

            #return the value
            return(thickness)
        except:
            self.logger.exception('Error in ConsoleConnect.GetAttenThickness')
            return(-1)

    def GetMD2ApertureDiameter(self):
        """
        Returns the aperture diameter
        """
        self.logger.debug('ConsoleConnect.GetMD2ApertureDiameter')

        try:
            #Connect to redis database
            r = self.getRedisConnection()
            #Grab the data we want
            diameter = int(r.get('MD2_AP_DIAM_SV'))

            #return the value
            return(diameter)
        except:
            self.logger.exception('Error in ConsoleConnect.GetMD2ApertureDiameter')
            return(-1)

    def GetEnergy(self):
        """
        Returns the energy in eV as a float
        """
        self.logger.debug('ConsoleConnect.GetEnergy')

        try:
            #Connect to redis database
            r = self.getRedisConnection()
            #Grab the data we want
            energy = float(r.get('ENERGY_SV'))

            #return the value
            return(energy)
        except:
            self.logger.exception('Error in ConsoleConnect.GetEnergy')
            return(-1)

    def GetFlux(self):
        """
        Returns the flux in arbitrary units as a float
        """
        self.logger.debug('ConsoleConnect.GetFlux')

        try:
            #Connect to redis database
            r = self.getRedisConnection()
            #Grab the data we want
            flux = float(r.get('FLUX_SV'))

            #return the value
            return(flux)
        except:
            self.logger.exception('Error in ConsoleConnect.GetFlux')
            return(-1)

    def GetPuck(self):
        """
        Returns the puck A/B/C/D as a string
        """
        self.logger.debug('ConsoleConnect.GetPuck')

        try:
            #Connect to redis database
            r = self.getRedisConnection()
            #Grab the data we want
            puck = r.get('PUCK_SV')

            #return the value
            return(puck)
        except:
            self.logger.exception('Error in ConsoleConnect.GetPuck')
            return(-1)

    def GetSample(self):
        return(self.GetPosition)

    def GetPosition(self):
        """
        Returns the puck position as an int
        """
        self.logger.debug('ConsoleConnect.GetPosition')

        try:
            #Connect to redis database
            r = self.getRedisConnection()
            #Grab the data we want
            sample = r.get('SAMP_SV')

            #return the value
            return(sample)
        except:
            self.logger.exception('Error in ConsoleConnect.GetPosition')
            return(-1)

    def GetRingCurrent(self):
        """
        Returns the ring mode
        """
        self.logger.debug('ConsoleConnect.GetRingCurrent')

        try:
            #Connect to redis database
            r = self.getRedisConnection()
            #Grab the data we want
            current = float(r.get('RING_CUR_SV'))

            #return the value
            return(current)
        except:
            self.logger.exception('Error in ConsoleConnect.GetRingCurrent')
            return(-1)

    def GetRingMode(self):
        """
        Returns the ring mode
        """
        self.logger.debug('ConsoleConnect.GetRingMode')

        try:
            #Connect to redis database
            r = self.getRedisConnection()
            #Grab the data we want
            mode = r.get('RING_MODE_SV')

            #return the value
            return(mode)
        except:
            self.logger.exception('Error in ConsoleConnect.GetRingMode')
            return(-1)

    def GetCollectionStatus(self):
        """
        Returns the ADSC status - IDLE COLLECTING ABORTED
        """
        self.logger.debug('ConsoleConnect.GetCollectionStatus')

        try:
            #Connect to redis database
            r = self.getRedisConnection()
            #Grab the data we want
            status = r.get('ADSC_SV')

            #return the value
            return(status)
        except:
            self.logger.exception('Error in ConsoleConnect.GetCollectionStatus')
            return(-1)

if __name__ == '__main__':

    #set up logging
    LOG_FILENAME = '/tmp/rapd_console.log'
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

    """
    #Testing ConsoleRedisMonitor on test db
    def notify(data):
        print 'Notify'
        print data

    test = ConsoleRedisMonitor(beamline='T',notify=notify,logger=logger)
    """

    #Testing console connect
    #C = ConsoleRedisMonitor(logger=logger)
    #C = ConsoleConnect(beamline="C",logger=logger)
    C = ConsoleRedisMonitor2(beamline="T",logger=logger)
