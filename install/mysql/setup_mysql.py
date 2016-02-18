"""
This file is part of RAPD

Copyright (C) 2016, Cornell University
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

__created__ = "2016-02-18"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Development"

import pymysql
import subprocess

# MySQL database connection information
HOST_ADDRESS = ("192.168.99.100", 3306)
USERNAME = "root"
PASSWORD = "root_password"

if __name__ == "__main__":

    print "setup_mysql.py"
    print "=============="

    connection = pymysql.connect(host=HOST_ADDRESS[0],
                                 port=HOST_ADDRESS[1],
                                 user=USERNAME,
                                 passwd=PASSWORD)
    print dir(connection)

    cursor = connection.cursor()
    print dir(cursor)

    for table_type in ("data", "users", "cloud"):

        try:
            cursor.execute("CREATE DATABASE rapd_%s" % table_type)
        except pymysql.err.ProgrammingError:
            print "Already exists"

        # Now create the tables
        subprocess.check_output("mysql -h %s -P %d -u %s -p%s rapd_%s < rapd_%s_schema.sql" % (HOST_ADDRESS[0], HOST_ADDRESS[1], USERNAME, PASSWORD, table_type, table_type), shell=True)
