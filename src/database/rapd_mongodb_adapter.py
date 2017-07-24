"""
This is an adapter for RAPD to connect to the results database, when it is a
MongoDB instance
"""

__license__ = """
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
__created__ = "2016-05-31"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

"""
To run a MongoDB instance in docker:
sudo docker run --name mongodb -p 27017:27017 -d mongo:3.4
"""

# Standard imports
import datetime
import json
import logging
import os
import threading

from bson.objectid import ObjectId
import numpy
import pymongo


CONNECTION_ATTEMPTS = 30

class Database(object):
    """
    Provides connection to MongoDB for Model.
    """

    client = None

    def __init__(self,
                 host=None,
                 port=27017,
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
    # Functions for connecting to the database                                 #
    ############################################################################
    def get_db_connection(self):
        """
        Returns a connection and cursor for interaction with the database.
        """

        # No client - then connect
        if not self.client:
            self.logger.debug("Connecting to MongDB at %s:%d", self.db_host, self.db_port)
            # Connect
            self.client = pymongo.MongoClient(host=self.db_host,
                                              port=self.db_port)

            # Not using user/password for now

        # Get the db
        db = self.client.rapd

        return db

    ############################################################################
    # Functions for sessions & users                                           #
    ############################################################################
    def get_session_id(self, data_root_dir):
        """
        Get the session _id for the input information. The entry will be made it does not yet exist.
        The data_root_dir must be input for this to work.

        Keyword arguments
        data_root_dir -- root of data for a session (ex. /raw/ID_16_05_25_uga_jjc)
        group_name -- name for a group (ex. uga_jjc) (default = None)
        session_name -- name for a session (ex. ID_16_05_25_uga_jjc) (default = None)
        """

        # Connect
        db = self.get_db_connection()

        # Retrieve the session id
        session_id = db.sessions.find_one({"data_root_dir":data_root_dir}, {"_id":1}).get("_id", False)

        if session_id:
            session_id = str(session_id)

        return session_id

    def create_session(self, data_root_dir, group_id=None):
        """
        Get the session _id for the input information. The entry will be made it does not yet exist.
        The data_root_dir must be input for this to work.

        Keyword arguments
        data_root_dir -- root of data for a session (ex. /raw/ID_16_05_25_uga_jjc)
        group_id -- id for a group (default = None)
        session_name -- name for a session (ex. ID_16_05_25_uga_jjc) (default = None)
        """

        # Connect
        db = self.get_db_connection()

        # Insert into the database
        result = db.sessions.insert_one({"data_root_dir": data_root_dir,
                                         "group_id": group_id,
                                         "timestamp": datetime.datetime.utcnow()})

        return str(result.inserted_id)


    ############################################################################
    # Functions for images                                                     #
    ############################################################################
    def add_image(self, data, return_type="id"):
        """
        Add new image to the MySQL database.

        Keyword arguments
        data -- dict with all the requisite parts
        return_type -- "boolean", "id", or "dict" (default = "id")
        """

        self.logger.debug(data)

        db = self.get_db_connection()

        # Add timestamp
        data["timestamp"] = datetime.datetime.utcnow()

        # Insert into db
        try:
            result = db.images.insert_one(data)
        # Image already entered
        except pymongo.errors.DuplicateKeyError:
            return False

        # Return the requested type
        if return_type == "boolean":
            return True
        elif return_type == "id":
            return str(result.inserted_id)
        elif return_type == "dict":
            result_dict = db.find_one({"_id":result.inserted_id})
            result_dict["_id"] = str(result_dict["_id"])
            return result_dict

    def get_image_by_image_id(self, image_id):
        """
        Returns a dict from the database when queried with image_id.

        image_id - the _id for the images collection. May be a string or ObjectId
        """

        self.logger.debug(image_id)

        # Get connection to database
        db = self.get_db_connection()

        # Query and return, transform _id to string
        return db.find_one({"_id":ObjectId(str(image_id))})

    #
    # Functions for processes                                                                      #
    #
    def add_plugin_process(self,
                           plugin_type=None,
                           request_type=None,
                           representation=None,
                           status=0,
                           display="show",
                           session_id=None,
                           data_root_dir=None):
        """
        Add an entry to the plugin_processes table - for keeping track of
        launched processes and their state

        Keyword arguments
        plugin_type -- type of plugin
        request_type -- request type, such as original
        representation -- how the request is represented to users
        status -- progress from 0 to 100 (default = 0) 1 = started,
                  100 = finished, -1 = error
        display -- display state of this process (default = show)
        session_id -- unique _id for session in sessions create_data_collections (default = None)
        data_root_dir -- unique root of the data for data collected at a site (default = None)
        """

        self.logger.debug("%s %s %s %s %s %s %s",
                          plugin_type,
                          request_type,
                          representation,
                          status,
                          display,
                          session_id,
                          data_root_dir)

        # Connect to the database
        db = self.get_db_connection()

        # Insert into db
        result = db.plugin_processes.insert_one({"plugin_type":plugin_type,
                                                 "display":display,
                                                 "status":status,
                                                 "representation":representation,
                                                 "request_type":request_type,
                                                 "session_id":session_id,
                                                 "data_root_dir":data_root_dir,
                                                 "timestamp":datetime.datetime.utcnow()})

        return str(result.inserted_id)

    def update_plugin_process(self,
                              plugin_process_id,
                              status=False,
                              display=False):
        """
        Add an entry to the plugin_processes table - for keeping track of
        launched processes and their state

        Keyword arguments
        plugin_process_id -- unique identifier for process
        status -- progress from 0 to 100 (default = 0) 1 = started,
                  100 = finished, -1 = error
        display -- display state of this process (default = show)
        """

        self.logger.debug("update_plugin_process %s %s %s", plugin_process_id, status, display)

        # Connect to the database
        db = self.get_db_connection()

        # Construct the values to be updated
        set_dict = {"timestamp":datetime.datetime.utcnow()}
        if status:
            set_dict["status"] = status

        if display:
            set_dict["display"] = display

        db.plugin_processes.update({"_id":ObjectId(str(plugin_process_id))},
                                   {"$set":set_dict})

        return True


    ############################################################################
    # Functions for results                                                    #
    ##########################################################################$#
    def parse_agent_type(self, agent_type):
        """
        Parse the agent_type string into something workable with the database


        agent_type                  result
        index+strategy:single       indexstrategy
        index+strategy:pair         indexstrategy


        Keyword argument
        agent_type -- corresponds to an agent_type as entered in the agent_processes
                      table, ex. index+strategy:single
        """

        return agent_type.split(":")[0].replace("+", "")

    def save_plugin_result(self, plugin_result):
        """
        Add and AUTOINDEX+STRATEGY result from the core plugin

        Keyword argument
        plugin_result -- dict of information from plugin - must have a process key pointing to a dict
        """

        self.logger.debug("save_plugin_result %s", plugin_result)

        # Connect to the database
        db = self.get_db_connection()

        # Add the current timestamp to the plugin_result
        plugin_result["timestamp"] = datetime.datetime.utcnow()

        # Add to results
        result = db.plugin_results.update(
            {"process.plugin_process_id":plugin_result["process"]["plugin_process_id"]},
            {"$set":plugin_result},
            upsert=True)

        self.logger.debug(result)

        # Work out the _id for the result
        # update
        if result.get("updatedExisting", True):
            return str(db.plugin_results.find_one(
                {"process.plugin_process_id":plugin_result["process"]["plugin_process_id"]},
                {"_id":1})["_id"])
        # upsert
        else:
            return str(result["upserted"])

    def getArrayStats(self,in_array,mode='float'):
        """
        return the max,min,mean and std_dev of an input array
        """
        self.logger.debug('Database::getArrayStats')

        if (mode == 'float'):
            narray = numpy.array(in_array, dtype=float)

        try:
            return(narray.max(), narray.min(), narray.mean(), narray.std())
        except:
            return(0, 0, 0, 0)

    ############################################################################
    # Functions for runs                                                       #
    ############################################################################
    def add_run(self, run_data, return_type="id"):
        """
        Add new run to the MySQL database.

        Keyword arguments
        data -- dict with all the requisite parts
        return_type -- "boolean", "id", or "dict" (default = "id")
        """

        self.logger.debug(run_data)

        # Add timestamp to the run_data
        run_data.update({"timestamp":datetime.datetime.utcnow()})

        db = self.get_db_connection()

        try:
            # Insert into db
            result = db.runs.insert_one(run_data)

            self.logger.debug("Inserted run _id", str(result.inserted_id))

            # Return the requested type
            if return_type == "boolean":
                return True
            elif return_type == "id":
                return str(result.inserted_id)
            elif return_type == "dict":
                result_dict = db.find_one({"_id":result.inserted_id})
                result_dict["_id"] = str(result_dict["_id"])
                return result_dict

        # Run already entered
        except pymongo.errors.DuplicateKeyError:
            return False

    def get_run(self,
                run_data=None,
                minutes=0,
                order="descending",
                return_type="boolean"):
        """
        Return information for runs that fit the data within the last minutes window. If minutes=0,
        no time limit. The return will either be a boolean, or a list of results.

        Match is performed on the directory, prefix, starting image number and
        total number of images.

        Keyword arguments
        run_data -- dict of run information (default None)
        minutes -- time window to look back into the data (default 0)
        order -- the order in which to sort the results, must be None, descending
                 or ascending (default descending)
        return_type -- "boolean", "id", "dict" (default = "boolean")
        """

        self.logger.debug("run_data:%s minutes:%d", run_data, minutes)

        # Get connection to database
        db = self.get_db_connection()

        # Order
        if order == "descending":
            order_param = -1
        elif order == "ascending":
            order_param = 1
        elif order == None:
            order_param = -1
        else:
            raise Exception("get_run_data order argument must be None, ascending, or descending")

        # Projection determined by return_type
        if return_type in ("boolean", "id"):
            projection = {"_id":1}
        else:
            projection = {}

        # Search parameters
        query = {"site_tag":run_data.get("site_tag", None),
                 "directory":run_data.get("directory", None),
                 "image_prefix":run_data.get("image_prefix", None),
                 "run_number":run_data.get("run_number", None),
                 "start_image_number":run_data.get("start_image_number", None),
                 "number_images":run_data.get("number_images", None)}

        # Limit to a time window
        if minutes != 0:
            time_limit = datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes)
            query.update({"timestamp":{"$lt":time_limit}})

        # self.logger.debug(query)
        # self.logger.debug(projection)
        # self.logger.debug(order_param)

        results = db.runs.find(query, projection).sort("file_ctime", order_param)

        # self.logger.debug("results.count() %d", results.count())

        # If no return, return a False
        if results.count() == 0:
            return False
        else:
            if return_type == "boolean":
                # self.logger.debug("Returning True")
                return True
            else:
                return results

    def query_in_run(self,
                     site_tag,
                     directory,
                     image_prefix,
                     run_number,
                     image_number,
                     minutes=0,
                     order="descending",
                     return_type="boolean"):
        """
        Return True/False or with list of data depending on whether the image information could
        correspond to a run stored in the database.

        Depending on the return_type, return could be True/False, a list of dicts, or a list of ids.

        Keyword arguments
        site_tag -- string describing site (default None)
        directory -- where the image is located
        image_prefix -- the image prefix
        run_number -- number for the run
        image_number -- number for the image
        minutes -- time window to look back into the data (default 0)
        return_type -- "boolean", "id", "dict" (default = "boolean")
        """

        self.logger.debug("query_in_run")

        # Order
        if order in ("descending", None):
            order_param = -1
        elif order == "ascending":
            order_param = 1
        else:
            raise Exception("get_run_data order argument must be None, ascending, or descending")

        # Get connection to database
        db = self.get_db_connection()

        # Search parameters
        query = {"site_tag":site_tag,
                 "directory":directory,
                 "image_prefix":image_prefix,
                 "run_number":run_number,
                 "start_image_number":{"$lte":image_number}}

        # Limit to a time window
        if minutes != 0:
            time_limit = datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes)
            query.update({"timestamp":{"$lt":time_limit}})

        # Projection determined by return_type
        if return_type in ("boolean", "id"):
            projection = {"_id":1, "start_image_number":1, "number_images":1}
        else:
            projection = {}

        self.logger.debug(query)
        self.logger.debug(projection)
        self.logger.debug(order_param)

        results = db.runs.find(query).sort("file_ctime", order_param)
        self.logger.debug(results.count())

        # Now filter for image_number inclusion
        filtered_results = []
        for result in results:
            self.logger.debug(result)
            if image_number <= (result["start_image_number"]+result["number_images"]+1):
                filtered_results.append(result)

        # If no return, return a False
        if len(filtered_results) == 0:
            self.logger.debug("Returning False")
            return False
        else:
            # boolean
            if return_type == "boolean":
                return True
            elif return_type == "dict":
                for result in filtered_results:
                    result["_id"] = str(result["_id"])
                return filtered_results
            elif return_type == "id":
                result_ids = []
                for result in filtered_results:
                    result_ids.append(str(result["_id"]))
                return result_ids

if __name__ == "__main__":

    print "rapd_mongodb_adapter.py.__main__"
