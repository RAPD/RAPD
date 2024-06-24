"""
This file is part of RAPD

Copyright (C) 2016-2018 Cornell University
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

__created__ = "2016-02-01"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

import logging
import os
import pymongo
import redis
import uuid

from utils.text import json
from bson.objectid import ObjectId

from utils import pysent

class Adapter(object):
    """Serves as a connection to the remote beamline control system"""

    mongo = None
    mongo_remote = None
    redis = None

    def __init__(self, settings):
        """
        Keyword arguments:
        beamline -- tag denoting the beamline to connect to C, E, or T at necat
        logger -- an instance of logger
        """

        # Get the logger Instance
        self.logger = logging.getLogger("RAPDLogger")
        self.logger.info("Initializing")

        # Store passed-in variables
        self.settings = settings
        self.logger.debug("Settings: %s", self.settings)

        # Initialize the database connections
        self.init_db()

    def init_db(self):
        """Initialize the database connections"""

        self.logger.debug("Remote.init_db")

        # Establish connection to redis database
        if self.settings["REDIS_CLUSTER"]:
            self.redis = pysent.RedisManager(sentinel_host=self.settings["SENTINEL_HOST"],
                                             sentinel_port=self.settings["SENTINEL_PORT"],
                                             main_name=self.settings["REDIS_MASTER_NAME"])
        else:
            self.redis = redis.Redis(self.settings["REDIS_HOST"], self.settings["REDIS_PORT"])
            # raise Exception("No connection to redis cluster")

        # Establish connection to Mongo database
        try:
            self.mongo = pymongo.MongoClient(
                self.settings["MONGO_CONNECTION_STRING"])
            self.mongo_remote = self.mongo.remote
        except:
            self.logger.exception("Cannot connect to MongoDB at %s",
                                  self.settings["MONGO_CONNECTION_STRING"])

    def add_image(self, image_metadata):
        """Add an image to the remote system

        Keyword argument:
        image_metadata -- dict containing image metadata
        """

        self.logger.debug("Remote.add_image image:%s",
                          image_metadata.get("fullname"))
        self.logger.debug(image_metadata)

        # Add useful info to the metadata for
        image_metadata["name"] = os.path.basename(image_metadata["fullname"])
        image_metadata["_id"] = str(uuid.uuid1())

        # Filter for no image_id key
        if not "image_id" in image_metadata:
            image_metadata["image_id"] = 0

        # Publish image_metadata for subscribers
        try:
            self.logger.debug("Publishing %s %s", (image_metadata["fullname"],
                                                   json.dumps(image_metadata)))
            self.redis.publish(image_metadata["fullname"],
                               json.dumps(image_metadata))
        except:
            self.logger.exception("Error publishing image metadata to Redis")

        # Save to Mongo
        try:
            self.mongo_remote.image_metadata.update(
                {"_id":image_metadata["_id"]},
                image_metadata,
                upsert=True,
                multi=False)
        except:
            if self.logger:
                self.logger.exception("Error writing image metadata to MongoDB")

        return image_metadata["_id"]

    def update_run_progress(self, run_position=0, image_name="", run_data=None):
        """Publish run status to the Redis database for Remote project"s benefit
        The run_data looks like this:
        {"status": "STARTED", "distance": 650.0, "phi": 0.0, "run_number": 1,
         "kappa": 0.0, "width": 0.5, "beamline": "C", "file_source": "PILATUS",
         "twotheta": 0.0, "start": 1, "prefix": "I5_GABA",
         "time": 0.20000000000000001,
         "directory": "/gpfs8/users/GU/Lodowski_C_Nov14/images/nick/H4_GABA/0_0",
         "total": 220, "omega": 100.0, "axis": "omega"}
        """

        self.logger.debug("Remote.update_run_progress")

        if image_name.endswith(".cbf"):
            my_repr = re.sub(r"\d{4}\.cbf", r"####.cbf", image_name)
        elif image_name.endswith(".img"):
            my_repr = re.sub(r"\d{3}\.img", r"###.img", image_name)

        if run_data == None:
            run_data = {}

        assembled_data = {"beamline"      : self.beamline,
                          "run_id"        : run_data.get("run_id", 0),
                          "run_position"  : run_position,
                          "run_start"     : run_data.get("start", 1),
                          "run_total"     : run_data.get("total", 0),
                          "directory"     : run_data.get("directory", ""),
                          "current_image" : image_name,
                          "omega_start"   : run_data.get("omega", 0.0),
                          "omega_delta"   : run_data.get("width", 0.0),
                          "exposure"      : run_data.get("time", 0.0),
                          "distance"      : run_data.get("distance", 0.0),
                          "date"          : datetime.datetime.now().isoformat(),
                          "repr"          : my_repr}

        # Publish data through redis
        self.logger.debug("Publishing run_update_%s %s",
            (self.settings.ID, json.dumps(assembled_data)))
        self.redis.publish("run_update_%s" % self.settings.ID, json.dumps(assembled_data))

        # Save to Mongo
        try:
            self.mongo_remote.run_data.update(
                {"run_id":run_data.get("run_id")},
                assembled_data,
                upsert=True,
                multi=False)
        # TODO - handle mongoDB exceptions
        except:
            if self.logger:
                self.logger.exception("Error writing run_data to MongoDB")

    def update_image_stats(self, result_db, wedges_db):
        """Publish image statistics to the Redis database for Remote project"s
        benefit
        """
        if self.logger:
            self.logger.debug("Remote.update_image_stats")
            self.logger.debug(result_db)
            self.logger.debug(wedges_db)

        # Data will go in here
        indexing_data = {}
        wedge = {}

        # If the indexing worked
        if result_db["labelit_status"] == "SUCCESS":
            indexing_data.update({"status"       : "indexed",
                                  "beamline"     : self.beamline,
                                  "fullname"     : result_db.get("fullname", 0),
                                  "image_id"     : result_db.get("image_id", 0),
                                  "pointgroup"   : result_db.get("labelit_spacegroup"),
                                  "a"            : result_db.get("labelit_a"),
                                  "b"            : result_db.get("labelit_b"),
                                  "c"            : result_db.get("labelit_c"),
                                  "alpha"        : result_db.get("labelit_alpha"),
                                  "beta"         : result_db.get("labelit_beta"),
                                  "gamma"        : result_db.get("labelit_gamma"),
                                  "resolution"   : result_db.get("distl_labelit_res"),
                                  "mosaicity"    : result_db.get("labelit_mosaicity"),
                                  "overloads"    : result_db.get("distl_overloads")})

            # If we have a normal strategy
            if result_db["best_norm_status"] == "SUCCESS":
                # Get the normal strategy wedge
                for wedge in wedges_db:
                    if wedge["strategy_type"] == "normal":
                        break
                indexing_data.update({"status"               : "normal",
                                      "normal_omega_start"   : wedge.get("phi_start", -1),
                                      "normal_omega_step"    : wedge.get("delta_phi", -1),
                                      "normal_number_images" : wedge.get("number_images", -1)
                                     })

                # If we have an anomalous strategy
                if result_db["best_anom_status"] == "SUCCESS":
                    # Get the anomalous strategy wedge
                    for wedge in wedges_db:
                        if  wedge["strategy_type"] == "anomalous":
                            break
                    indexing_data.update({"status"               : "all",
                                          "anom_omega_start"   : wedge.get("phi_start", -1),
                                          "anom_omega_step"    : wedge.get("delta_phi", -1),
                                          "anom_number_images" : wedge.get("number_images", -1)
                                         })

        # No indexing solution
        else:
            indexing_data.update({"status"   : "failure",
                                  "beamline" : self.beamline,
                                  "fullname" : result_db.get("fullname", 0),
                                  "image_id" : result_db.get("image_id", 0)
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
        Publish run statistics to the Redis database for Remote project"s benefit
        """

        if self.logger:
            self.logger.debug("Remote.update_run_stats")
            self.logger.debug(result_db)
            self.logger.debug(wedges)

        # Derive the session_id
        session_id = result_db["data_root_dir"].split("_")[-1]

        #
        integration_data = {}
        # Assign the basic data
        integration_data.update({"status"       : result_db.get("integrate_status").lower(),
                                 "beamline"     : self.beamline,
                                 "run_id"       : result_db.get("run_id", -1),
                                 "spacegroup"   : result_db.get("spacegroup", "P0"),
                                 "a"            : result_db.get("a", -1),
                                 "b"            : result_db.get("b", -1),
                                 "c"            : result_db.get("c", -1),
                                 "alpha"        : result_db.get("alpha", -1),
                                 "beta"         : result_db.get("beta", -1),
                                 "gamma"        : result_db.get("gamma", -1),
                                 "image_start"  : result_db.get("image_start", -1),
                                 "image_end"    : result_db.get("image_end", -1)})

        # Organize the wedges
        if wedges:
            for wedge in wedges:
                wtag = wedge.get("shell_type")
                if wtag in ("overall", "outer", "inner"):
                    integration_data.update(
                        {"res_low_"+wtag           : wedge.get("low_res", -1),
                         "res_high_"+wtag          : wedge.get("high_res", -1),
                         "completeness_"+wtag      : wedge.get("completeness", -1),
                         "multiplicity_"+wtag      : wedge.get("multiplicity", -1),
                         "i_sigi_"+wtag            : wedge.get("i_sigma", -1),
                         "rmeas_"+wtag             : wedge.get("r_meas", -1),
                         "rpim_"+wtag              : wedge.get("r_pim", -1),
                         "anom_completeness_"+wtag : wedge.get("anom_completeness", -1),
                         "anom_multiplicity_"+wtag : wedge.get("anom_multiplicity", -1),
                         "anom_rmeas_"+wtag        : wedge.get("r_meas_pm", -1),
                         "anom_rpim_"+wtag         : wedge.get("r_pim_pm", -1),
                         "anom_corr_"+wtag         : wedge.get("anom_correlation", -1),
                         "anom_slope_"+wtag        : wedge.get("anom_slope", -1),
                         "ref_total_"+wtag         : wedge.get("total_obs", -1),
                         "ref_unique_"+wtag        : wedge.get("unique_obs", -1)
                        })

        if self.logger:
            self.logger.debug("Sending integration_data to remote")
            self.logger.debug(integration_data)

        # Publish to redis connection
        #self.redis.publish("run_stats_"+self.beamline,data)

        # Save the data to redis
        j_data = json.dumps(integration_data)
        # Publish to redis connections
        self.redis.publish("run_stats_"+self.beamline, j_data)

        # Save to Mongo
        try:
            self.logger.debug("Saving to mongoDB")
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
            self.logger.info("Remote.add_quick_analysis_result")
            self.logger.info(result_data)

        # Add the image to the remote client
        node, image_uuid = self.add_image(result_data)

        # Assemble results to be published
        assemble = {"raster_uuid": result_data.get("raster_uuid", ""),
                    "image_uuid": image_uuid,
                    "node": node,
                    "status": "success",
                    "beamline": self.beamline,
                    "crystal_image": result_data.get("crystal_image", ""),
                    "fullname": result_data.get("fullname", ""),
                    "image_id": result_data.get("image_id", 0),
                    "image_number": result_data.get("image_number", 0),
                    "md2_x": result_data.get("md2_x", 0),
                    "md2_y": result_data.get("md2_y", 0),
                    "md2_z": result_data.get("md2_z", 0)
                   }

        # Publish to redis connection
        results = json.dumps(assemble)
        json_assemble = json.dumps(assemble)
        a_key = "quickanalysis_result:"+assemble.get("raster_uuid")+":"+ \
                str(assemble.get("image_number"))

        self.redis.publish("quickanalysis_result_%s" % self.beamline, results)

        # Save data in redis database
        self.redis.set(a_key, json_assemble)
        self.redis.expire(a_key, 8000000)  # Expire in a month
