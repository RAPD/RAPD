"""
Creates new MySQL database for RAPD
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
__created__ = "2009-07-08"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

# Standard imports
import datetime
import sys

import pymongo

# RAPD imports
import utils.text as text

VERSION = "2.0"

"""
docker run --name mongo -p 27017:27017 -d mongo --storageEngine wiredTiger
"""

def get_host_info():
    """
    Query the user for host and database information
    """

    # Get the host name
    msg1 = text.green+"Input host of MySQL database: "+text.stop
    select1 = raw_input(msg1).strip()
    if select1:
        hostname = str(select1)
        if len(hostname) == 0:
            print text.error+"Error - you have not input a host"+text.stop
            sys.exit(9)
    else:
        print text.error+"Error - you have not input a host"+text.stop
        sys.exit(9)
    print "                              %s" % hostname

    # Get the port
    msg4 = text.green+"Input port of MySQL database (3306 is standard): "+text.stop
    select4 = raw_input(msg4).strip()
    if select4:
        port = int(select4)
        if port == 0:
            print text.error+"Error - you have not input a port"+text.stop
            sys.exit(9)
    else:
        print text.error+"Error - you have not input a port"+text.stop
        sys.exit(9)
    print "                                                 %d" % port

    # Get the user name
    msg2 = text.green+"Input user name: "+text.stop
    select2 = raw_input(msg2).strip()
    if select2:
        username = str(select2)
        if len(username) == 0:
            print text.error+"Error - you have not input a username"+text.stop
            sys.exit(9)
    else:
        print text.error+"Error - you have not input a username"+text.stop
        sys.exit(9)
    print "                 %s" % username

    # Get the password
    msg3 = text.green+"Input password: "+text.stop
    #select3 = getpass.getpass(msg3).strip()
    select3 = raw_input(msg3).strip()
    if select3:
        password = str(select3)
        if len(password) == 0:
            print text.error+"Error - you have not input a password"+text.stop
            sys.exit(9)
    else:
        print text.error+"Error - you have not input a password"+text.stop
        sys.exit(9)
    print "                %s" % password

    return hostname, port, username, password

def check_database_connection(hostname, port, username, password):
    """
    Attempts to connect to the database using the input parameters

    Keyword arguments
    hostname -- server where the database is accessed
    port -- port for the database
    username -- name to use accessing the database
    password -- the password
    """

    print "check_database_connection %s:%s" % (hostname, port)

    try:
        client = pymongo.MongoClient(host=hostname,
                                    port=port)
        __ = client.address

        db = client.rapd

        print text.green+"Able to connect to MongoDB"+text.stop

    # Cannot connect
    except pymongo.errors.ServerSelectionTimeoutError as error:
        # print error
        # print(dir(error))
        if "Host is down" in error.message:
            print text.red+"Unable to connect to MongoDB at %s:%s - host is down" % (hostname, port)+text.stop
        elif "Connection refused" in error.message:
            print text.red+"Unable to connect to MongoDB at %s:%s - port could be wrong" % (hostname, port)+text.stop

        sys.exit(9)

    return True

def check_database_version(hostname, port, username, password):
    """
    Find the status of the RAPD MySQL database.
    Returns 0 for no database present or a version number found.

    The NE-CAT RAPD v1.x database is version 4.
    The database version should match the RAPD version from here on, so the
    version currently under development is 2.0

    Keyword arguments
    hostname -- server where the database is accessed
    port -- port for the database
    username -- name to use accessing the database
    password -- the password
    """

    print "check_database_version"

    client = pymongo.MongoClient(host=hostname,
                                 port=port)

    db = client.rapd

    try:
        version = db.rapd_db_version.find().sort("version", -1).limit(1)
        for v in version:
            return v["version"]

    # Naive db
    except TypeError as error:
        if error.message.startswith("'Collection' object is not callable. If you meant to call th"):
            print text.blue+"Looks like a new installation of RAPD database"+text.stop
        return 0

def create_version_collection(hostname, port, username, password):
    """
    Create the version table

    Keyword arguments
    hostname -- server where the database is accessed
    port -- port for the database
    username -- name to use accessing the database
    password -- the password
    """

    # Connect
    client = pymongo.MongoClient(host=hostname,
                                port=port)

    # Get the db
    db = client.rapd

    # Drop the collection
    db.drop_collection("rapd_db_version")

    # Create the collection
    db.create_collection(name="rapd_db_version")

    # Insert version into the table
    db.rapd_db_version.insert({"version":VERSION,
                               "timestamp":datetime.datetime.utcnow()})

    print "Version set to %s" % VERSION

def create_data_collections(hostname, port, username, password):
    """
    Create the "data" tables for rapd core functions

    Keyword arguments
    hostname -- server where the database is accessed
    port -- port for the database
    username -- name to use accessing the database
    password -- the password
    """

    # Connect
    client = pymongo.MongoClient(host=hostname,
                                 port=port)

    # Get the db
    db = client.rapd

    # images
    db.drop_collection("images")
    db.create_collection(name="images")
    db.images.create_index([("fullname", pymongo.ASCENDING),
                            ("date", pymongo.ASCENDING)],
                           unique=True,
                           name="blocker")

    # runs
    db.drop_collection("runs")
    db.create_collection(name="runs")
    db.runs.create_index([("directory", pymongo.ASCENDING),
                          ("image_prefix", pymongo.ASCENDING),
                          ("run_number", pymongo.ASCENDING),
                          ("start_image_number", pymongo.ASCENDING),
                          ("number_images", pymongo.ASCENDING),
                          ("file_ctime", pymongo.ASCENDING)],
                         unique=True,
                         name="blocker")

    # agent_processes
    db.drop_collection("agent_processes")
    db.create_collection(name="agent_processes")

    # agent_results
    db.drop_collection("agent_results")
    db.create_collection(name="agent_results")

    # sessions
    db.drop_collection("sessions")
    db.create_collection(name="sessions")
    db.sessions.create_index("data_root_dir",
                             unique=True)

    return True

def perform_naive_install(hostname, port, username, password):
    """
    Orchestrate the installation of v2.0 of the RAPD MongoDB database

    Keyword arguments
    hostname -- server where the database is accessed
    port -- port for the database
    username -- name to use accessing the database
    password -- the password
    """

    print text.blue+"Performing installation of RAPD database version %s" % VERSION + text.stop

    # Create the version table
    create_version_collection(hostname=hostname,
                              port=port,
                              username=username,
                              password=password)

    # Create "data" tables
    create_data_collections(hostname=hostname,
                            port=port,
                            username=username,
                            password=password)

def main():
    """
    Orchestrate command-line running
    """

    print "\nrapd_create_mongodb.py v%s" % VERSION
    print "============================="

    # Get the host information
    # hostname, port, username, password = get_host_info()

    hostname = "192.168.99.100"
    port = 27017
    username = None
    password = None

    hostname = "164.54.208.142"
    port = 27017
    #
    # hostname = "192.168.99.100"
    # port = 3306
    # username = "root"
    # password = "root_password"

    # Check that the database is accessible
    check_database_connection(hostname, port, username, password)

    # Check the current state of the database
    database_version = check_database_version(hostname, port, username, password)

    # Perform install
    if database_version in (0, None):
        perform_naive_install(hostname, port, username, password)

    # Version is current
    elif database_version == VERSION:
        print text.green+"RAPD database version %s is current." % database_version + text.stop
        # For Development
        perform_naive_install(hostname, port, username, password)

    # Upgrades go here

    # Version is not understood
    else:
        print text.error+"RAPD database version %s is NOT understood." % database_version + text.stop

if __name__ == '__main__':

    main()
