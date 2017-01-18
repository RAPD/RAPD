"""
This file is part of RAPD

Copyright (C) 2015-2017, Cornell University
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

__created__ = "2015-01-01"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

import redis
import sys
import time
from functools import wraps
import threading
import pprint
import Queue

__version__ = "1.0.1"

MAXSIZE = 0
RECONNECT_TRIES = 60
RECONNECT_PAUSE = 1


PP = pprint.PrettyPrinter()
def pp(item):
    PP.pprint(item)


class SentinelWatcher(threading.Thread):
    """
    Separate thread that maintains an active ping on the preferred sentinel
    and executes the passed in on_error function when the sentinel instance is
    not available
    """
    def __init__(self,
                 host="127.0.0.1",
                 port=26379,
                 name="testmaster",
                 password=False,
                 on_error=None):

        print "SentinelWatcher.__init__ host:%s port:%d name:%s password:%s" % (host,port,name,password)

        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.name = name
        self.password = password
        self.on_error = on_error

        self.GO = True

        self.start()

    def run(self):

        print "SentinelWatcher.run"

        # Connect to sentinel
        self.sentinel = redis.Redis(self.host,self.port)

        counter = 0
        while self.GO:
            counter += 1
            try:
                status = self.sentinel.ping()
                #if counter % 60 == 0:
                #   TODO - add reference for updating the alternate sentinels info
                time.sleep(1)
            except redis.ConnectionError:
                self.GO = False
                if self.on_error:
                    self.on_error()

        print "Exiting SentinelWatcher main loop"

class SentinelListener(threading.Thread):
    """
    Separate thread which listens to the sentinel pubsub activity and acts on
    messages it finds important via the passed-in actions
    """

    def __init__(self,
                 host="127.0.0.1",
                 port=26379,
                 name="testmaster",
                 password=False,
                 on_master=None):

        print "SentinelListener.__init__ host:%s port:%d name:%s password:%s" % (host,port,name,password)

        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.name = name
        self.password = password
        self.on_master = on_master

        self.GO = True

        self.start()

    def run(self):

        print "SentinelListener.run"

        # Connect to sentinel
        self.sentinel = redis.Redis(self.host,self.port)
        # pp(self.sentinel.info())

        # Subscribe
        pubsub = self.sentinel.pubsub()
        pubsub.psubscribe("*")

        while self.GO:
            message = pubsub.get_message()
            if message:
                # print "[SentinelListener]",time.time(),message
                if message["channel"] == "+switch-master":
                    name,old_ip,old_port,new_ip,new_port = message["data"].split()
                    print "NEW MASTER"
                    if self.on_master:
                        self.on_master()
            time.sleep(0.1)
        print "Exiting SentinelListener main loop"


class PipelineConnection(redis.client.StrictPipeline):

    def __init__(self, *args, **kwargs):
        super(PipelineConnection,self).__init__(*args, **kwargs)

def executePipelineCommand(func):
    """
    Decorator that will cause the function to be executed on the proper
    redis node. In the case of a Connection failure, it will attempt to find
    a new master node and perform the action there.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        nodeFunc = getattr(self.get_pipeline_connection(), func.__name__)
        print nodeFunc,args,kwargs
        try:
            return nodeFunc(*args, **kwargs)
        except redis.ConnectionError:
            # if it fails a second time, then sentinel hasn't caught up, so
            # we have no choice but to fail for real.
            self.master_conn = False
            nodeFunc = getattr(self.get_pipeline_connection(), func.__name__)
            return nodeFunc(*args, **kwargs)
    return wrapper

class PubsubConnection(redis.client.PubSub):

    def __init__(self, *args, **kwargs):
        super(PubsubConnection,self).__init__(*args, **kwargs)

def executeRedisPubsubCommand(func):
    """
    Decorator that will cause the function to be executed on the proper
    redis node. In the case of a Connection failure, it will attempt to find
    a new master node and perform the action there.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            nodeFunc = getattr(self.get_pubsub_connection(), func.__name__)
            # print nodeFunc,args,kwargs
            return nodeFunc(*args, **kwargs)
        # This is error observed from loss of connection from get_message
        except AttributeError:
            print "AttributeError"
            return None

        #master_conn is down or has gone down in the middle of this transaction
        except (redis.ConnectionError):
            print "redis.ConnectionError"
            return None

    return wrapper

class RedisConnection(redis.StrictRedis):

    def __init__(self,*args,**kwargs):
        super(RedisConnection,self).__init__(*args,**kwargs)

def executeRedisCommand(func):
    """
    Decorator that will cause the function to be executed on the proper
    redis node. In the case of a Connection failure, it will attempt to find
    a new master node and perform the action there.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            nodeFunc = getattr(self.get_master_connection(), func.__name__)
            #print nodeFunc,args,kwargs
            return nodeFunc(*args, **kwargs)

        # master_conn is not up
        except (AttributeError):
            print "AttributeError"
            if self.status == "starting":
                print "Still in startup"
                # Stash the command
                print "Stashing %s" % (str((func.__name__,args,kwargs)))
                self.command_queue.put((func.__name__,args,kwargs),False)
            elif self.status == "down":
                print "Connection down"
                # Stash the command
                print "Stashing %s" % (str((func.__name__,args,kwargs)))
                self.command_queue.put((func.__name__,args,kwargs),False)
            return False

        # master_conn is down or has gone down in the middle of this transaction
        except (redis.ConnectionError):
            print "redis.ConnectionError",self.status
            if self.status == "down":
                print "Connection is down"
                # Stash the command
                print "Stashing %s" % (str((func.__name__,args,kwargs)))
                self.command_queue.put((func.__name__,args,kwargs),False)
            elif self.status == "up":
                print "Connection went down"
                # Stash the command
                print "Stashing %s" % (str((func.__name__,args,kwargs)))
                self.command_queue.put((func.__name__,args,kwargs),False)
            return False

    return wrapper


class RedisManager():

    def __init__(self,
                 sentinel_host=False,
                 sentinel_port=False,
                 master_name=False,
                 master_password=False,
                 verbose=False):

        self.verbose = verbose

        if self.verbose:
            print "RedisManager.__init__"

        self.sentinel_host =   False
        self.sentinel_port =   False
        self.master_name =     False
        self.master_password = False

        self.sentinel =        False
        self.sentinels =       []

        self.master_conn =       False
        self.pubsub_conn =       False
        self.sentinel_watcher =  False
        self.sentinel_listener = False
        self.status =            "starting" #starting,up,down

        self.command_queue = Queue.Queue(MAXSIZE)

        # If passed in sentinel information, add it
        if (sentinel_host and sentinel_port):
            self.add_sentinel(sentinel_host=sentinel_host,
                              sentinel_port=sentinel_port,
                              master_name=master_name,
                              master_password=master_password)



    def add_sentinel(self,
                     sentinel_host="127.0.0.1",
                     sentinel_port=36379,
                     master_name="testmaster",
                     master_password="foobared"):

        if self.verbose:
            print "RedisManager.add_sentinel host:%s port:%d name:%s pass:%s" % (
                  master_password,sentinel_port,master_name,master_password)

        # Save sentinel info
        self.sentinel_host =    sentinel_host
        self.sentinel_port =    sentinel_port
        self.master_name =      master_name
        self.master_password =  master_password

        # Connect to sentinel
        self.sentinel = redis.Redis(self.sentinel_host,self.sentinel_port)

        # Make sure it is a sentinel
        s_info = self.sentinel.info()
        if s_info["redis_mode"] != "sentinel":
            print "Error - %s:%d is not a sentinel instance" % (sentinel_host,
                  sentinel_port)
            raise redis.ConnectionError("%s:%d is not a sentinel instance" %
                  (host,port))

        # Get the other sentinels in the quorum
        _ = self.get_alternate_sentinels()

        # If there is already a watcher, clear it
        if self.sentinel_watcher:
            self.sentinel_watcher.GO = False
            del self.sentinel_watcher

        # If there is already a listener, clear it
        if self.sentinel_listener:
            self.sentinel_listener.GO = False
            del self.sentinel_listener

        # Start SentinelWatcher & SentinelListener
        self.sentinel_watcher = SentinelWatcher(sentinel_host,
                                                sentinel_port,
                                                master_name,
                                                master_password,
                                                self.connect_to_alternate_sentinel)
        # Start SentinelListener
        self.sentinel_listener = SentinelListener(sentinel_host,
                                                  sentinel_port,
                                                  master_name,
                                                  master_password,
                                                  self.reconnect_master_connection)

        # Connect to master redis instance
        self.reconnect_master_connection()

        return True

    def get_sentinel_info(self):

        if self.verbose:
            print "RedisManager.get_sentinel_info"

        if not self.sentinel:
            raise(AttributeError("RedisManager has no sentinel"))

        try:
            sentinel_info = self.sentinel.info()
        except redis.exceptions.ConnectionError:
            print "Cannot contact sentinel"
            status = self.connect_to_alternate_sentinel()
            if status:
                return self.get_sentinel_info()
            else:
                redis.exceptions.ConnectionError("Cannot connect to alternate sentinel instance")
        return sentinel_info


    def connect_to_alternate_sentinel(self):

        if self.verbose:
            print "RedisManager.connect_to_alternate_sentinel"

        if not self.sentinel:
            raise(AttributeError("RedisManager has no sentinel"))

        status = False

        for sentinel in self.sentinels:
            status = self.add_sentinel(sentinel["ip"],
                                       sentinel["port"],
                                       self.master_name,
                                       self.master_password)
            if status:
                break

        return status

    def get_alternate_sentinels(self):

        if self.verbose:
            print "RedisManager.get_alternate_sentinels"

        if not self.sentinel:
            raise(AttributeError("RedisManager has no sentinel"))

        self.sentinels = []
        try:
            for sentinel in self.sentinel.sentinel("sentinels",self.master_name):
                self.sentinels.append(sentinel)
        # There are no alternate sentinels yet...
        except TypeError:
            pass
        # pp(self.sentinels)

        return True

    def on_master_down(self):
        """
        Handle the inability of the sentinel instance to find a suitable master
        instance
        """

        print "RedisManager.on_master_down"

        # Set the status
        if self.status != "down":
            self.status = "down"

            # Try to reconnect
            counter = 0
            while counter < RECONNECT_TRIES:

                # Try to get a master from the Sentinel instance
                try:
                    status = self.reconnect_master_connection()
                except redis.ConnectionError:
                    print "Error connecting to master. Will try %d more times" % (RECONNECT_TRIES-counter)
                    status = False
                if status:
                    print "Reconnected - breaking loop"
                    break

                counter += 1
                time.sleep(RECONNECT_PAUSE)

            if self.status == "down":
                print "Unable to reconnect after %d seconds" % (RECONNECT_PAUSE*RECONNECT_TRIES)



    def reconnect_master_connection(self):
        """Reconnect the master connection.
        To be used to refresh the connction, ex. when the sentinel reports a
        new master
        """

        if self.verbose:
            print "RedisManager.reconnect_master_connection"

        # Look for pubsub subscriptions
        patterns = False
        channels = False
        if self.pubsub_conn:
            if self.pubsub_conn.patterns:
                patterns = self.pubsub_conn.patterns.copy()
            if self.pubsub_conn.channels:
                channels = self.pubsub_conn.channels.copy()

        # Get rid of reference to previous master
        self.master_conn = False

        if not self.sentinel:
            raise(AttributeError("RedisManager has no sentinel"))

        # Get the master address from the sentinel
        try:
            master_address = self.sentinel.sentinel_get_master_addr_by_name(self.master_name)
        except redis.exceptions.ConnectionError:
            print "Cannot contact sentinel"
            status = self.connect_to_alternate_sentinel()
            if status:
                return self.get_master_connection()
            else:
                raise redis.exceptions.ConnectionError("Cannot connect to alternate sentinel instance")

        # Connect to master
        print "Connecting to master"
        if self.master_password:
            self.master_conn = RedisConnection(master_address[0],master_address[1],password=self.master_password)
        else:
            self.master_conn = RedisConnection(master_address[0],master_address[1])
        try:
            self.master_conn.ping()
        except redis.ConnectionError:
            print "Cannot connect to master"
            self.master_conn = False
            self.status = "down"
            raise redis.ConnectionError

        # Make pubsub connection
        print "Connecting to pubsub"
        self.pubsub_conn = PubsubConnection(connection_pool=self.master_conn.connection_pool)
        #                                    ignore_subscribe_messages=True)


        # Resubscribe
        if patterns:
            for pattern, handler in patterns.iteritems():
                print pattern, handler
                self.psubscribe(pattern, handler)
        if channels:
            for channel, handler in channels.iteritems():
                print channel, handler
                self.psubscribe(channel, handler)

        self.status = "up"

        # Handle backlog of data puts
        if not self.command_queue.empty():
            time.sleep(1)
            while not self.command_queue.empty():
                # Get a command FIFO
                command = self.command_queue.get(False)
                print ">>>",command,"<<<"
                func = getattr(self, command[0])
                func(*command[1],**command[2])

        return True


    def get_master_connection(self):

        if self.verbose:
            print "RedisManager.get_master_connection"

        # Have a connection - return it
        if self.status == "up":
        #if self.master_conn:
            #print "  self.master_conn is not False"
            return self.master_conn

        # No master - connect and return new connection
        else:
            return False
            """
            # Connect
            status = self.reconnect_master_connection()

            if status:
                return self.master_conn
            else:
                return False
            """

    def get_pubsub_connection(self):
        """
        Returns the pubsub connection for the RedisManager instance
        If there is no pubsub connection, create and then return
        """

        if self.verbose:
            print "RedisManager.get_pubsub_connection"

        # Have a connection - return it
        if self.status == "up":
            return self.pubsub_conn
        else:
            return False
        """
        if self.pubsub_conn:
            # print "  self.pubsub_conn is not False"
            return self.pubsub_conn

        # No connection - connect and return new connection
        else:
            # Connect
            status = self.reconnect_master_connection()

            if status:
                return self.pubsub_conn
            else:
                return False
        """

    def close(self):
        """
        Gracefully stop the RedisManager
        """

        if self.verbose:
            print "RedisManager.close"

        # Stop the sentinel_watcher and then join the thread
        self.sentinel_watcher.GO = False
        self.sentinel_watcher.join()

        # Stop the sentinel_listener and then join the thread
        self.sentinel_listener.GO = False
        self.sentinel_listener.join()

        # Close the pubsub connection
        if self.pubsub_conn:
            self.pubsub_conn.close()

        # Close the redis connection
        del(self.master_conn)

        return True

    @executeRedisCommand
    def set_response_callback(self, command, callback):
        "Set a custom Response Callback"

    @executeRedisCommand
    def pipeline(self, transaction=True, shard_hint=None):
        """
        Return a new pipeline object that can queue multiple commands for
        later execution. transaction indicates whether all commands
        should be executed atomically. Apart from making a group of operations
        atomic, pipelines are useful for reducing the back-and-forth overhead
        between the client and server.
        """

    @executeRedisCommand
    def transaction(self, func, *watches, **kwargs):
        """
        Convenience method for executing the callable func as a transaction
        while watching all keys specified in watches. The 'func' callable
        should expect a single argument which is a Pipeline object.
        """

    @executeRedisCommand
    def lock(self, name, timeout=None, sleep=0.1):
        """
        Return a new Lock object using key name that mimics
        the behavior of threading.Lock.

        If specified, timeout indicates a maximum life for the lock.
        By default, it will remain locked until release() is called.

        sleep indicates the amount of time to sleep per loop iteration
        when the lock is in blocking mode and another client is currently
        holding the lock.
        """

    def pubsub(self, **kwargs):
        """
        Return a new instance of RedisManager with the current sentinel, master
        and set pubsub. Ready for use as a traditional redis.pubsub return
        would be.
        """
        M = RedisManager()
        M.add_sentinel()
        M.set_pubsub()
        return M

    def set_pubsub(self, on=True):
        """
        Set the current RedisManager instance to pubsub mode
        """
        self.mode_pubsub = on

    @executeRedisCommand
    def execute_command(self, *args, **options):
        "Execute a command and return a parsed response"

    @executeRedisCommand
    def parse_response(self, connection, command_name, **options):
        "Parses a response from the Redis server"

    @executeRedisCommand
    def bgrewriteaof(self):
        "Tell the Redis server to rewrite the AOF file from data in memory."

    @executeRedisCommand
    def bgsave(self):
        """
        Tell the Redis server to save its data to disk.  Unlike save(),
        this method is asynchronous and returns immediately.
        """

    @executeRedisCommand
    def client_kill(self, address):
        "Disconnects the client at address (ip:port)"

    @executeRedisCommand
    def client_list(self):
        "Returns a list of currently connected clients"

    @executeRedisCommand
    def client_getname(self):
        "Returns the current connection name"

    @executeRedisCommand
    def client_setname(self, name):
        "Sets the current connection name"

    @executeRedisCommand
    def config_get(self, pattern="*"):
        "Return a dictionary of configuration based on the pattern"

    @executeRedisCommand
    def config_set(self, name, value):
        "Set config item name with value"

    @executeRedisCommand
    def config_resetstat(self):
        "Reset runtime statistics"

    @executeRedisCommand
    def dbsize(self):
        "Returns the number of keys in the current database"

    @executeRedisCommand
    def debug_object(self, key):
        "Returns version specific metainformation about a give key"

    @executeRedisCommand
    def echo(self, value):
        "Echo the string back from the server"

    @executeRedisCommand
    def flushall(self):
        "Delete all keys in all databases on the current host"

    @executeRedisCommand
    def flushdb(self):
        "Delete all keys in the current database"

    @executeRedisCommand
    def info(self, section=None):
        """
        Returns a dictionary containing information about the Redis server

        The section option can be used to select a specific section
        of information

        The section option is not supported by older versions of Redis Server,
        and will generate ResponseError
        """

    @executeRedisCommand
    def lastsave(self):
        """
        Return a Python datetime object representing the last time the
        Redis database was saved to disk
        """

    @executeRedisCommand
    def object(self, infotype, key):
        "Return the encoding, idletime, or refcount about the key"

    @executeRedisCommand
    def ping(self):
        "Ping the Redis server"

    @executeRedisCommand
    def save(self):
        """
        Tell the Redis server to save its data to disk,
        blocking until the save is complete
        """

    @executeRedisCommand
    def sentinel(self, *args):
        "Redis Sentinel's SENTINEL command"

    @executeRedisCommand
    def sentinel_masters(self):
        "Returns a dictionary containing the master's state."

    @executeRedisCommand
    def sentinel_slaves(self, service_name):
        "Returns a list of slaves for service_name"

    @executeRedisCommand
    def sentinel_sentinels(self, service_name):
        "Returns a list of sentinels for service_name"

    @executeRedisCommand
    def sentinel_get_master_addr_by_name(self, service_name):
        "Returns a (host, port) pair for the given service_name"

    @executeRedisCommand
    def shutdown(self):
        "Shutdown the server"

    @executeRedisCommand
    def slaveof(self, host=None, port=None):
        """
        Set the server to be a replicated slave of the instance identified
        by the host and port. If called without arguments, the
        instance is promoted to a master instead.
        """

    @executeRedisCommand
    def time(self):
        """
        Returns the server time as a 2-item tuple of ints:
        (seconds since epoch, microseconds into this second).
        """

    @executeRedisCommand
    def append(self, key, value):
        """
        Appends the string value to the value at key. If key
        doesn't already exist, create it with a value of value.
        Returns the new length of the value at key.
        """

    @executeRedisCommand
    def bitcount(self, key, start=None, end=None):
        """
        Returns the count of set bits in the value of key.  Optional
        start and end paramaters indicate which bytes to consider
        """

    @executeRedisCommand
    def bitop(self, operation, dest, *keys):
        """
        Perform a bitwise operation using operation between keys and
        store the result in dest.
        """

    @executeRedisCommand
    def decr(self, name, amount=1):
        """
        Decrements the value of key by amount.  If no key exists,
        the value will be initialized as 0 - amount
        """

    @executeRedisCommand
    def delete(self, *names):
        "Delete one or more keys specified by names"

    @executeRedisCommand
    def dump(self, name):
        """
        Return a serialized version of the value stored at the specified key.
        If key does not exist a nil bulk reply is returned.
        """

    @executeRedisCommand
    def exists(self, name):
        "Returns a boolean indicating whether key name exists"

    @executeRedisCommand
    def expire(self, name, time):
        """
        Set an expire flag on key name for time seconds. time
        can be represented by an integer or a Python timedelta object.
        """

    @executeRedisCommand
    def expireat(self, name, when):
        """
        Set an expire flag on key name. when can be represented
        as an integer indicating unix time or a Python datetime object.
        """

    @executeRedisCommand
    def get(self, name):
        """
        Return the value at key name, or None if the key doesn't exist
        """

    @executeRedisCommand
    def __getitem__(self, name):
        """
        Return the value at key name, raises a KeyError if the key
        doesn't exist.
        """

    @executeRedisCommand
    def getbit(self, name, offset):
        "Returns a boolean indicating the value of offset in name"

    @executeRedisCommand
    def getrange(self, key, start, end):
        """
        Returns the substring of the string value stored at key,
        determined by the offsets start and end (both are inclusive)
        """

    @executeRedisCommand
    def getset(self, name, value):
        """
        Set the value at key name to value if key doesn't exist
        Return the value at key name atomically
        """

    @executeRedisCommand
    def incr(self, name, amount=1):
        """
        Increments the value of key by amount.  If no key exists,
        the value will be initialized as amount
        """

    @executeRedisCommand
    def incrby(self, name, amount=1):
        """
        Increments the value of key by amount.  If no key exists,
        the value will be initialized as amount
        """

    @executeRedisCommand
    def incrbyfloat(self, name, amount=1.0):
        """
        Increments the value at key name by floating amount.
        If no key exists, the value will be initialized as amount
        """

    @executeRedisCommand
    def keys(self, pattern='*'):
        "Returns a list of keys matching pattern"

    @executeRedisCommand
    def mget(self, keys, *args):
        """
        Returns a list of values ordered identically to keys
        """

    @executeRedisCommand
    def mset(self, *args, **kwargs):
        """
        Sets key/values based on a mapping. Mapping can be supplied as a single
        dictionary argument or as kwargs.
        """

    @executeRedisCommand
    def msetnx(self, *args, **kwargs):
        """
        Sets key/values based on a mapping if none of the keys are already set.
        Mapping can be supplied as a single dictionary argument or as kwargs.
        Returns a boolean indicating if the operation was successful.
        """

    @executeRedisCommand
    def move(self, name, db):
        "Moves the key name to a different Redis database db"

    @executeRedisCommand
    def persist(self, name):
        "Removes an expiration on name"

    @executeRedisCommand
    def pexpire(self, name, time):
        """
        Set an expire flag on key name for time milliseconds.
        time can be represented by an integer or a Python timedelta
        object.
        """

    @executeRedisCommand
    def pexpireat(self, name, when):
        """
        Set an expire flag on key name. when can be represented
        as an integer representing unix time in milliseconds (unix time * 1000)
        or a Python datetime object.
        """

    @executeRedisCommand
    def psetex(self, name, time_ms, value):
        """
        Set the value of key name to value that expires in time_ms
        milliseconds. time_ms can be represented by an integer or a Python
        timedelta object
        """

    @executeRedisCommand
    def pttl(self, name):
        "Returns the number of milliseconds until the key name will expire"

    @executeRedisCommand
    def randomkey(self):
        "Returns the name of a random key"

    @executeRedisCommand
    def rename(self, src, dst):
        """
        Rename key src to dst
        """

    @executeRedisCommand
    def renamenx(self, src, dst):
        "Rename key src to dst if dst doesn't already exist"

    @executeRedisCommand
    def restore(self, name, ttl, value):
        """
        Create a key using the provided serialized value, previously obtained
        using DUMP.
        """

    @executeRedisCommand
    def set(self, name, value, ex=None, px=None, nx=False, xx=False):
        """
        Set the value at key name to value

        ex sets an expire flag on key name for ex seconds.

        px sets an expire flag on key name for px milliseconds.

        nx if set to True, set the value at key name to value if it
            does not already exist.

        xx if set to True, set the value at key name to value if it
            already exists.
        """

    @executeRedisCommand
    def setbit(self, name, offset, value):
        """
        Flag the offset in name as value. Returns a boolean
        indicating the previous value of offset.
        """

    @executeRedisCommand
    def setex(self, name, time, value):
        """
        Set the value of key name to value that expires in time
        seconds. time can be represented by an integer or a Python
        timedelta object.
        """

    @executeRedisCommand
    def setnx(self, name, value):
        "Set the value of key name to value if key doesn't exist"

    @executeRedisCommand
    def setrange(self, name, offset, value):
        """
        Overwrite bytes in the value of name starting at offset with
        value. If offset plus the length of value exceeds the
        length of the original value, the new value will be larger than before.
        If offset exceeds the length of the original value, null bytes
        will be used to pad between the end of the previous value and the start
        of what's being injected.

        Returns the length of the new string.
        """

    @executeRedisCommand
    def strlen(self, name):
        "Return the number of bytes stored in the value of name"

    @executeRedisCommand
    def substr(self, name, start, end=-1):
        """
        Return a substring of the string at key name. start and end
        are 0-based integers specifying the portion of the string to return.
        """

    @executeRedisCommand
    def ttl(self, name):
        "Returns the number of seconds until the key name will expire"

    @executeRedisCommand
    def type(self, name):
        "Returns the type of key name"

    @executeRedisCommand
    def watch(self, *names):
        """
        Watches the values at keys names, or None if the key doesn't exist
        """

    @executeRedisCommand
    def unwatch(self):
        """
        Unwatches the value at key name, or None of the key doesn't exist
        """

    @executeRedisCommand
    def blpop(self, keys, timeout=0):
        """
        LPOP a value off of the first non-empty list
        named in the keys list.

        If none of the lists in keys has a value to LPOP, then block
        for timeout seconds, or until a value gets pushed on to one
        of the lists.

        If timeout is 0, then block indefinitely.
        """

    @executeRedisCommand
    def brpop(self, keys, timeout=0):
        """
        RPOP a value off of the first non-empty list
        named in the keys list.

        If none of the lists in keys has a value to LPOP, then block
        for timeout seconds, or until a value gets pushed on to one
        of the lists.

        If timeout is 0, then block indefinitely.
        """

    @executeRedisCommand
    def brpoplpush(self, src, dst, timeout=0):
        """
        Pop a value off the tail of src, push it on the head of dst
        and then return it.

        This command blocks until a value is in src or until timeout
        seconds elapse, whichever is first. A timeout value of 0 blocks
        forever.
        """

    @executeRedisCommand
    def lindex(self, name, index):
        """
        Return the item from list name at position index

        Negative indexes are supported and will return an item at the
        end of the list
        """

    @executeRedisCommand
    def linsert(self, name, where, refvalue, value):
        """
        Insert value in list name either immediately before or after
        [where] refvalue

        Returns the new length of the list on success or -1 if refvalue
        is not in the list.
        """

    @executeRedisCommand
    def llen(self, name):
        "Return the length of the list name"

    @executeRedisCommand
    def lpop(self, name):
        "Remove and return the first item of the list name"

    @executeRedisCommand
    def lpush(self, name, *values):
        "Push values onto the head of the list name"

    @executeRedisCommand
    def lpushx(self, name, value):
        "Push value onto the head of the list name if name exists"

    @executeRedisCommand
    def lrange(self, name, start, end):
        """
        Return a slice of the list name between
        position start and end

        start and end can be negative numbers just like
        Python slicing notation
        """

    @executeRedisCommand
    def lrem(self, name, count, value):
        """
        Remove the first count occurrences of elements equal to value
        from the list stored at name.

        The count argument influences the operation in the following ways:
            count > 0: Remove elements equal to value moving from head to tail.
            count < 0: Remove elements equal to value moving from tail to head.
            count = 0: Remove all elements equal to value.
        """

    @executeRedisCommand
    def lset(self, name, index, value):
        "Set position of list name to value"

    @executeRedisCommand
    def ltrim(self, name, start, end):
        """
        Trim the list name, removing all values not within the slice
        between start and end

        start and end can be negative numbers just like
        Python slicing notation
        """

    @executeRedisCommand
    def rpop(self, name):
        "Remove and return the last item of the list name"

    @executeRedisCommand
    def rpoplpush(self, src, dst):
        """
        RPOP a value off of the src list and atomically LPUSH it
        on to the dst list.  Returns the value.
        """

    @executeRedisCommand
    def rpush(self, name, *values):
        "Push values onto the tail of the list name"

    @executeRedisCommand
    def rpushx(self, name, value):
        "Push value onto the tail of the list name if name exists"

    @executeRedisCommand
    def sort(self, name, start=None, num=None, by=None, get=None,
             desc=False, alpha=False, store=None, groups=False):
        """
        Sort and return the list, set or sorted set at name.

        start and num allow for paging through the sorted data

        by allows using an external key to weight and sort the items.
            Use an "*" to indicate where in the key the item value is located

        get allows for returning items from external keys rather than the
            sorted data itself.  Use an "*" to indicate where int he key
            the item value is located

        desc allows for reversing the sort

        alpha allows for sorting lexicographically rather than numerically

        store allows for storing the result of the sort into
            the key store

        groups if set to True and if get contains at least two
            elements, sort will return a list of tuples, each containing the
            values fetched from the arguments to get.
        """

    @executeRedisCommand
    def scan(self, cursor=0, match=None, count=None):
        """
        Scan and return (nextcursor, keys)

        match allows for filtering the keys by pattern

        count allows for hint the minimum number of returns
        """

    @executeRedisCommand
    def sscan(self, name, cursor=0, match=None, count=None):
        """
        Scan and return (nextcursor, members_of_set)

        match allows for filtering the keys by pattern

        count allows for hint the minimum number of returns
        """

    @executeRedisCommand
    def hscan(self, name, cursor=0, match=None, count=None):
        """
        Scan and return (nextcursor, dict)

        match allows for filtering the keys by pattern

        count allows for hint the minimum number of returns
        """

    @executeRedisCommand
    def zscan(self, name, cursor=0, match=None, count=None,
              score_cast_func=float):
        """
        Scan and return (nextcursor, pairs)

        match allows for filtering the keys by pattern

        count allows for hint the minimum number of returns

        score_cast_func a callable used to cast the score return value
        """

    @executeRedisCommand
    def sadd(self, name, *values):
        "Add value(s) to set name"

    @executeRedisCommand
    def scard(self, name):
        "Return the number of elements in set name"

    @executeRedisCommand
    def sdiff(self, keys, *args):
        "Return the difference of sets specified by keys"

    @executeRedisCommand
    def sdiffstore(self, dest, keys, *args):
        """
        Store the difference of sets specified by keys into a new
        set named dest.  Returns the number of keys in the new set.
        """

    @executeRedisCommand
    def sinter(self, keys, *args):
        "Return the intersection of sets specified by keys"

    @executeRedisCommand
    def sinterstore(self, dest, keys, *args):
        """
        Store the intersection of sets specified by keys into a new
        set named dest.  Returns the number of keys in the new set.
        """

    @executeRedisCommand
    def sismember(self, name, value):
        "Return a boolean indicating if value is a member of set name"

    @executeRedisCommand
    def smembers(self, name):
        "Return all members of the set name"

    @executeRedisCommand
    def smove(self, src, dst, value):
        "Move value from set src to set dst atomically"

    @executeRedisCommand
    def spop(self, name):
        "Remove and return a random member of set name"

    @executeRedisCommand
    def srandmember(self, name, number=None):
        """
        If number is None, returns a random member of set name.

        If number is supplied, returns a list of number random
        memebers of set name. Note this is only available when running
        Redis 2.6+.
        """

    @executeRedisCommand
    def srem(self, name, *values):
        "Remove values from set name"

    @executeRedisCommand
    def sunion(self, keys, *args):
        "Return the union of sets specified by keys"

    @executeRedisCommand
    def sunionstore(self, dest, keys, *args):
        """
        Store the union of sets specified by keys into a new
        set named dest.  Returns the number of keys in the new set.
        """

    @executeRedisCommand
    def zadd(self, name, *args, **kwargs):
        """
        Set any number of score, element-name pairs to the key name. Pairs
        can be specified in two ways:

        As *args, in the form of: score1, name1, score2, name2, ...
        or as **kwargs, in the form of: name1=score1, name2=score2, ...

        The following example would add four values to the 'my-key' key:
        redis.zadd('my-key', 1.1, 'name1', 2.2, 'name2', name3=3.3, name4=4.4)
        """

    @executeRedisCommand
    def zcard(self, name):
        "Return the number of elements in the sorted set name"

    @executeRedisCommand
    def zcount(self, name, min, max):
        """
        Returns the number of elements in the sorted set at key name with
        a score between min and max.
        """

    @executeRedisCommand
    def zincrby(self, name, value, amount=1):
        "Increment the score of value in sorted set name by amount"

    @executeRedisCommand
    def zinterstore(self, dest, keys, aggregate=None):
        """
        Intersect multiple sorted sets specified by keys into
        a new sorted set, dest. Scores in the destination will be
        aggregated based on the aggregate, or SUM if none is provided.
        """

    @executeRedisCommand
    def zrange(self, name, start, end, desc=False, withscores=False,
               score_cast_func=float):
        """
        Return a range of values from sorted set name between
        start and end sorted in ascending order.

        start and end can be negative, indicating the end of the range.

        desc a boolean indicating whether to sort the results descendingly

        withscores indicates to return the scores along with the values.
        The return type is a list of (value, score) pairs

        score_cast_func a callable used to cast the score return value
        """

    @executeRedisCommand
    def zrangebyscore(self, name, min, max, start=None, num=None,
                      withscores=False, score_cast_func=float):
        """
        Return a range of values from the sorted set name with scores
        between min and max.

        If start and num are specified, then return a slice
        of the range.

        withscores indicates to return the scores along with the values.
        The return type is a list of (value, score) pairs

        score_cast_func a callable used to cast the score return value
        """

    @executeRedisCommand
    def zrank(self, name, value):
        """
        Returns a 0-based value indicating the rank of value in sorted set
        name
        """

    @executeRedisCommand
    def zrem(self, name, *values):
        "Remove member values from sorted set name"

    @executeRedisCommand
    def zremrangebyrank(self, name, min, max):
        """
        Remove all elements in the sorted set name with ranks between
        min and max. Values are 0-based, ordered from smallest score
        to largest. Values can be negative indicating the highest scores.
        Returns the number of elements removed
        """

    @executeRedisCommand
    def zremrangebyscore(self, name, min, max):
        """
        Remove all elements in the sorted set name with scores
        between min and max. Returns the number of elements removed.
        """

    @executeRedisCommand
    def zrevrange(self, name, start, end, withscores=False,
                  score_cast_func=float):

        """
        Return a range of values from sorted set name between
        start and end sorted in descending order.

        start and end can be negative, indicating the end of the range.

        withscores indicates to return the scores along with the values
        The return type is a list of (value, score) pairs

        score_cast_func a callable used to cast the score return value
        """

    @executeRedisCommand
    def zrevrangebyscore(self, name, max, min, start=None, num=None,
                         withscores=False, score_cast_func=float):
        """
        Return a range of values from the sorted set name with scores
        between min and max in descending order.

        If start and num are specified, then return a slice
        of the range.

        withscores indicates to return the scores along with the values.
        The return type is a list of (value, score) pairs

        score_cast_func a callable used to cast the score return value
        """

    @executeRedisCommand
    def zrevrank(self, name, value):
        """
        Returns a 0-based value indicating the descending rank of
        value in sorted set name
        """

    @executeRedisCommand
    def zscore(self, name, value):
        "Return the score of element value in sorted set name"

    @executeRedisCommand
    def zunionstore(self, dest, keys, aggregate=None):
        """
        Union multiple sorted sets specified by keys into
        a new sorted set, dest. Scores in the destination will be
        aggregated based on the aggregate, or SUM if none is provided.
        """

    @executeRedisCommand
    def hdel(self, name, *keys):
        "Delete keys from hash name"

    @executeRedisCommand
    def hexists(self, name, key):
        "Returns a boolean indicating if key exists within hash name"

    @executeRedisCommand
    def hget(self, name, key):
        "Return the value of key within the hash name"

    @executeRedisCommand
    def hgetall(self, name):
        "Return a Python dict of the hash's name/value pairs"

    @executeRedisCommand
    def hincrby(self, name, key, amount=1):
        "Increment the value of key in hash name by amount"

    @executeRedisCommand
    def hincrbyfloat(self, name, key, amount=1.0):
        """
        Increment the value of key in hash name by floating amount
        """

    @executeRedisCommand
    def hkeys(self, name):
        "Return the list of keys within hash name"

    @executeRedisCommand
    def hlen(self, name):
        "Return the number of elements in hash name"

    @executeRedisCommand
    def hset(self, name, key, value):
        """
        Set key to value within hash name
        Returns 1 if HSET created a new field, otherwise 0
        """

    @executeRedisCommand
    def hsetnx(self, name, key, value):
        """
        Set key to value within hash name if key does not
        exist.  Returns 1 if HSETNX created a field, otherwise 0.
        """

    @executeRedisCommand
    def hmset(self, name, mapping):
        """
        Set key to value within hash name for each corresponding
        key and value from the mapping dict.
        """

    @executeRedisCommand
    def hmget(self, name, keys, *args):
        "Returns a list of values ordered identically to keys"

    @executeRedisCommand
    def hvals(self, name):
        "Return the list of values within hash name"

    @executeRedisCommand
    def publish(self, channel, message):
        """
        Publish message on channel.
        Returns the number of subscribers the message was delivered to.
        """

    @executeRedisCommand
    def eval(self, script, numkeys, *keys_and_args):
        """
        Execute the Lua script, specifying the numkeys the script
        will touch and the key names and argument values in keys_and_args.
        Returns the result of the script.

        In practice, use the object returned by register_script. This
        function exists purely for Redis API completion.
        """

    @executeRedisCommand
    def evalsha(self, sha, numkeys, *keys_and_args):
        """
        Use the sha to execute a Lua script already registered via EVAL
        or SCRIPT LOAD. Specify the numkeys the script will touch and the
        key names and argument values in keys_and_args. Returns the result
        of the script.

        In practice, use the object returned by register_script. This
        function exists purely for Redis API completion.
        """

    @executeRedisCommand
    def script_exists(self, *args):
        """
        Check if a script exists in the script cache by specifying the SHAs of
        each script as args. Returns a list of boolean values indicating if
        if each already script exists in the cache.
        """

    @executeRedisCommand
    def script_flush(self):
        "Flush all scripts from the script cache"

    @executeRedisCommand
    def script_kill(self):
        "Kill the currently executing Lua script"

    @executeRedisCommand
    def script_load(self, script):
        "Load a Lua script into the script cache. Returns the SHA."

    @executeRedisCommand
    def register_script(self, script):
        """
        Register a Lua script specifying the keys it will touch.
        Returns a Script object that is callable and hides the complexity of
        deal with scripts, keys, and shas. This is the preferred way to work
        with Lua scripts.
        """






    @executeRedisPubsubCommand
    def psubscribe(self, *args, **kwargs):
        """
        Subscribe to channel patterns. Patterns supplied as keyword arguments
        expect a pattern name as the key and a callable as the value. A
        pattern's callable will be invoked automatically when a message is
        received on that pattern rather than producing a message via
        ``listen()``.
        """

    @executeRedisPubsubCommand
    def punsubscribe(self, *args):
        """
        Unsubscribe from the supplied patterns. If empy, unsubscribe from
        all patterns.
        """

    @executeRedisPubsubCommand
    def subscribe(self, *args, **kwargs):
        """
        Subscribe to channels. Channels supplied as keyword arguments expect
        a channel name as the key and a callable as the value. A channel's
        callable will be invoked automatically when a message is received on
        that channel rather than producing a message via ``listen()`` or
        ``get_message()``.
        """

    @executeRedisPubsubCommand
    def unsubscribe(self, *args):
        """
        Unsubscribe from the supplied channels. If empty, unsubscribe from
        all channels
        """
    @executeRedisPubsubCommand
    def listen(self):
        "Listen for messages on channels this client has been subscribed to"

    @executeRedisPubsubCommand
    def get_message(self, ignore_subscribe_messages=False):
        "Get the next message if one is available, otherwise None"

    @executeRedisPubsubCommand
    def run_in_thread(self, sleep_time=0):
        """
        Runs an event loop in a separate thread. pubsub.run_in_thread() creates
        a new thread and starts the event loop. The thread object is returned to
        the caller of run_in_thread(). The caller can use the thread.stop()
        method to shut down the event loop and thread. Behind the scenes, this
        is simply a wrapper around get_message() that runs in a separate thread,
        essentially creating a tiny non-blocking event loop for you.
        run_in_thread() takes an optional sleep_time argument. If specified, the
        event loop will call time.sleep() with the value in each iteration of
        the loop.
        """








if __name__ == "__main__":

  print "Testing pysent v%s" % __version__
  print "----------------"+"-"*len(__version__)
  print "Usage: pysent.py [host] [port] [name] [password]\n"

  host = "127.0.0.1"
  port = 36379
  name = "testmaster"
  password = "foobared"

  # Handle commandline args
  args = sys.argv
  if len(args) == 2:
      host = args[1]
  if len(args) == 3:
      port = int(args[2])
  if len(args) == 4:
    name = args[3]
  if len(args) == 5:
    password = args[4]
  print "Will connect to %s at %s on port %d" % (name,host,port)

  Manager = RedisManager(verbose=True)
  Manager.add_sentinel(host,port,name,password)

  print dir(Manager)

  print Manager.set("test","foo1")
  print Manager.get("test")

  #PS = Manager.get_pubsub_connection()
  Manager.psubscribe("*")

  counter = 0
  while True:
      message = Manager.get_message()
      if message:
          print message
      time.sleep(1)
  print "Exited loop"

  sys.exit(0)


  """
  PS = Manager.pubsub()
  print dir(PS)
  """

  """
  PS.psubscribe("test")
  while True:
      message = PS.get_message()
      if message:
          print message
      else:
          PS.ping()
      time.sleep(0.1)


  #Manager.publish("foo","bar")
  """
