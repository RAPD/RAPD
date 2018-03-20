"""
Creates new MySQL database for RAPD
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
__created__ = "2009-07-08"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

# Standard imports
import argparse
import bcrypt
import datetime
import pymongo
import sys
import time

# RAPD imports
import utils.text as text

# Constants
CURRENT_VERSION = "2.0"
DEFAULT_MONGOURI = "mongodb://localhost:27017/rapd"

"""
To run a MongoDB instance in Docker
docker run -d -p 27017:27017 --name mongo -v LOCAL_DATA_DIR:/data/db mongo --storageEngine wiredTiger
"""

def check_database_connection(mongouri):
    """
    Attempts to connect to the database using the input parameters

    Keyword arguments
    mongouri -- the MongoDB connection string in URI format
    """

    print "Checking the RAPD database connection for %s" % mongouri

    try:
        client = pymongo.MongoClient(mongouri)
        __ = client.address

        db = client.rapd

        print text.green+"  Able to connect to MongoDB"+text.stop

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

def check_database_version(mongouri):
    """
    Find the status of the RAPD MySQL database.
    Returns 0 for no database present or a version number found.

    The NE-CAT RAPD v1.x database is version 4.
    The database version should match the RAPD version from here on, so the
    version currently under development is 2.0

    Keyword arguments
    mongouri -- the MongoDB connection string in URI format
    """

    print "Checking the RAPD database version"

    client = pymongo.MongoClient(mongouri)

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

# def create_version_collection(hostname, port, username, password):
#     """
#     Create the version table
#
#     Keyword arguments
#     hostname -- server where the database is accessed
#     port -- port for the database
#     username -- name to use accessing the database
#     password -- the password
#     """
#
#     # Connect
#     client = pymongo.MongoClient(host=hostname,
#                                 port=port)
#
#     # Get the db
#     db = client.rapd
#
#     # Drop the collection
#     db.drop_collection("rapd_db_version")
#
#     # Create the collection
#     db.create_collection(name="rapd_db_version")
#
#     # Insert version into the table
#     db.rapd_db_version.insert({"version":CURRENT_VERSION,
#                                "timestamp":datetime.datetime.utcnow()})
#
#     print "Version set to %s" % CURRENT_VERSION

def insert_user(mongouri, new_user):
    """
    Create a new user in the database
    """

    # Connect
    client = pymongo.MongoClient(mongouri)

    # Get the db
    db = client.rapd

    # Get the group_id
    group_result = db.groups.find_one({"groupname":new_user["groupname"]})
    new_user["groups"] = [group_result["_id"]]
    new_user.pop("groupname")

    # Insert user
    result = db.users.insert_one(new_user)

    return result

def insert_group(mongouri, new_group):
    """
    Insert a new group into the database
    """

    # Connect
    client = pymongo.MongoClient(mongouri)

    # Get the db
    db = client.rapd

    # Insert user
    result = db.groups.insert_one(new_group)

    return result

# def create_data_collections(hostname, port, username, password):
#     """
#     Create the "data" tables for rapd core functions
#
#     Keyword arguments
#     hostname -- server where the database is accessed
#     port -- port for the database
#     username -- name to use accessing the database
#     password -- the password
#     """
#
#     # Connect
#     client = pymongo.MongoClient(host=hostname,
#                                  port=port)
#
#     # Get the db
#     db = client.rapd
#
#     # images
#     db.drop_collection("images")
#     db.create_collection(name="images")
#     db.images.create_index([("fullname", pymongo.ASCENDING),
#                             ("date", pymongo.ASCENDING)],
#                            unique=True,
#                            name="blocker")
#
#     # runs
#     db.drop_collection("runs")
#     db.create_collection(name="runs")
#     db.runs.create_index([("directory", pymongo.ASCENDING),
#                           ("image_prefix", pymongo.ASCENDING),
#                           ("run_number", pymongo.ASCENDING),
#                           ("start_image_number", pymongo.ASCENDING),
#                           ("number_images", pymongo.ASCENDING),
#                           ("file_ctime", pymongo.ASCENDING)],
#                          unique=True,
#                          name="blocker")
#
#     # agent_processes
#     db.drop_collection("agent_processes")
#     db.create_collection(name="agent_processes")
#
#     # agent_results
#     db.drop_collection("agent_results")
#     db.create_collection(name="agent_results")
#
#     # sessions
#     db.drop_collection("sessions")
#     db.create_collection(name="sessions")
#     db.sessions.create_index("data_root_dir",
#                              unique=True)
#
#     return True

# def perform_naive_install(hostname, port, username, password):
#     """
#     Orchestrate the installation of v2.0 of the RAPD MongoDB database
#
#     Keyword arguments
#     hostname -- server where the database is accessed
#     port -- port for the database
#     username -- name to use accessing the database
#     password -- the password
#     """
#
#     print text.blue+"Performing installation of RAPD database version %s" % CURRENT_VERSION + text.stop
#
#     # Create the version table
#     create_version_collection(hostname=hostname,
#                               port=port,
#                               username=username,
#                               password=password)
#
#     # Create "data" tables
#     create_data_collections(hostname=hostname,
#                             port=port,
#                             username=username,
#                             password=password)

def get_commandline():
    """Get the commandline variables and handle them"""

    # Parse the commandline arguments
    commandline_description = """Launch an index & strategy on input image(s)"""
    parser = argparse.ArgumentParser(add_help=False)

    #
    # Add arguments
    #

    # Add user
    parser.add_argument("-u", "--user",
                        action="store_true",
                        dest="add_user",
                        help="Add user to database")

    # Add group
    parser.add_argument("-g", "--group",
                        action="store_true",
                        dest="add_group",
                        help="Add group to database")

    # Directory or files
    parser.add_argument(action="store",
                        dest="mongouri",
                        nargs="*",
                        help="Mongo connection string in URI format")

    args = parser.parse_args()

    # Use the default mongouri
    if not args.mongouri:
        args.mongouri = [DEFAULT_MONGOURI]

    return args

def main():
    """
    Orchestrate command-line running
    """

    print "\nrapd_create_mongodb.py v%s" % CURRENT_VERSION
    print "============================="

    # Get the host information
    args = get_commandline()

    MONGO_URI = args.mongouri[0]

    # Check that the database is accessible
    check_database_connection(mongouri=MONGO_URI)

    # Check the current state of the database
    database_version = check_database_version(mongouri=MONGO_URI)

    # No versioning found
    if database_version in (0, None):
        print "  No versioning found"
        # perform_naive_install(hostname, port, username, password)

    # Version is current
    elif database_version == CURRENT_VERSION:
        print text.green+"  RAPD database version %s is current." % database_version + text.stop
        # For Development
        # perform_naive_install(hostname, port, username, password)

    if args.add_group:
        print "Adding a group..."
        groupname = raw_input("  Name: ")
        institution = raw_input("  Institution: ")

        new_group = {
            "created":     datetime.datetime.now(),
            "groupname":   groupname,
            "institution": institution,
            "status":      "active",
        }
        result_group = insert_group(mongouri=MONGO_URI, new_group=new_group)

    # Add a user
    if args.add_user:
        print "Adding a user..."

        username = raw_input("  Name: ")
        email = raw_input("  Email: ")
        group = raw_input("  Group: ")
        role = raw_input("  Role (site_admin, group_admin, user): ")
        password = raw_input("  Password: ")

        # Password encryption
        hashed = bcrypt.hashpw(password, bcrypt.gensalt(14))

        new_user = {
            "created":           datetime.datetime.now(),
            "groupname":         group,
            "password":          hashed,
            "pass_expire":       datetime.datetime.now(),
            "pass_force_change": True,
            "role":              role,
            "status":            "active",
            "username":          username,
        }
        result_user = insert_user(mongouri=MONGO_URI, new_user=new_user)

        sys.exit()

        # Upgrades go here

    # Version is not understood
    else:
        print text.error+"RAPD database version %s is NOT understood." % database_version + text.stop

if __name__ == '__main__':

    main()
