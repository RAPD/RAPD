"""
This is an adapter for RAPD to connect to the results database, when it is a
REDIS instance.

The connection should be automatically reconnecting, and a disconnection should
be fully recovered from if the disconnection is shorter than 
ATTEMPT_LIMIT * ATTEMPT_PAUSE seconds
"""

__license__ = """
This file is part of RAPD

Copyright (C) 2009-2018, Cornell University
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
#To run a MongoDB instance in docker:
#sudo docker run --name mongodb -p 27017:27017 -d mongo:3.4
"""

# Standard imports
import atexit
import datetime
import logging
import os
from pprint import pprint
import threading
import time

#from bson.objectid import ObjectId
import redis
from redis.sentinel import Sentinel

import utils.log
from utils.text import json
from bson.objectid import ObjectId

ATTEMPT_LIMIT = 3600
ATTEMPT_PAUSE = 1.0
CONNECTION_ATTEMPT_LIMIT = 3600


def connectionErrorWrapper(func):
    def wrapper(*args, **kwargs):
        attempts = 0
        while attempts < ATTEMPT_LIMIT:
            try:
                attempts += 1
                return func(*args, **kwargs)
                break
            except redis.exceptions.ConnectionError as e:
                # Pause for specified time
                print "try %d" % attempts
                time.sleep(ATTEMPT_PAUSE)
        else:
            args[0]._raise_ConnectionError(error)
    return wrapper

class Database(object):
    """
    Provides connection to REDIS for Model.
    """

    client = None

    def __init__(self, settings):

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

        # Used for a Redis connection pool
        self.redis_host = settings.get("REDIS_HOST", False)
        self.redis_port = settings.get("REDIS_PORT", False)
        self.redis_db = settings.get("REDIS_DB", False)

        # Used for a more reliable sentinal connection.
        self.sentinal_hosts = settings.get("REDIS_SENTINEL_HOSTS", False)
        self.sentinal_name = settings.get("REDIS_MASTER_NAME", False)

        if settings.get("REDIS_CONNECTION", False) == "pool":
            self.pool = True
        else:
            self.pool = False

        # A lock for troublesome fast-acting data entry
        #self.LOCK = threading.Lock()
    def connect_to_redis(self):
        if self.pool:
            return self.connect_redis_pool()
        else:
            return self.connect_redis_manager_HA()

    def connect_redis_pool(self):
        # Create a pool connection
        pool = redis.ConnectionPool(host=self.redis_host,
                                    port=self.redis_port,
                                    db=self.redis_db)
        # Save the pool for a clean exit.
        self.pool = redis.Redis(connection_pool=pool)
        # The return the connection
        return self.pool

    def connect_redis_manager_HA(self):
        return (Sentinel(self.sentinal_hosts).master_for(self.sentinal_name))

    def stop(self):
        pass
        #if self.pool:
        #    self.pool.close()


class RedisClient:
    """
    Provide an interface using which to communicate with a Redis server.

    A new connection to the server is created by each class instance.

    Custom exception hierarchy:
    Error
     +-- ConnectionError
     +-- WaitTimeoutError
    """

    socket_timeout = 1
    pubsubs = {}
    sentinel = None

    class Error(Exception):
        pass
        # print "Error"

    class ConnectionError(Error):
        pass
        # print "ConnectionError"

    class WaitTimeoutError(Error):
        def __str__(self):
            return self.msg
        def __init__(self, msg, key, value, timeout):

            msg = str(msg) # in the event msg was an Exception, for example
            self.msg = msg
            self.key = key
            self.value = value
            self.timeout = timeout

            super(RedisClient.WaitTimeoutError, self).__init__(self, msg) # this raises the exception
            # Note: In Python 2.x, self.__class__ should not be used in place of base class name.

    def state_connection(self):
        """
        Return a dict containing keys and values providing information about
        the state of the connection to the Redis server.
        """

        self.logger.debug("state_connection")

        # conn_kwargs = self._pool.connection_kwargs
        # server_addr = (conn_kwargs["host"], conn_kwargs["port"])

        # state = {"Server address": "{}:{}".format(*server_addr),}
        state = {}

        # Do ping test
        try:
            # connection = redis.Redis(connection_pool=self._pool)
            state["Server pingable"] = self.redis.ping() # returns True
        except redis.exceptions.ConnectionError: # as e:
            #self.logger.error("{} Console Redis ping failure: {}".format(tools.cm_name(), e))
                # intentionally not self.logger.exception
            state["Server pingable"] = False

        # # Test availability of a key
        # try:
        #     self["MONO_SV"]
        # except self.ConnectionError: # as e:
        #     #self.logger.error("{} Console Redis test failure: {}".format(tools.cm_name(), e))
        #         # intentionally not self.logger.exception
        #     state["Test result"] = "Failed"
        # else:
        #     state["Test result"] = "Passed"

        return state

    def state_server(self):
        """Return a dict containing keys and values providing some properties
        about the the Redis server."""

        self.logger.debug("state_server")

        try:
            # connection = redis.Redis(connection_pool=self._pool)
            info = self.redis.info()
        except redis.exceptions.ConnectionError as e:
            self.logger.error("Redis info acquisition failure: {}".format(e))
            # intentionally not self.logger.exception
            state = {}
        else:
            state = {"Number of connected clients": info["connected_clients"],
                     "Redis version": info["redis_version"],
                     "Uptime": datetime.datetime.utcnow() - datetime.datetime.utcfromtimestamp(time.time() - info["uptime_in_seconds"]),
                     }

        return state

    def __init__(self,
                 host="localhost",
                 port=6379,
                 db=0, 
                 password=None, 
                 sentinels=None,
                 master=None,
                 settings=None,
                 logger=False):
        """Initialize the client."""

        # Save passed-in variables
        self.host =      host
        self.port =      port
        self.db =        db
        self.password =  password 
        self.sentinels = sentinels
        self.master =    master
        self.logger =    logger

        # Use the RAPD CONTROL_DATABASE_SETTINGS object
        if settings:
            # Sentinel
            if settings["REDIS_CONNECTION"] == "sentinel":
                self.host =      None
                self.port =      None
                self.db =        None
                self.password =  settings["REDIS_PASSWORD"] 
                self.sentinels = settings["REDIS_SENTINEL_HOSTS"] 
                self.master =    settings["REDIS_MASTER_NAME"] 
            # Standard
            else:
                self.host =      settings["REDIS_HOST"]
                self.port =      settings["REDIS_PORT"]
                self.db =        settings["REDIS_DB"]
                self.password =  settings["REDIS_PASSWORD"] 
                self.sentinels = None
                self.master =    None

        self._ConnectionError_last_log_time = float("-inf")

        # Connect to server
        self._connect_lock = threading.Lock()
        self._connect() # "with self._connect_lock:" is not necessary in __init__
        atexit.register(self._disconnect)

    ###############
    # ADMIN Methods
    ###############

    def _connect(self):
        """Connect to server."""

        # self.logger.debug(tools.cm_name())

        socket_timeout = self.socket_timeout

        # Sentinel connection
        if self.sentinels:
            self.sentinel = Sentinel(self.sentinels)

            # Assign master connection to self.redis
            self.redis = self.sentinel.master_for(self.master)

        # Standard connection
        else:
            attempt_count = 0
            while attempt_count < CONNECTION_ATTEMPT_LIMIT:
                try:
                    # Connect
                    self.redis = redis.Redis(host=self.host,
                                             port=self.port,
                                             db=self.db,
                                             password=self.password)
                    # self._pool = redis.ConnectionPool(host=self.host, port=self.port, db=0)
                    
                    # Make sure redis server is up
                    _ = self.redis.ping()
                    break
                    # self._connection = redis.Redis(host, socket_timeout=socket_timeout)
                    # redis module reconnects automatically as needed.
                    # socket_timeout is not set to a higher value because it blocks.
                except redis.exceptions.ConnectionError as e:
                    print "except"
                    self.logger.debug("Connection error {}".format(e))
                    time.sleep(1)
                    attempt_count += 1
                    # self._raise_ConnectionError(e)

        # # Make sure redis server is up
        # try:
        #     _ = self.redis.ping()
        # except redis.sentinel.MasterNotFoundError as error:
        #     self._raise_ConnectionError(error)

    def _disconnect(self):
        """Disconnect from server."""

        # self.logger.debug(tools.cm_name())

        try:
            pool = self._pool
        except AttributeError:
            pass
        else:
            pool.disconnect()
            #self.logger.info("{} Disconnected Redis client from Redis server {host}:{port}.".format(tools.cm_name(), **connection.connection_pool.connection_kwargs))

    def _raise_ConnectionError(self, exc):
        """
        Raise ConnectionError exception with an error message corresponding
        to the provided exception.
        """

        # TODO: Implement functionality of _raise_ConnectionError directly into ConnectionError exception instead. Delete method definition.

        err_msg = str(exc)
        if err_msg: err_msg = ": {}".format(err_msg)
        err_msg = "Redis connection error{}".format(err_msg)

        # Conditionally log error
        # log_interval = backend.settings.redis["Console"]["ConnectionError log interval"]
        # if time.time() > (self._ConnectionError_last_log_time + log_interval):
        #     self._ConnectionError_last_log_time = time.time()
        #     logger = self.logger.info
        # else:
        logger = self.logger.debug
        logger("{}".format(err_msg))

        raise self.ConnectionError(err_msg)

    def discover_master(self):
        """
        Return the master instance (host, ip)
        """

        if self.sentinel and self.master:
            attempts = 0
            while attempts < ATTEMPT_LIMIT:
                try:
                    attempts += 1
                    master = self.sentinel.discover_master(self.master)
                    break
                except redis.sentinel.MasterNotFoundError as e:
                    # Pause for specified time
                    print "try %d" % attempts
                    time.sleep(ATTEMPT_PAUSE)
            else:
                self._raise_ConnectionError(e)

            return master 
        else:
            self._raise_ConnectionError("Sentinels not properly defined")

    def discover_slaves(self):
        """
        Return the slave instances [(host, ip),]
        """

        if self.sentinel and self.master:
            attempts = 0
            while attempts < ATTEMPT_LIMIT:
                try:
                    attempts += 1
                    master = self.sentinel.discover_slaves(self.master)
                    break
                except redis.sentinel.SlaveNotFoundError as e:
                    # Pause for specified time
                    print "try %d" % attempts
                    time.sleep(ATTEMPT_PAUSE)
            else:
                self._raise_ConnectionError(e)

            return master 
        else:
            self._raise_ConnectionError("Sentinels not properly defined")


    #############
    # GET Methods
    #############

    def __getitem__(self, key, return_dict=False):
        """
        Return the value of the specified key(s).

        key can be either a str, or a tuple or list of strs. It is recommended
        that key(s) be present in backend.redis_console_keys.keys.

        `transform` indicates whether to apply transformations to the value
        before returning it, as defined in the self._transform_value method.

        `return_dict` indicates whether to return values in a dict. If True,
        the keys in the returned dict match the specified key(s).
        """

        # Get value(s)
        if isinstance(key, str):
            return self.get(key, return_dict)
        elif isinstance(key, tuple) or isinstance(key, list):
            return self.mget(key, return_dict)
    get = __getitem__

    @connectionErrorWrapper
    def get(self, key, return_dict=False):
        """
        Return the value of `key`.

        `return_dict` indicates whether to return values in a dict. If True,
        the keys in the returned dict match the specified key(s).
        """

        # self.logger.debug("get key:{} return_dict:{}".format(key, return_dict))

        # Retrieve value
        value = self.redis.get(key)
        
        # Wrap in dict if requested
        return ({key: value} if return_dict else value)

    # def get(self, key, return_dict=False):
    #     """
    #     Return the value of `key`.

    #     `return_dict` indicates whether to return values in a dict. If True,
    #     the keys in the returned dict match the specified key(s).
    #     """

    #     # self.logger.debug("get key:{} return_dict:{}".format(key, return_dict))

    #     # Retrieve value
    #     attempts = 0
    #     while attempts < ATTEMPT_LIMIT:
    #         try:
    #             attempts += 1
    #             value = self.redis.get(key)
    #             break
    #         except redis.exceptions.ConnectionError as e:
    #             # Pause for specified time
    #             print "try %d" % attempts
    #             time.sleep(ATTEMPT_PAUSE)
    #     else:
    #         self._raise_ConnectionError(e)

    #     return ({key: value} if return_dict else value)

    @connectionErrorWrapper
    def mget(self, keys, return_dict=False):
        """
        Return the values of the sequence `keys`.

        `transform` indicates whether to apply transformations to the value
        before returning it, as defined in the self._transform_value method.

        `return_dict` indicates whether to return values in a dict. If True,
        the keys in the returned dict match the specified key(s).
        """

        # Retrieve values
        values = self.redis.mget(keys)

        return (dict(zip(keys,values)) if return_dict else values)

    # def mget(self, keys, return_dict=False):
    #     """
    #     Return the values of the sequence `keys`.

    #     `transform` indicates whether to apply transformations to the value
    #     before returning it, as defined in the self._transform_value method.

    #     `return_dict` indicates whether to return values in a dict. If True,
    #     the keys in the returned dict match the specified key(s).
    #     """

    #     # self.logger.log(5, "{} keys:{} transform:{} return_dict:{}".format(tools.cm_name(), keys, transform, return_dict))

    #     # Retrieve values
    #     try:
    #         connection = redis.Redis(connection_pool=self._pool)
    #         values = connection.mget(keys)
    #     except redis.exceptions.ConnectionError as e:
    #         self._raise_ConnectionError(e)
    #     # self.logger.log(5 if transform else logging.DEBUG, "{} keys:{} values:{}".format(tools.cm_name(), keys, repr(values)))

    #     # Transform and return values
    #     # if transform: values = self._transform_value(keys, values)
    #     return (dict(zip(keys,values)) if return_dict else values)

    #############
    # SET Methods
    #############

    @connectionErrorWrapper
    def set(self, key, value):
        """
        Set the indicated key value pair.
        """

        self.logger.debug("set key:{} value:{}".format(key, value))

        self.redis.set(key, str(value))

    # def set(self, key, value):
    #     """
    #     Set the indicated key value pair.
    #     """

    #     self.logger.debug("set key:{} value:{}".format(key, value))

    #     # Set
    #     attempts = 0
    #     while attempts < ATTEMPT_LIMIT:
    #         try:
    #             attempts += 1
    #             self.redis.set(key, str(value))
    #             break
    #         except redis.exceptions.ConnectionError as error:
    #             # Pause for specified time
    #             print "try %d" % attempts
    #             time.sleep(ATTEMPT_PAUSE)
    #     else:
    #         self._raise_ConnectionError(error)

    __setitem__ = set

    @connectionErrorWrapper
    def mset(self, mapping):
        """
        Set the key value pairs which are in the dict `mapping`.
        """

        # self.logger.debug("{} mapping:{}".format(tools.cm_name(), mapping))

        # Get the mapping ready
        mapping = {k: str(v) for k, v in mapping.items()}

        # Set in redis
        self.redis.mset(mapping)


    # def mset(self, mapping):
    #     """
    #     Set the key value pairs which are in the dict `mapping`.
    #     """

    #     # self.logger.debug("{} mapping:{}".format(tools.cm_name(), mapping))

    #     mapping = {k: str(v) for k, v in mapping.items()}
    #     # Set
    #     attempts = 0
    #     while attempts < ATTEMPT_LIMIT:
    #         try:
    #             attempts += 1
    #             self.redis.mset(mapping)
    #             break
    #         except redis.exceptions.ConnectionError as error:
    #             # Pause for specified time
    #             # print "try %d" % attempts
    #             time.sleep(ATTEMPT_PAUSE)
    #     else:
    #         self._raise_ConnectionError(error)

    ##############
    # LIST Methods
    ##############
    @connectionErrorWrapper
    def lpush(self, key, value):
        """
        LPUSH a values onto a given list
        """
        self.redis.lpush(key, value)

    @connectionErrorWrapper
    def rpop(self, key):
        """
        RPOP a value off a given list
        """
        value = self.redis.rpop(key)
        return value
               

    ################
    # PUBSUB Methods
    ################
    @connectionErrorWrapper
    def publish(self, key, value):
        """
        Publish a value on a given key
        """

        # print "publish {} {}".format(key, value)
        self.redis.publish(key, value)

    # def publish(self, key, value):
    #     """
    #     Publish a value on a given key
    #     """

    #     # print "publish {} {}".format(key, value)

    #     attempts = 0
    #     while attempts < ATTEMPT_LIMIT:
    #         try:
    #             attempts += 1
    #             self.redis.publish(key, value)
    #             break
    #         except redis.exceptions.ConnectionError as error:
    #             # Pause for specified time
    #             print "try %d" % attempts
    #             time.sleep(ATTEMPT_PAUSE)
    #     else:
    #         self._raise_ConnectionError(error)

    @connectionErrorWrapper
    def get_message(self, id):
        """
        Get message on pubsub connection
        """

        message = self.pubsubs[id].get_message()

        return message

    # def get_message(self, id):
    #     """
    #     Get message on pubsub connection
    #     """

    #     attempts = 0
    #     while attempts < ATTEMPT_LIMIT:
    #         try:
    #             attempts += 1
    #             message = self.pubsubs[id].get_message()
    #             break
    #         except redis.exceptions.ConnectionError as error:
    #             # Pause for specified time
    #             print "try %d" % attempts
    #             time.sleep(ATTEMPT_PAUSE)
    #     else:
    #         self._raise_ConnectionError(error)

    #     return message

    def get_pubsub(self):
        """
        Returns a pubsub connection - no error is triggered if no connection
        """

        # Create the pubsub object
        ps = self.redis.pubsub()

        # Give it an id
        id = len(self.pubsubs) + 1
        ps._id = id

        # Store a reference
        self.pubsubs[id] = ps

        # Return the id
        return id

    @connectionErrorWrapper
    def psubscribe(self, id=False, pattern=False):
        """
        Add pattern subscription to a pubsub object and return id of pubsub object
        """

        # No id passed in - create pubsub object
        if not id:
            id = self.get_pubsub()

        self.pubsubs[id].psubscribe(pattern)

        return id

    # def psubscribe(self, id=False, pattern=False):
    #     """
    #     Add pattern subscription to a pubsub object and return id of pubsub object
    #     """

    #     # No id passed in - create pubsub object
    #     if not id:
    #         id = self.get_pubsub()

    #     attempts = 0
    #     while attempts < ATTEMPT_LIMIT:
    #         try:
    #             attempts += 1
    #             self.pubsubs[id].psubscribe(pattern)
    #             break
    #         except redis.exceptions.ConnectionError as error:
    #             # Pause for specified time
    #             # print "try %d" % attempts
    #             time.sleep(ATTEMPT_PAUSE)
    #     else:
    #         self._raise_ConnectionError(error)

    #     return id

    @connectionErrorWrapper
    def subscribe(self, id=None, channel=None):
        """
        Add subscription to a pubsub object and return id of pubsub object
        """

        if channel:

            # No id passed in - create pubsub object
            if not id:
                id = self.get_pubsub()

            return id

    # def subscribe(self, id=None, channel=None):
    #     """
    #     Add subscription to a pubsub object and return id of pubsub object
    #     """

    #     if channel:

    #         # No id passed in - create pubsub object
    #         if not id:
    #             id = self.get_pubsub()

    #         attempts = 0
    #         while attempts < ATTEMPT_LIMIT:
    #             try:
    #                 attempts += 1
    #                 self.pubsubs[id].subscribe(channel)
    #                 break
    #             except redis.exceptions.ConnectionError as error:
    #                 # Pause for specified time
    #                 # print "try %d" % attempts
    #                 time.sleep(ATTEMPT_PAUSE)
    #         else:
    #             self._raise_ConnectionError(error)

    #         return id

    ###############
    # WATCH Methods
    ###############

#     def watch(self, key, duration=float("inf"), interval=0.5):
#         """
#         Print the untransformed and transformed values of the specified key for
#         the indicated duration.

#         key can be a str, or a tuple or list of keys.

#         duration is the number of seconds for which to watch the key.

#         interval is the number of seconds to sleep in between repetitions.
#         """

#         # self.logger.debug("{} key(s):{}, duration:{}, interval:{}".format(tools.cm_name(), key, duration, interval))

#         start_time = time.time()
#         deadline = start_time + duration

#         try:
#             while time.time() < deadline:
#                 dict_untransformed = self.get(key, transform=False, return_dict=True)
#                 dict_transformed = self.get(key, transform=True, return_dict=True)
#                 elapsed_time = time.time() - start_time
#                 print("[{}] (at {:.1f}s) (Beamline {}):\n\tUntransformed: {}\n\tTransformed:   {}".format(time.asctime(), elapsed_time, self._beamline, dict_untransformed, dict_transformed))
#                 time.sleep(interval)
#         except (KeyboardInterrupt, SystemExit):
#             pass

#     def wait(self, key, condition, timeout=float("inf"), interval=0.5, delay=0,
#              true_period=None, use_dict=False):
#         """
#         Wait while the condition is False (i.e. until the condition is True)
#         for the value(s) of the key(s), up to timeout, returning values(s).

#         key can be either a str, or a tuple or list of keys.

#         condition is the desired state(s) at which to stop waiting. It is
#         expressed as a callable function or their sequence. These accept one
#         input argument, i.e. the value(s) of the specified key(s), and return
#         a value which is evaluated as a bool.

#         timeout is the maximum number of seconds for which to monitor the key.
#         self.WaitTimeoutError exception is raised if the condition is still
#         false at the end of the timeout period.

#         interval is the number of seconds to sleep in between checks.

#         delay is the number of seconds to sleep before starting to test
#         condition for the first time. It is independent of the timeout period.

#         true_period is the minimum number of seconds for which the condition
#         must be true. This is implemented by rechecking the condition after
#         each interval of time. If None, the condition must be true once.

#         use_dict indicates whether to retrieve and test the value(s) of the
#         specified key(s) as a dict. If True, condition must accordingly accept
#         a dict.

#         Examples:
#         wait("CENTERING_READY_SV", lambda v: v=="ready", 4*60)
#         wait(("XINBAND_SV", "YINBAND_SV"), lambda v: v[0]==v[1]=="IN")
#         wait(("PUCK_SV", "SAMP_SV"),
#              lambda v: (v["PUCK_SV"]=="A" and v["SAMP_SV"]==1),
#              use_dict=True)
#         """

#         # Note: condition is a function rather than an equality test, as a
#         #       function allows for richer comparisons.

#         # self.logger.debug("{} key(s):{}, timeout:{}, interval:{}, delay:{}, true_period:{}".format(tools.cm_name(), key, timeout, interval, delay, true_period))

#         if (not backend.settings.active) and (timeout > 1):
#             # self.logger.info("{} Because application is not running in active mode, timeout will be reduced from {} to 0.".format(tools.cm_name(), timeout))
#             timeout = 0 # also noted in log message above

#         condition_is_callable = callable(condition)
#         condition_is_callable_sequence = ((isinstance(condition, list) or isinstance(condition, tuple))
#                                           and all((callable(c) for c in condition)))
#         if not (condition_is_callable or condition_is_callable_sequence):
#             raise TypeError("The specified condition must be either a callable, or a tuple or list sequence of callables.")

#         time.sleep(delay)
#         deadline = time.time() + timeout

#         condition_true = False

#         while True:
#             value = self.get(key, return_dict=use_dict)
#             self.logger.debug("Value is {}".format(value))
#             # Determine if condition is true or false
#             if condition_is_callable:
#                 condition_true = condition(value)
#             elif condition_is_callable_sequence:
#                 condition_true = all((c(value) for c in condition))
#             # else TypeError is previously raised

#             # Handle the four possible logical conditions
#             if condition_true and (not true_period):
#                 return value
#             elif condition_true and true_period:
#                 try:
#                     if time.time() > true_period_end: #@UndefinedVariable
#                         return value
#                 except NameError:
#                     true_period_end = time.time() + true_period
#             elif (not condition_true) and true_period:
#                 try: del true_period_end #@UndefinedVariable
#                 except NameError: pass
# #           elif (not condition_true) and (not true_period):
# #               pass

#             # Raise exception if deadline is crossed
#             if time.time() > deadline:
#                 true_period_msg = " for the required true period" if true_period else ""
#                 msg = "Timeout occurred waiting for the required condition(s) to return True{}. [key(s):{}, timeout:{}, interval:{}, true_period:{}, last_value(s):{}]".format(true_period_msg, key, timeout, interval, true_period, value)
#                 logger = self.logger.warning #if backend.settings.active else self.logger.info
#                 # logger("{} {}".format(tools.cm_name(), msg))
#                 raise self.WaitTimeoutError(msg, key, value, timeout)

#             time.sleep(interval)

    def print_items(self):
        """
        Print all key-value pairs for the current server and beamline.

        This method is for debugging only.
        """

        # self.logger.debug(tools.cm_name())
        # self._reconnect_if_beamline_mismatch()

        # Create a list of keys
        keys = [key for key, key_dict in backend.redis_console_keys.keys.items() if self._beamline in key_dict["bl"]] # @UnusedVariable
        connection = redis.Redis(connection_pool=self._pool)
        keys = list(connection.keys())
        keys.sort()

        # Print keys and their values
        for key in keys:
            print_str = "\t{}:{}".format(self._beamline, key)
            try:
                desc = backend.redis_console_keys.keys[key]["desc"]
                if desc: print_str += " ({})".format(desc)
            except KeyError:
                pass
            try:
                backend.redis_console_keys.keys[key]["transform"]
            except KeyError:
                print_str += " (not transformed)"
            try:
                print_str += ": {}".format(repr(self[key]))
            except Exception as e:
                self.logger.exception("An exception occurred while getting value of key {}. The exception is: {}".format(key, e))
            else:
                print(print_str)

def main():
    """
    The main process docstring
    This function is called when this module is invoked from
    the commandline
    """

    print "main"

    # commandline_args = get_commandline()
    # print commandline_args

    # Logger
    logger = utils.log.get_logger(logfile_dir="./",
                                  logfile_id="rapd_redis",
                                  level=10,
                                  console=True)


    RC = RedisClient(host="127.0.0.1", port="6379", logger=logger) #, password="foobared", logger=logger)
    pprint(RC.state_server())
    pprint(RC.state_connection())
    counter = 0
    # ps = RC.get_pubsub()
    # RC.subscribe(id=ps, channel="foo")
    # RC.publish("foo", "bar{}".format(counter))
    while True:
        time.sleep(1)
        # print RC.get("foo")
        # RC.set("foo", counter)
        # print RC.get_message(ps)
        print RC.lpush("fool", "bar%d" % counter)
        
        counter += 1

    """
    RC = RedisClient(sentinels=[("164.54.212.172", 26379)], master="remote_master", logger=logger)
    ps = RC.get_pubsub()
    RC.subscribe(id=ps, channel="foo")
    counter = 0 
    while True:
        time.sleep(1)
        
        # print RC.discover_master()
        # print RC.discover_slaves()
        # print RC.set("foo", counter)
        # print RC.get("foo")
        # RC.publish("foo", "bar{}".format(counter))
        print RC.get_message(ps)

        counter += 1
    """

if __name__ == "__main__":
    main()
