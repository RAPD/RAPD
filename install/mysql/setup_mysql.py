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

    # Add the admin
    connection.select_db("rapd_users")
    cursor = connection.cursor()
    cursor.execute("INSERT INTO authorize VALUES ('Admin_First','Admin_Last','RAPD_Admin','11cefeb763516b3c','Users','Administrators','','0','admin_email@email.com','https://myserver.com/rapd/main.php','1','2016-01-01')")

    # Add a setting
    connection.select_db("rapd_data")
    cursor = connection.cursor()
    cursor.execute("INSERT INTO settings VALUES (1, 'NECAT_E', 'DEFAULTS', 'True', 'None', 'Protein', 0.55, 1, 100, 100, 100, 0, 0, 0, 0, 0, 0, 'False', '/tmp', 'False', 0, 0, 0, 'best', 'none', 1, 0, 0, 360, 1, 0, 'AUTO', 'AUTO', 'rapd', 0, 'GLOBAL', NOW())")
    cursor.execute("INSERT INTO current VALUES('NECAT_E', 1, '/tmp', 0, NOW())")
    connection.close()
