"""
This file is part of RAPD

Copyright (C) 2014-2016, Cornell University
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

__created__ = "2014-04-30"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"
__changelog__ = {
"1.0.1":"""Add changes to handle OVA for remote
""",
"0.9.1":"""Make MongoDB work in processes (multithreading)
Use global pool for redis & mongo
Not breaking redis saves yet, but will as soon as dependency on Mongo can be
confirmed
""",
"0.8": """Save results to mongodb
Remove MySQLdb methods
Redis data saving marked as deprecated
Move to creating global shared redis connections
at svn 6246 before commit
at svn 6247 first commit
""",
"0.7":"""Add processing of scan coords
file for dfa
""",
"0.6":"""Add DISTL analysis for all snaps and run images""",
"0.5" : """Add ability to signal Console heartbeat via the
Redis database using the key DISTL_EPOCHTIME_SV""",
"0.4" : """Handle remote access functions:
	1. Check for current raster request
	2. Copy images to a directory for user use
	3. Publish results and image information for remote usage
"""
}


from rapd_site import beamline_settings, secret_settings

import fcntl
import json
import logging, logging.handlers
import math
import multiprocessing
import os
from pprint import PrettyPrinter
import pymongo
from pymongo.errors import AutoReconnect
import pysent
# from Queue import Queue as queue
import redis
import random
import re
import shutil
import sys
import threading
import time
import urllib2
import uuid


# Number of images concurrently processed
_POOLSIZE = 8
# Available DISTL servers
_HOSTS = ['164.54.212.150']
# Available ports for DISTL
_PORTS = [8125,8126,8127,8128]
# Base URL for DISTL server command
_BASEURL = "http://%s:%d/spotfinder/distl.signal_strength?distl.image=%s&distl.bins.verbose=False&distl.res.outer=%s&distl.res.inner=%s"
# Data to parse out of results
_LOOKUPS = [('file',re.compile("\s*File \:\s*([\w\d\.\_]*)\s*", re.MULTILINE),lambda x: str(x)),
			('total_spots',re.compile("\s*Spot Total \:\s*(\d*)\s*", re.MULTILINE), lambda x: int(x)),
			('remove_ice_spots',re.compile("\s*Remove Ice \:\s*(\d*)\s*", re.MULTILINE), lambda x: int(x)),
			('in_res_spots',re.compile("\s*In-Resolution Total \:\s*(\d*)\s*", re.MULTILINE), lambda x: int(x)),
			('good_b_spots',re.compile("\s*Good Bragg Candidates \:\s*(\d*)\s*", re.MULTILINE), lambda x: int(x)),
			('ice_rings',re.compile("\s*Ice Rings \:\s*([\d\.]*)\s*", re.MULTILINE), lambda x: float(x)),
			('resolution_1',re.compile("\s*Method 1 Resolution \:\s*([\d\.]*)\s*", re.MULTILINE), lambda x: float(x)),
			('resolution_2',re.compile("\s*Method 2 Resolution \:\s*([\d\.]*)\s*", re.MULTILINE), lambda x: float(x)),
			('max_cell',re.compile("\s*Maximum unit cell \:\s*([\d\.]*)\s*", re.MULTILINE), lambda x: float(x)),
			('eccentricity',re.compile("\s*<Spot model eccentricity> \:\s*([\d\.]*)\s*", re.MULTILINE), lambda x: float(x)),
			('saturation_50',re.compile("\s*\%Saturation\, Top 50 Peaks \:\s*([\d\.]*)\s*", re.MULTILINE), lambda x: float(x)),
			('overloads',re.compile("\s*In-Resolution Ovrld Spots \:\s*(\d*)\s*", re.MULTILINE), lambda x: int(x)),
			('total_signal',re.compile("\s*Total integrated signal, pixel-ADC units above local background \(just the good Bragg candidates\)\s*([\d\.]*)\s*", re.MULTILINE), lambda x: float(x)),
			('signal_min',re.compile("\s*Signals range from ([\d\.]*)\s*", re.MULTILINE), lambda x: float(x)),
			('signal_max',re.compile("\s*Signals range from [\d\.]* to ([\d\.]*)\s*", re.MULTILINE), lambda x: float(x)),
			('signal_mean',re.compile("\s*Signals range from [\d\.]* to [\d\.]* with mean integrated signal ([\d\.]*)\s*", re.MULTILINE), lambda x: float(x)),
			('saturation_min',re.compile("\s*Saturations range from ([\d\.]*)\%\s*", re.MULTILINE), lambda x: float(x)),
			('saturation_max',re.compile("\s*Saturations range from [\d\.]*\% to ([\d\.]*)\%\s*", re.MULTILINE), lambda x: float(x)),
			('saturation_mean',re.compile("\s*Saturations range from [\d\.]*% to [\d\.]*% with mean saturation ([\d\.]*)%\s*", re.MULTILINE), lambda x: float(x))]

# Handle remote?
_REMOTE = True


"""
+----------+------+-------+-------+-----------+--------------+
| beamline | zoom | x_cen | y_cen | px_per_um | vector_y_adj |
+----------+------+-------+-------+-----------+--------------+
| E        |    1 |   376 |   283 |     0.318 |         1.01 |
| E        |    2 |   379 |   282 |       0.4 |            1 |
| E        |    3 |   379 |   282 |      0.52 |            1 |
| E        |    4 |   380 |   285 |      0.68 |            1 |
| E        |    5 |   383 |   287 |      0.91 |         1.04 |
| E        |    6 |   385 |   289 |      1.18 |         1.03 |
| E        |    7 |   392 |   296 |      1.55 |         1.02 |
| E        |    8 |   397 |   300 |         2 |         1.02 |
| E        |    9 |   412 |   314 |      2.55 |            1 |
| E        |   10 | 406.8 | 315.4 |      3.35 |            1 |
| C        |    1 |   374 |   284 |     0.355 |         0.95 |
| C        |    2 |   375 |   287 |      0.42 |         0.95 |
| C        |    3 |   376 |   280 |      0.55 |         0.95 |
| C        |    4 |   376 |   280 |      0.72 |         0.95 |
| C        |    5 |   379 |   280 |      0.95 |         0.95 |
| C        |    6 |   384 |   280 |      1.25 |         0.95 |
| C        |    7 |   386 |   280 |       1.6 |         0.95 |
| C        |    8 |   387 |   280 |     2.125 |         0.95 |
| C        |    9 |   394 |   280 |    3.0641 |         0.95 |
| C        |   10 |   399 |   276 |     3.475 |         0.95 |
+----------+------+-------+-------+-----------+--------------+
"""
_CAMERA_PARAMS = {
	"C": {
		1:  {"x_cen":374,"y_cen":284,"px_per_um":0.355},
		2:  {"x_cen":375,"y_cen":287,"px_per_um":0.42},
		3:  {"x_cen":376,"y_cen":280,"px_per_um":0.55},
		4:  {"x_cen":376,"y_cen":280,"px_per_um":0.72},
		5:  {"x_cen":379,"y_cen":280,"px_per_um":0.95},
		6:  {"x_cen":384,"y_cen":280,"px_per_um":1.25},
		7:  {"x_cen":386,"y_cen":280,"px_per_um":1.6},
		8:  {"x_cen":387,"y_cen":280,"px_per_um":2.125},
		9:  {"x_cen":394,"y_cen":280,"px_per_um":3.0641},
		10: {"x_cen":399,"y_cen":276,"px_per_um":3.475},
		"magic_angle":287.5
	},
	"E": {
		1:  {"x_cen":376,"y_cen":283,"px_per_um":0.318},
		2:  {"x_cen":379,"y_cen":282,"px_per_um":0.40},
		3:  {"x_cen":379,"y_cen":282,"px_per_um":0.52},
		4:  {"x_cen":380,"y_cen":285,"px_per_um":0.68},
		5:  {"x_cen":383,"y_cen":287,"px_per_um":0.91},
		6:  {"x_cen":385,"y_cen":289,"px_per_um":1.18},
		7:  {"x_cen":392,"y_cen":296,"px_per_um":1.55},
		8:  {"x_cen":397,"y_cen":300,"px_per_um":2.0},
		9:  {"x_cen":412,"y_cen":314,"px_per_um":2.55},
		10: {"x_cen":406.8,"y_cen":315.4,"px_per_um":3.35},
		"magic_angle":226.5
	},
	"T": {
		1:  {"x_cen":374,"y_cen":284,"px_per_um":0.355},
		2:  {"x_cen":375,"y_cen":287,"px_per_um":0.42},
		3:  {"x_cen":376,"y_cen":280,"px_per_um":0.55},
		4:  {"x_cen":376,"y_cen":280,"px_per_um":0.72},
		5:  {"x_cen":379,"y_cen":280,"px_per_um":0.95},
		6:  {"x_cen":384,"y_cen":280,"px_per_um":1.25},
		7:  {"x_cen":386,"y_cen":280,"px_per_um":1.6},
		8:  {"x_cen":387,"y_cen":280,"px_per_um":2.125},
		9:  {"x_cen":394,"y_cen":280,"px_per_um":3.0641},
		10: {"x_cen":399,"y_cen":276,"px_per_um":3.475},
		"magic_angle":287.5
	}
}

_TESTING = True
_FILE_HEARTBEAT = False
_REDIS_HEARTBEAT = True
_RUN = True
_PROCESS_ALL = False

# MongoDB?
_MONGO = True
_TESTING_MONGO = False


def processImage(image,dat_dirs,test_image,test_dat,main,beamline,logger=False):
	"""Process an image through the DISTL server"""

	if logger:
		logger.debug('processImage %s' % image)

	# Only process image if need be
	if _PROCESS_ALL or (image == test_image) or (os.path.dirname(image) in dat_dirs):

		# Get parameters from beamline
		beamline_params = getBeamlineParams(beamline,main,logger)
		# Run distl
		parameters = runDistl(image,beamline_params,main,logger)

		# Test image - write special non-data-containing file
		# This is after running DISTL to make it useful as a heartbeat
		if image == test_image:

			# Signal console via redis
			signalHeartbeat(beamline,main,logger)

			return True

		# Rastering images
		elif os.path.dirname(image) in dat_dirs:

			if logger:
				logger.debug("%s in dat_dirs" % image)

			# For Console
			writeDatFile(image,parameters,main,logger)

			# Handle remote access
			if _REMOTE:
				handleRemote(image,parameters,beamline,logger)

			return True

		# Process everything
		# elif _PROCESS_ALL:
		# 	publishDistl(image,parameters,beamline)


# ========================
# AFTER PROCESSING METHODS
# ========================

def publishDistl(image,parameters,beamline,logger=False):
	"""Push the results out over redis"""
	if logger:
		logger.debug("publishDistl %s %s" % (image,beamline))
		logger.debug(parameters)

	_RedisClient1.publish('%s:distl_result' % beamline, json.dumps(parameters))


################
# REMOTE METHODS
################

def handleRemote(image,parameters,beamline,logger=False):
	"""Handle remote access support actions
	"""
	if logger:
		logger.debug('handleRemote %s %s' % (image,beamline))

	# Some manipulations we might need
	split_image = image.split("_")
	image_number = int(split_image[-1].split(".")[0])
	image_uuid = str(uuid.uuid4())

	# CURRENT_RASTER
	# Is there a current raster for my beamline? Check both redis instances
	# Could track locally, but using expiring redis key works well
	current_raster_return = _RedisClient1.get("%s:current_raster" % beamline)
	sure_thing = 1
	if (current_raster_return == None):
		if logger:
			logger.debug("Cannot find a current raster specification for %s" % beamline)
		return False

	current_raster_id = current_raster_return.split(":")[1]
	if logger:
		logger.debug("Have a current raster %s" % current_raster_id)

	# RASTER_SPECIFICATION
	current_raster_data = False

	# MongoDB
	if (not current_raster_data) and _MONGO:
		if logger:
			logger.debug("Try mongo to get the raster specification")
		current_raster_data = get_raster_specification(current_raster_id,logger)

		if logger:
			logger.debug("current_raster_data from MongoDB")
			logger.debug(current_raster_data)

	# Redis
	if not current_raster_data:
		if logger:
			logger.debug('Using redis to get the raster specification')

		raster_key = "image_raster_exec:%s" % current_raster_id

		current_raster_data = json.loads(_RedisClient1.get(raster_key))

		if logger:
			logger.debug("Have current raster data for %s" % current_raster_id)
			logger.debug(current_raster_data)

	# Check for points data
	update = False
	points = False
	if (not current_raster_data.get("points",False)):
		if logger:
			logger.debug('Handling ADX_PERFRAME')
		points = getAdxPerframe(beamline,image,logger)
		update = True
		if logger:
			logger.debug("%d points retrieved" % len(points))
		# Store in soon to be passed dict
		current_raster_data["points"] = points

	# Scan coordinates
	coords = False
	md2_xyz = False
	if (not current_raster_data.get("coords",False)):
		if logger:
			logger.debug('Handling Scan Coords')
		coords,md2_xyz = getScanCoords(beamline,image,current_raster_data,logger)
		if coords:
			update = True
			if logger:
				logger.debug("Scan coordinates retrieved")
				logger.debug(coords)


	# Has anything updated?
	if update:

		if logger:
			logger.debug("Raster specification has been updated")

		# Save points
		# DEV when redis goes away this will change
		if points:
			if logger:
				logger.debug("Points updated")
			# Update MongoDB?
			if _MONGO:
				update_raster_specification(current_raster_data,"points",logger)

		# Save coords state in the current_raster_data
		if coords:
			if logger:
				logger.debug("Coords updated")
			current_raster_data["coords"] = coords
			# Update MongoDB?
			if _MONGO:
				update_raster_specification(current_raster_data,"coords",logger)

		# Save md2_xyz
		if md2_xyz:
			if logger:
				logger.debug("md2_xyz updated")
			current_raster_data["md2_xyz"] = md2_xyz
			# Update MongoDB?
			if _MONGO:
				update_raster_specification(current_raster_data,"md2_xyz",logger)

# DEPRECATED
		# Save to redis database
		# Convert to JSON for portability
		current_raster_data.pop("_id",False)
		json_current_raster_data = json.dumps(current_raster_data)
		if logger:
			logger.debug("Updating image_raster_exec:%s" % current_raster_id)
		_RedisClient1.set("image_raster_exec:%s" % current_raster_id,json_current_raster_data)
		#_RedisClient2.set("image_raster_exec:%s" % current_raster_id,json_current_raster_data)

		if points:
			if logger:
				logger.debug("Setting points:%s" % current_raster_id)
			_RedisClient1.set("points:%s"%current_raster_id,json.dumps(points))
			#_RedisClient2.set("points:%s"%current_raster_id,json.dumps(points))

		if coords:
			if logger:
				logger.debug("Setting %s:coords" % current_raster_id)
			_RedisClient1.set("coords:%s"%current_raster_id,json.dumps(coords))
			#_RedisClient2.set("coords:%s"%current_raster_id,json.dumps(coords))

		if md2_xyz:
			if logger:
				logger.debug("Setting md2_xyz:%s" % current_raster_id)
			md2_xyz_json = json.dumps(md2_xyz)
			#_RedisClient1.set("md2_xyz:%s"%current_raster_id,md2_xyz_json)
			#_RedisClient2.set("md2_xyz:%s"%current_raster_id,md2_xyz_json)

# END DEPRECATED

		# Publish specs for immediate use
		if logger:
			logger.debug("Publishing %s:new_raster_spec" % beamline)
		_RedisClient1.publish('%s:new_raster_spec' % beamline, json_current_raster_data)

	else:
		if logger:
			logger.debug("Already have all perframe positional information")


	# Store xyz data in result data temporarily for use
	current_raster_data["md2_x"] = current_raster_data["points"][image_number-1]["x"]
	current_raster_data["md2_y"] = current_raster_data["points"][image_number-1]["y"]
	current_raster_data["md2_z"] = current_raster_data["points"][image_number-1]["z"]

	# Make sure inputs are something reasonable
	puck_label = current_raster_data.get('puck_label')
	if puck_label:
		puck_label = puck_label.replace(' ','_')
	else:
		puck_label = "UNK"

	# Compose the target directory
	tdir = os.path.join('/',
						current_raster_data.get('filespace'),
						'users',
						current_raster_data.get('inst'),
						'_'.join((current_raster_data.get('group'),current_raster_data.get('beamline'),str(current_raster_data.get('session_id')))),
						'process',
						'rasters',
						puck_label)

	if logger:
		logger.debug("Image will be copied to %s" % tdir)

	# If we are not testing, then copy the file
	if beamline != 'T':
		# If the target directory does not exist, make it
		if not (os.path.exists(tdir)):
			if logger:
				logger.debug("Creating directory %s" % tdir)
			try:
				os.makedirs(tdir)
			except:
				if logger:
					logger.debug("Error creating %s" % tdir)
				return False

	# rastersnap
	if (("_raster_snap" in image) or ("rastersnap_scan" in image)):
		if logger:
			logger.debug("RASTERSNAP")
		tfile = '_'.join((puck_label,
											str(current_raster_data.get('sample')),
											'line',
											str(current_raster_data.get('iteration')),
											split_image[-1]))
	# dfa
	elif (("_dfa_" in image) or ("dfa_scan" in image)):
		if logger:
			logger.debug("DFA")
		tfile = '_'.join((puck_label,
											str(current_raster_data.get('sample')),
											'grid',
											str(current_raster_data.get('iteration')),
											split_image[-1]))

	# ova
	elif ("ova_scan" in image):
		if logger:
			logger.debug("OVA")
		tfile = '_'.join((current_raster_data.get('puck_label').replace(' ','_'),
											str(current_raster_data.get('sample')),
											'vert',
											str(current_raster_data.get('iteration')),
											split_image[-1]))

	#
	if logger:
		logger.debug("Target file: %s" % tfile)
	target_file = os.path.join(tdir,tfile)

	# If we are not testing, then copy the file
	if beamline != 'T':
		# Now copy the file
		success = copyFile(image,target_file,logger)
		if (not success):
			return False

	# # Tell remote access about the new image
	# try:
	# 	image_metadata = {"fullname":     target_file,
	# 	                  "id":           image_uuid,
	# 					  "run_uuid":     current_raster_id,
	# 					  "type":         "RUN",  # Change type to 1D??
	# 					  "name":         os.path.basename(target_file),
	# 					  "osc_start":    current_raster_data.get("omega_initial",0.0),
	# 					  "osc_range":    current_raster_data.get("omega_delta",0.0),
	# 					  "time":         current_raster_data.get("exposure",0.0),
	# 					  "distance":     current_raster_data.get("distance",0.0),
	# 					  "transmission": current_raster_data.get("transmission",0.0),
	# 					  "analysis":     True, # Not sure on the usage of this, but seems important
	# 				  	  "image_number": image_number
	# 					  }
	# except:
	# 	if logger:
	# 		logger.debug("Error constructing image_metadata")
	#
	# if logger:
	# 	logger.debug("\nWill publish on channel %s" % target_file)
	# 	logger.debug(image_metadata)
	#
	#
	# # Publish the file being created - remember this is now in the user space
	#json_image_metadata = json.dumps(image_metadata)
	#_RedisClient1.publish(target_file,json_image_metadata)

	# Publish the DISTL results
	assemble = {'raster_uuid': current_raster_id,
				'image_uuid': image_uuid,
				'status': 'success',
				'beamline': beamline,
				'crystal_image': current_raster_data.get('crystal_image',''),
				'fullname': target_file,
				'image_id': current_raster_data.get('image_id',0),
				'image_number': image_number,
				'md2_x': current_raster_data.get('md2_x',0),
				'md2_y': current_raster_data.get('md2_y',0),
				'md2_z': current_raster_data.get('md2_z',0)
				}
	# Update results (parameters) with image data
	parameters.update(assemble)

	# Save DISTL analysis to MongoDB
	if _MONGO:
		update_quickanalysis_result(parameters)

	# For portability
	json_assemble = json.dumps(parameters)

# DEPRECATED
	# Save to redis
	a_key = 'quickanalysis_result:%s:%s' % (current_raster_id,str(image_number))
	_RedisClient1.set(a_key,json_assemble)
# END DEPRECATED

	# Publish result over redis
	if logger:
		logger.debug("Will publish on channel %s:quickanalysis_result" % beamline)
		logger.debug(parameters)
	_RedisClient1.publish('%s:quickanalysis_result' % beamline,json_assemble)

	return True

def getAdxPerframe(beamline,image,logger=False):

	if logger:
		logger.debug("getAdxPerframe %s %s" % (beamline,image))

	# Wait for a second
	#time.sleep(1)

	# new style
	if 'scan' in image:
		src_file = "_".join(image.replace('/0_0','').split('_')[:-2]+['cenxyz.dat',])
	# old style
	else:
		src_file = secret_settings[beamline].get("adx_perframe_file")

	# Copy the frame for reading
	tmp_filename = os.path.join('/','tmp',str(uuid.uuid4())+'.dat')
	success = copyFile(src_file,tmp_filename,logger)
	if (not success):
		return False

	# Read adx_perframe for data collection points
	lines = open(tmp_filename,"r").readlines()
	points = []
	for line in lines:
		vals = line.strip().split()
		if len(vals) > 3:
			points.append({"x":float(vals[0]),
						   "y":float(vals[1]),
						   "z":float(vals[2])})

	# Remove the tmp file
	os.unlink(tmp_filename)

	if logger:
		logger.debug(points)

	return points

def getScanCoords(beamline,image="",raster_specification=False,logger=False):

	if logger:
		logger.debug("getScanCoords %s %s" % (beamline,image))

	# Wait for a second to make sure the filesystem is up to date
	time.sleep(1)

	try:
		# new style
		if 'scan' in image:
			src_file = "_".join(image.replace('/0_0','').split('_')[:-2]+['axoval.dat',])
		# old style
		else:
			src_file = secret_settings[beamline].get("scan_coords_file")

		# Copy the frame for reading
		tmp_filename = os.path.join('/','tmp',str(uuid.uuid4())+'.dat')
		success = copyFile(src_file,tmp_filename,logger)
		if (not success):
			if logger:
				logger.debug("Not successful copying %s to %s" % (src_file,tmp_filename))
			return (False,False)

		# Read adx_perframe for data collection points
		lines = open(tmp_filename,"r").readlines()
		coords = []
		for line in lines:
			vals = line.strip().split()
			if len(vals) > 3:
				if logger:
					logger.debug(vals)
				coord = {"x":(float(vals[0]) + float(vals[1])) / 2,
						 "y":(float(vals[2]) + float(vals[3])) / 2,
						 "rx":(float(vals[1]) - float(vals[0])) / 2,
						 "ry":(float(vals[3]) - float(vals[2])) / 2}
				if logger:
					logger.debug(coord)
				coords.append(coord)

		# Remove the tmp file
		os.unlink(tmp_filename)

		# Convert coords to md2 motor xyz
		if raster_specification:
			motor_points = []
			if logger:
				logger.debug("Have raster_specification")

			# Position of md2 is the home position taken from beamline
			if raster_specification.has_key('home_md2'):
				md2_position = {
					"x":raster_specification["home_md2"]["x"],
					"y":raster_specification["home_md2"]["y"],
					"z":raster_specification["home_md2"]["z"],
					"zoom":raster_specification["zoom"],
					"omega":raster_specification["omega_initial"] + raster_specification["omega_delta"]/2.0
				};
			# Position of md2 is the center of the vector
			else:
				md2_position = {
					"x":(raster_specification["start_point"]["x"] + raster_specification["end_point"]["x"]) / 2.0,
					"y":(raster_specification["start_point"]["y"] + raster_specification["end_point"]["y"]) / 2.0,
					"z":(raster_specification["start_point"]["z"] + raster_specification["end_point"]["z"]) / 2.0,
					"zoom":raster_specification["zoom"],
					"omega":raster_specification["omega_initial"] + raster_specification["omega_delta"]/2.0
				};
			if logger:
				logger.debug('>>>md2_position',str(md2_position))

			#microns per pixel
			x_cen = _CAMERA_PARAMS[raster_specification["beamline"]][raster_specification["zoom"]]["x_cen"]
			y_cen = _CAMERA_PARAMS[raster_specification["beamline"]][raster_specification["zoom"]]["y_cen"]
			mpp = 1/_CAMERA_PARAMS[raster_specification["beamline"]][raster_specification["zoom"]]["px_per_um"];
			if logger:
				logger.debug(">>>x_cen %f" % x_cen)
				logger.debug(">>>y_cen %f" % y_cen)
				logger.debug(">>>mpp %f" % mpp)

			# omega
			omega = md2_position["omega"]-_CAMERA_PARAMS[raster_specification["beamline"]]["magic_angle"];
			while (omega < 0):
				omega = omega + 360.0;
			omega = omega % 360.0;
			omega = (math.pi/180.0)*omega;
			if logger:
				logger.debug(">>>omega %f" % omega)

			for draw_point in coords:

				# Calculate offsets
				dz = ((draw_point["x"] - x_cen) * mpp) / 1000
				dy = -1 * (draw_point["y"] - y_cen) * mpp * math.cos(omega) / 1000
				dx = (draw_point["y"] - y_cen) * mpp * math.sin(omega) / 1000

				motor_point = {
					"x": md2_position["x"] - dx,
					"y": md2_position["y"] - dy,
					"z": md2_position["z"] - dz
				}

				if logger:
					logger.debug('draw_point',draw_point,'motor_point',motor_point)

				#Place in array
				motor_points.append(motor_point)

		else:
			motor_points = False

		# Return the coordinates
		return coords,motor_points

	except:
		if logger:
			logger.debug("Error in getScan Coords")
		return False, False


#################
# UTILITY METHODS
#################
def copyFile(source_file,target_file,logger=False):
	if logger:
		logger.debug("copyFile %s >> %s" % (source_file,target_file))

	target_dir = os.path.dirname(target_file)

	try:
		# Make sure files aren't being overwritten
		if os.path.exists(target_file):
			counter = 1
			targetbase = target_file+'_'
			while (counter < 999):
				target_file = targetbase+str(counter)
				if not os.path.exists(target_file):
					break
				else:
					counter += 1
	except:
		if logger:
			logger.debug("Error finding permissible target file iteration")
		return False

	try:
		# Make sure target directory exists
		if not (os.path.exists(target_dir)):
			pass
			if _RUN:
				os.makedirs(target_dir)
	except:
		if logger:
			logger.debug("Error checking/creating target directory %s" % target_dir)
		return False

	try:
		# Copy the file
		if _RUN: shutil.copyfile(source_file,target_file)
	except:
		if logger:
			logger.debug("Error copying file %s to %s" % (source_file,target_file))
			logger.debug(sys.exc_info()[0])
		return False

	return target_file

# For feedback to user
_PPRINTER = PrettyPrinter()
def pprint(item):
	_PPRINTER.pprint(item)

# For making sure we are running a singleton
_file_handle = None
def file_is_locked(file_path):
		global _file_handle
		_file_handle= open(file_path, 'w')
		try:
				fcntl.lockf(_file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
				return False
		except IOError:
				return True

def runDistl(image,beamline_params,main,logger=False):
	"""Run the DISTL process and pass back the parsed data"""

	if logger:
		logger.debug('runDistl %s' % image)

	if beamline_params['beamline'] != 'T':

		command = _BASEURL%(random.choice(_HOSTS),random.choice(_PORTS),image,beamline_params['outer'],beamline_params['inner'])

		if logger:
			logger.debug(command)

		Response = urllib2.urlopen(command)
		raw = Response.read()
		Response.close()

		# Parse raw reply
		parameters = {'file'             : 'None',
					  'total_spots'      : 0,
					  'remove_ice_spots' : 0,
					  'in_res_spots'     : 0,
					  'good_b_spots'     : 0,
					  'ice_rings'        : 0.0,
					  'resolution_1'     : 0.0,
					  'resolution_2'     : 0.0,
					  'max_cell'         : 0.0,
					  'eccentricity'     : 0.0,
					  'saturation_50'    : 0.0,
					  'overloads'        : 0,
					  'total_signal'     : 0.0,
					  'signal_min'       : 0.0,
					  'signal_max'       : 0.0,
					  'signal_mean'      : 0.0,
					  'saturation_min'   : 0.0,
					  'saturation_max'   : 0.0,
					  'saturation_mean'  : 0.0 }

		for lookup in _LOOKUPS:
			label,pattern,xform = lookup
			matches = pattern.findall(raw)
			if len(matches) > 0:
				try:
					parameters[label] = xform(matches[0])
				except:
					pass
	else:
		parameters = {  'file'             : image,
						'total_spots'      : 0,
						'remove_ice_spots' : 0,
						'in_res_spots'     : 0,
						'good_b_spots'     : 0,
						'ice_rings'        : 0.0,
						'resolution_1'     : 0.0,
						'resolution_2'     : 0.0,
						'max_cell'         : 0.0,
						'eccentricity'     : 0.0,
						'saturation_50'    : 0.0,
						'overloads'        : 0,
						'total_signal'     : 0.0,
						'signal_min'       : 0.0,
						'signal_max'       : 0.0,
						'signal_mean'      : 0.0,
						'saturation_min'   : 0.0,
						'saturation_max'   : 0.0,
						'saturation_mean'  : 0.0 }

		if logger:
			logger.debug(parameters)
	return parameters

##################
# BEAMLINE METHODS
##################
def writeDatFile(image,parameters,main,logger=False):
	"""Write the output file"""

	if logger:
		logger.debug('writeDatFile')

	try:
		# New style?
		if '_scan_data' in image:
			# Manipulate the input filename to get output filename
			split_image = image.replace('/0_0','').replace('.img','.dat').replace('.cbf','.dat').split('_')
			output_file = '_'.join(split_image[:-1]+['distl_res']+split_image[-1:])
		else:
			# Manipulate the input filename to get output filename
			output_file = image.replace('in','out').replace('/0_0','').replace('.img','.dat').replace('.cbf','.dat')

		if logger:
			logger.debug('writing %s' % output_file)

		# Write the file
		output = open(output_file,'w')
		output.write('%12.2f\r\n'%parameters['resolution_1'])
		output.write('%12.2f\r\n'%parameters['resolution_2'])
		output.write('%10d\r\n'%parameters['overloads'])
		output.write('%10d\r\n'%parameters['total_spots'])
		output.write('%10d\r\n'%parameters['good_b_spots'])
		output.write('%10d\r\n'%parameters['in_res_spots'])
		output.write('%12.2f\r\n'%parameters['signal_max'])
		output.write('%12.2f\r\n'%parameters['signal_mean'])
		output.write('%12.2f\r\n'%parameters['signal_min'])
		output.write('%12.2f\r\n'%parameters['total_signal'])
		output.write('%12.2f\r\n'%parameters['saturation_50'])
		output.close()
		return True

	except:
		return False

def getBeamlineParams(beamline,main,logger=False):
	"""Retrieve parameters for analysis from the beamline"""

	if logger:
		logger.debug('getBeamlineParams %s' % beamline)

	try:
            inner_limit = _RedisBeamline.get("DISTL_INNERRES_SV")
            outer_limit = _RedisBeamline.get("DISTL_OUTERRES_SV")
            if logger:
                logger.debug("Retrieved DISTL params from beamline: inner:%s outer:%s" % (inner_limit, outer_limit))
        except:
            inner_limit = "30"
            outer_limit = "5"

	return {"beamline":beamline,"inner":inner_limit, "outer":outer_limit}


###################
# HEARTBEAT METHODS
###################
def writeHeartbeatFile(filename,main,logger=False):
	"""Write the heartbeat file for console to monitor"""

	if logger:
		logger.debug('writeHeartbeatFile %s' % filename)

	try:
		output = open(filename,'w')
		output.write('%f \n' % time.time());
		output.close()
		return True

	except:
		if logger:
			logger.debug("Error writing heartbeat file")
		return False

def signalHeartbeat(beamline,main,logger=False):
	"""Write the heartbeat information to the Redis db"""

	if logger:
		logger.debug('signalHeartbeat %s' % beamline)

	try:
		_RedisBeamline.set("DISTL_EPOCHTIME_SV","%d" % int(time.time()))
		return True

	except:
		if logger:
			logger.debug("Error updating heartbeat in Redis db")
		return False

############
# MAIN CLASS
############
class DISTL_Freeagent(threading.Thread):
	"""Freestanding agent for processing images collected on beamline
	through DISTL to get key image parameters"""

	def __init__(self,beamline='C',main=False,logger=False):

		if logger:
			logger.debug("DISTL_Freeagent.__init__")

		threading.Thread.__init__(self)

		self.logger = logger
		self.main = main
		self.beamline = beamline
		self.settings = beamline_settings[beamline]
		self.secret_settings = secret_settings[beamline]

		self.dat_dirs = self.settings['analysis_shortcircuits']
		self.test_frame = self.secret_settings['rastersnap_test_image']
		self.test_dat = self.secret_settings['rastersnap_test_dat']

		self.start()

	def run(self):
		"""Run the agent to listen for files to analyze"""

		if self.logger:
			self.logger.debug('DISTL_Freeagent.run')

		# Create subscription for new files
		if self.logger:
			self.logger.debug('Subscribing to filecreate:%s' % self.beamline)

		# Test uses local redis
		if self.beamline == 'T':
			red = pysent.RedisManager(sentinel_host="remote.nec.aps.anl.gov",
									  sentinel_port=26379,
									  master_name="remote_master")
		else:
			red = pysent.RedisManager(sentinel_host="remote.nec.aps.anl.gov",
								      sentinel_port=26379,
						              master_name="remote_master")

		# Create pubsub & subscribe to file creation
		red.subscribe('filecreate:%s' % self.beamline)

		# Listen for messages and do something
		if self.logger:
			self.logger.debug("Start listening on redis subscription")

		for payload in red.listen():

			if self.logger:
				self.logger.debug(payload)

			filename = payload['data']
			if type(filename) == str:
				p = multiprocessing.Process(target=processImage, args=(filename,self.dat_dirs,self.test_frame,self.test_dat,self.main,self.beamline,self.logger))
				p.start()
				if self.logger:
					self.logger.debug('Process started with pid %d' % p.pid)
				p.join(0)



if __name__ == '__main__':

	print 'rapd_distl_freeagent v%s' % __version__
	print '----------------------'+'-'*len(__version__)

	# Assure we are running as a singleton
	file_path = '/tmp/lock/rapd_freeagent_distl.lock'

	if not os.path.exists(os.path.dirname(file_path)):
			os.makedirs((os.path.dirname(file_path)))

	if file_is_locked(file_path):
			print 'another instance is running exiting now'
			sys.exit(0)
	else:
			print 'no other instance is running'

	# Capture the commandline and go
	try:
		beamline = sys.argv[1]
	except:
		print 'Beamline needs to be selected. Choices are C,E or T'
		sys.exit(9)

	#
	# Set up logging
	#
	LOG_FILENAME = '/tmp/rapd_freeagent_distl.log'

	# Set up a specific logger with our desired output level
	logger = logging.getLogger('RAPDLogger')
	logger.setLevel(logging.DEBUG)

	# Add the log message handler to the logger
	handler = logging.handlers.RotatingFileHandler(
			LOG_FILENAME, maxBytes=5000000, backupCount=5)

	#add a formatter
	formatter = logging.Formatter("%(asctime)s - %(message)s")
	handler.setFormatter(formatter)
	logger.addHandler(handler)

	# Create mongo client
	if _MONGO:
		# Import
		# from pymongo import ReplicaSetConnection
		# from pymongo import Connection
		# from pymongo.errors import AutoReconnect

		# Create the mongo connection
		_MongoClient = pymongo.MongoClient(secret_settings[beamline]['mongo-connection-string'])
		# if (secret_settings[beamline]['mongo-type'] == 'replicaset'):
		# 	_MongoClient = ReplicaSetConnection(secret_settings[beamline]['mongo-connection'],
		# 										replicaSet=secret_settings[beamline]['mongo-replicaset'])
		# elif (secret_settings[beamline]['mongo-type'] == 'single'):
		# 	_MongoClient = Connection(secret_settings[beamline]['mongo-connection'])
		_MongoDB = _MongoClient.remote

		# Handle reconnection failover
		def safe_mongocall(call):
			def _safe_mongocall(*args, **kwargs):
				for i in xrange(5):
					try:
						return call(*args, **kwargs)
					except AutoReconnect:
						time.sleep(pow(2, i))
					if logger:
						logger.debug('Error: Failed operation!')
			return _safe_mongocall

		# Retrieve a single raster_specification, by raster_uuid
		@safe_mongocall
		def get_raster_specification(raster_uuid,logger=False):
			if logger:
				logger.debug("get_raster_specification")
			return _MongoDB.raster_specifications.find_one({'raster_uuid':raster_uuid})

		if _TESTING_MONGO:
			if logger:
				logger.debug('Test get_raster_specification')
				logger.debug(get_raster_specification('658AF831-962F-4F38-B9E4-57EF0CCDC46F'))

		# Update a raster specification
		@safe_mongocall
		def update_raster_specification(raster_specification,mode='__document',logger=False):

			if logger:
				logger.debug("update_raster_specification")

			if mode == '__document':
				_MongoDB.raster_specifications.update(
					{'raster_uuid':raster_specification['raster_uuid']},
					raster_specification,
					upsert=True,
					multi=False)
				return True

			elif type(mode) == str:
				_MongoDB.raster_specifications.update(
					{'raster_uuid':raster_specification['raster_uuid']},
					{'$set':{mode:raster_specification[mode]}},
					multi=False)
				return True

			elif type(mode) in (tuple,list):
				for field in mode:
					_MongoDB.raster_specifications.update(
						{'raster_uuid':raster_specification['raster_uuid']},
						{'$set':{field:raster_specification[field]}},
						multi=False)
				return True

		if _TESTING_MONGO:
			if logger:
				logger.debug('Test update_raster_specification')
			raster_specification = get_raster_specification('658AF831-962F-4F38-B9E4-57EF0CCDC46F')
			raster_specification['zoom'] = 0
			if logger:
				logger.debug(update_raster_specification(raster_specification,'zoom')) # return is none
				logger.debug(get_raster_specification('658AF831-962F-4F38-B9E4-57EF0CCDC46F')['zoom'])
			raster_specification['zoom'] = 1
			update_raster_specification(raster_specification,('zoom',),logger)
			if logger:
				logger.debug(get_raster_specification('658AF831-962F-4F38-B9E4-57EF0CCDC46F')['zoom'])
			sys.exit(0)

		# Save a distl analysis result
		# Update a raster specification
		@safe_mongocall
		def update_quickanalysis_result(quickanalysis_result):
			return _MongoDB.quickanalysis_results.update(
				{
					'raster_uuid':quickanalysis_result['raster_uuid'],
					'image_number':quickanalysis_result['image_number']
				},
				quickanalysis_result,
				upsert=True,
				multi=False)

		if _TESTING_MONGO:
			if logger:
				logger.debug('Test update_quickanalysis_result')
			result={ u'beamline': u'C',
					 u'crystal_image': u'xtal_images/C/2014/10/14/658AF831-962F-4F38-B9E4-57EF0CCDC46F.jpg',
					 u'eccentricity': 0.0,
					 u'file': u'phi_rastsnap_1_0004.cbf',
					 u'fullname': u'/gpfs7/users/necat/necat_C_862/process/rasters/SKI5/SKI5_0_line_4_0004.cbf',
					 u'good_b_spots': 0,
					 u'ice_rings': 0.0,
					 u'image_id': 0,
					 u'image_number': 4,
					 u'image_uuid': u'671d6a5e-899f-4a6e-97ff-a876e5cb1c89',
					 u'in_res_spots': 0,
					 u'max_cell': 0.0,
					 u'md2_x': -1.04243,
					 u'md2_y': -0.35936,
					 u'md2_z': 0.7075,
					 u'overloads': 0,
					 u'raster_uuid': u'658AF831-962F-4F38-B9E4-57EF0CCDC46F',
					 u'remove_ice_spots': 0,
					 u'resolution_1': 10.0,
					 u'resolution_2': 0.0,
					 u'saturation_50': 0.0,
					 u'saturation_max': 0.0,
					 u'saturation_mean': 0.0,
					 u'saturation_min': 0.0,
					 u'signal_max': 0.0,
					 u'signal_mean': 0.0,
					 u'signal_min': 0.0,
					 u'status': u'success',
					 u'total_signal': 0.0,
					 u'total_spots': 0 }

			if logger:
				logger.debug(update_quickanalysis_result(result)) # return is none



	# Create redis clients
	if beamline == 'T':
		_RedisClient1 =  pysent.RedisManager(sentinel_host="remote.nec.aps.anl.gov",
								sentinel_port=26379,
								master_name="remote_master")
		_RedisBeamline = redis.Redis(secret_settings[beamline]['redis_ip'])

	else:
		"""
		_RedisClient1 =  redis.Redis(secret_settings[beamline]['remote_redis_ip'])
		_RedisClient2 =  redis.Redis(secret_settings[beamline]['remote_redis_ip2'])
		_RedisBeamline = redis.Redis(secret_settings[beamline]['redis_ip'])
		"""
		_RedisClient1 =  pysent.RedisManager(sentinel_host="remote.nec.aps.anl.gov",
								sentinel_port=26379,
								master_name="remote_master")
		#_RedisClient2 =  pysent.RedisManager(sentinel_host="remote.nec.aps.anl.gov",
		#						sentinel_port=26379,
		#						master_name="remote_master")
		_RedisBeamline = redis.Redis(secret_settings[beamline]['redis_ip'])


	A = DISTL_Freeagent(beamline=beamline,main=True,logger=logger)
