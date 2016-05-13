"""
Creates new MySQL database for RAPD
"""

__license__ = """
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

__created__ = "2009-07-08"
__maintainer__ = "Frank Murphy"
__email__ = "fmurphy@anl.gov"
__status__ = "Production"

# Standard imports
import sys

import pymysql

# RAPD imports
import utils.text as text

VERSION = "2.0"

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

def perform_mysql_command(hostname, port, username, password, database, command):
    """
    Run a MySQL command_back

    Keyword arguments
    hostname -- server where the database is accessed
    port -- port for the database
    username -- name to use accessing the database
    password -- the password
    database -- the database to run on
    command -- compatible MySQL command
    """
    print "perform_mysql_command"
    print command

    connection = pymysql.connect(host=hostname,
                                 port=port,
                                 db=database,
                                 user=username,
                                 passwd=password)

    cursor = connection.cursor()

    cursor.execute(command)
    connection.commit()

    # cursor.close()
    # connection.close()

    return True

def check_database_connection(hostname, port, username, password):
    """
    Attempts to connect to the database using the input parameters

    Keyword arguments
    hostname -- server where the database is accessed
    port -- port for the database
    username -- name to use accessing the database
    password -- the password
    """

    try:
        connection = pymysql.connect(host=hostname,
                                     port=port,
                                     user=username,
                                     passwd=password)

        print text.green+"Able to connect to MySQL database"+text.stop

    except pymysql.err.OperationalError as error:
        error_number, error_message = error
        # print error_number, error_message

        if error_number == 2003:

            # Server is not reachable
            if "Errno 8" in error_message:
                print text.error+"Error - cannot find the server %s" % hostname
                print "The raw error: %s" % error_message + text.stop
                sys.exit(9)

            # Server exists, but cannot connect
            elif "Errno 61" in error_message:
                print text.error+"Error - cannot connect to database on host:%s\
port:%d" % (hostname, port)
                print "The raw error: %s" % error_message + text.stop
                sys.exit(9)

            # Unknown
            else:
                print text.error+"Unknown error connecting to the database"
                print "The raw error: %s" % error_message + text.stop
                sys.exit(9)

        # Permission problems
        elif error_number == 1045:
            print text.error+"Error - problem connecting to the database with u\
sername:%s password:%s" % (username, password)
            print "The raw error: %s" % error_message + text.stop
            sys.exit(9)

        # Unknown
        else:
            print text.error+"Unknown error"
            print "The raw error:%d %s" % (error_number, error_message+text.stop)
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

    try:
        connection = pymysql.connect(host=hostname,
                                     port=port,
                                     db="rapd",
                                     user=username,
                                     passwd=password)

        cursor = connection.cursor()

    # No table
    except pymysql.err.InternalError as error:
        error_number, error_message = error
        # print error_number, error_message

        if error_number == 1049:
            print text.blue+"Looks like a new installation of RAPD database"+text.stop
            return 0

    # Get the RAPD database version number
    try:
        cursor.execute("SELECT * FROM version")
        for row in cursor.fetchall():
            version, timestamp = row
            return version
    except pymysql.err.ProgrammingError as error: #(1049, u"Unknown database 'rapd'")
        error_number, error_message = error
        if error_number == 1146:
            print text.blue+"Looks like a new installation of RAPD database"+text.stop
            return 0

def create_database(hostname, port, username, password, database, drop=False):
    """
    Generic method for database creation

    Keyword arguments
    hostname -- server where the database is accessed
    port -- port for the database
    username -- name to use accessing the database
    password -- the password
    database -- name of the database to be created
    drop -- drop the table first?
    """

    connection = pymysql.connect(host=hostname,
                                 port=port,
                                 user=username,
                                 passwd=password)

    cursor = connection.cursor()

    # Try to delete the database - used in testing
    if drop is True:
        try:
            cursor.execute("drop database %s" % database)
            connection.commit()
            print text.green+"Database %s dropped" % database + text.stop
        except:
            print "Database %s does not exist to delete" % database

    # Create the database
    # try:
    cursor.execute("CREATE DATABASE %s" % database)
    connection.commit()
    # except _mysql_exceptions.ProgrammingError:
    #     if self.verbose:
    #         print 'Database rapd_data already exists'

    print text.green+"Database %s created" % database + text.stop

def create_table(hostname,
                 port,
                 username,
                 password,
                 database,
                 table,
                 table_definition,
                 drop=False):
    """
    Generic method for database creation

    Keyword arguments
    hostname -- server where the database is accessed
    port -- port for the database
    username -- name to use accessing the database
    password -- the password
    database -- database to put table in
    table -- name of the table to be created
    table_definition -- table definition string
    drop -- drop the table first?
    """

    connection = pymysql.connect(host=hostname,
                                 port=port,
                                 db=database,
                                 user=username,
                                 passwd=password)

    cursor = connection.cursor()

    # Try to delete the database - used in testing
    if drop == True:
        try:
            cursor.execute("drop table %s" % table)
            connection.commit()
            print text.green+"Table %s dropped" % table + text.stop
        except pymysql.err.InternalError as error:
            error_number, error_message = error
            if error_number == 1051:
                print text.blue+"Table %s does not exist to drop." % table +text.stop

    # Create the database
    # try:
    cursor.execute("CREATE TABLE %s (%s)" % (table, table_definition))
    connection.commit()
    # except _mysql_exceptions.ProgrammingError:
    #     if self.verbose:
    #         print 'Database rapd_data already exists'

    print text.green+"Table %s created" % table + text.stop

def create_version_table(hostname, port, username, password):
    """
    Create the version table

    Keyword arguments
    hostname -- server where the database is accessed
    port -- port for the database
    username -- name to use accessing the database
    password -- the password
    """

    # Create the version table
    version_table_string = """version VARCHAR(16) NOT NULL,
                              timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                              PRIMARY KEY (version)"""
    create_table(hostname=hostname,
                 port=port,
                 username=username,
                 password=password,
                 database="rapd",
                 table="version",
                 table_definition=version_table_string,
                 drop=False)

    # Inerst version into the table
    version_insert_string = "INSERT INTO version (version) VALUES (%s)" % VERSION
    perform_mysql_command(hostname=hostname,
                          port=port,
                          username=username,
                          password=password,
                          database="rapd",
                          command=version_insert_string)
    print "Version set to %s" % VERSION

def create_data_tables(hostname, port, username, password):
    """
    Create the "data" tables

    Keyword arguments
    hostname -- server where the database is accessed
    port -- port for the database
    username -- name to use accessing the database
    password -- the password
    """

    # Create Distl table
    distl_results = """distl_result_id  mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
        indexstrategy_result_id mediumint(8) unsigned DEFAULT NULL,
        good_bragg_spots mediumint(8) unsigned DEFAULT NULL,
        ice_rings smallint(5) unsigned DEFAULT NULL,
        labelit_res float DEFAULT NULL,
        max_cell float DEFAULT NULL,
        max_signal_strength mediumint(8) unsigned DEFAULT NULL,
        mean_int_signal mediumint(8) unsigned DEFAULT NULL,
        min_signal_strength mediumint(8) unsigned DEFAULT NULL,
        overloads mediumint(8) unsigned DEFAULT NULL,
        res float DEFAULT NULL,
        spots_in_res mediumint(8) unsigned DEFAULT NULL,
        status varchar(8) DEFAULT NULL,
        timestamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (distl_result_id),
        KEY indexstrategy_result_id (indexstrategy_result_id)"""

    create_table(hostname=hostname,
                 port=port,
                 username=username,
                 password=password,
                 database="rapd",
                 table="distl_results",
                 table_definition=distl_results,
                 drop=False)

    # Create Labelit table
    labelit_results = """labelit_result_id  mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
        indexstrategy_result_id mediumint(8) unsigned DEFAULT NULL,
        iteration tinyint(3) unsigned DEFAULT NULL,
        res float DEFAULT NULL,
        spots_fit mediumint(8) unsigned DEFAULT NULL,
        metric float DEFAULT NULL,
        spacegroup varchar(8) DEFAULT NULL,
        distance float DEFAULT NULL,
        x_beam float DEFAULT NULL,
        y_beam float DEFAULT NULL,
        a float DEFAULT NULL,
        b float DEFAULT NULL,
        c float DEFAULT NULL,
        alpha float DEFAULT NULL,
        beta float DEFAULT NULL,
        gamma float DEFAULT NULL,
        mosaicity float DEFAULT NULL,
        rmsd float DEFAULT NULL,
        status varchar(8) DEFAULT NULL,
        timestamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (labelit_result_id),
        KEY indexstrategy_result_id (indexstrategy_result_id)"""

    create_table(hostname=hostname,
                 port=port,
                 username=username,
                 password=password,
                 database="rapd",
                 table="labelit_results",
                 table_definition=labelit_results,
                 drop=False)

    # Create Raddose table
    raddose_results = """raddose_result_id  mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
        indexstrategy_result_id mediumint(8) unsigned DEFAULT NULL,
        dose_per_image float DEFAULT NULL,
        adjusted_dose float DEFAULT NULL,
        henderson_limit mediumint(8) unsigned DEFAULT NULL,
        exp_dose_limit mediumint(8) unsigned DEFAULT NULL,
        status varchar(8) DEFAULT NULL,
        timestamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (raddose_result_id),
        KEY indexstrategy_result_id (indexstrategy_result_id)"""

    create_table(hostname=hostname,
                 port=port,
                 username=username,
                 password=password,
                 database="rapd",
                 table="raddose_results",
                 table_definition=raddose_results,
                 drop=False)

    # Create Best table
    best_results = """best_result_id  mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
        indexstrategy_result_id mediumint(8) unsigned DEFAULT NULL,
        strategy_type varchar(4) DEFAULT NULL,
        atten float DEFAULT NULL,
        completeness float DEFAULT NULL,
        complexity varchar(8) DEFAULT NULL,
        i_sigi_all float DEFAULT NULL,
        i_sigi_high float DEFAULT NULL,
        phi_end float DEFAULT NULL,
        r_all float DEFAULT NULL,
        r_high float DEFAULT NULL,
        redundancy float DEFAULT NULL,
        res_limit float DEFAULT NULL,
        rot_range float DEFAULT NULL,
        total_exp float DEFAULT NULL,
        unique_in_blind float DEFAULT NULL,
        status varchar(8) DEFAULT NULL,
        timestamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (best_result_id),
        KEY indexstrategy_result_id (indexstrategy_result_id)"""

    create_table(hostname=hostname,
                 port=port,
                 username=username,
                 password=password,
                 database="rapd",
                 table="best_results",
                 table_definition=best_results,
                 drop=False)

    # Create Mosflm strategy table
    mosstrat_results = """mosstrat_result_id  mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
        indexstrategy_result_id mediumint(8) unsigned DEFAULT NULL,
        strategy_type varchar(4) DEFAULT NULL,
        completeness float DEFAULT NULL,
        delta_phi float DEFAULT NULL,
        distance float DEFAULT NULL,
        img_exposure_time float DEFAULT NULL,
        redundancy float DEFAULT NULL,
        res_limit float DEFAULT NULL,
        status varchar(8) DEFAULT NULL,
        timestamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (mosstrat_result_id),
        KEY indexstrategy_result_id (indexstrategy_result_id)"""

    create_table(hostname=hostname,
                 port=port,
                 username=username,
                 password=password,
                 database="rapd",
                 table="mosstrat_results",
                 table_definition=mosstrat_results,
                 drop=False)

    # Create index table
    indexstrategy_results = """indexstrategy_result_id mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
        data_root_dir varchar(256) DEFAULT NULL,
        distl_result_id_1 mediumint(8) DEFAULT NULL,
        distl_result_id_2 mediumint(8) DEFAULT NULL,
        labelit_result_id mediumint(8) DEFAULT NULL,
        raddose_result_id mediumint(8) DEFAULT NULL,
        best_anom_result_id mediumint(8) DEFAULT NULL,
        best_norm_result_id mediumint(8) DEFAULT NULL,
        mosstrat_anom_result_id mediumint(8) DEFAULT NULL,
        mosstrat_norm_result_id mediumint(8) DEFAULT NULL,
        fullname_1 varchar(256) DEFAULT NULL,
        fullname_2 varchar(256) DEFAULT NULL,
        image_id_1 int(10) unsigned DEFAULT NULL,
        image_id_2 int(10) unsigned DEFAULT NULL,
        process_id mediumint(8) unsigned DEFAULT NULL,
        repr varchar(128) DEFAULT NULL,
        result_id mediumint(8) unsigned DEFAULT NULL,
        sample_id varchar(16) DEFAULT NULL,
        settings_id mediumint(8) unsigned DEFAULT NULL,
        type varchar(12) DEFAULT NULL,
        work_dir varchar(256) DEFAULT NULL,
        file_summary_short varchar(128) DEFAULT NULL,
        file_summary_long varchar(128) DEFAULT NULL,
        file_summary_stac varchar(128) DEFAULT NULL,
        file_plots varchar(128) DEFAULT NULL,
        stac_file1 varchar(256) DEFAULT NULL,
        stac_file2 varchar(256) DEFAULT NULL,
        status varchar(8) DEFAULT NULL,
        timestamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (indexstrategy_result_id),
        KEY result_id (result_id)"""

    create_table(hostname=hostname,
                 port=port,
                 username=username,
                 password=password,
                 database="rapd",
                 table="indexstrategy_results",
                 table_definition=indexstrategy_results,
                 drop=False)

    # Changes from v4
    # axis >> osc_axis
    # calc_beam_center_x >> beam_center_calc_x
    # calc_beam_center_y >> beam_center_calc_y
    # image_prefix >> prefix
    # md2_x >> sample_pos_x
    # md2_y >> sample_pos_y
    # md2_z >> sample_pos_z
    # puck + sample >> robot_position varchar(16)
    # ring_current >> source_current
    # ring_mode varchar(48) >> source_mode varchar(96)
    # sample_id mediumint(8) >> sample_id varchar(16)
    # site varchar(12) > site_tag varchar(16)
    # wavelength >>>>> energy
    #
    # ADDED
    # omega float
    # rapd_detector_id varchar(64)
    #
    # DELETED
    # acc_time
    # adc
    # byte_order
    # ccd_image_saturation
    # count_cutoff
    # dim
    # header_bytes
    # md2_aperture
    # md2_prg_exp
    # md2_net_exp
    # type
    # unif_ped

    # Create the images table
    images = """image_id int(10) unsigned NOT NULL AUTO_INCREMENT,
        beam_center_calc_x float DEFAULT NULL,
        beam_center_calc_y float DEFAULT NULL,
        beam_center_x float DEFAULT NULL,
        beam_center_y float DEFAULT NULL,
        beam_gauss_x float DEFAULT NULL,
        beam_gauss_y float DEFAULT NULL,
        beam_size_x float DEFAULT NULL,
        beam_size_y float DEFAULT NULL,
        collect_mode varchar(8) DEFAULT NULL,
        date datetime DEFAULT NULL,
        detector varchar(64) DEFAULT NULL,
        detector_sn varchar(12) DEFAULT NULL,
        distance float DEFAULT NULL,
        energy float DEFAULT NULL,
        flux float DEFAULT NULL,
        fullname varchar(128) DEFAULT NULL,
        image_number smallint(5) unsigned DEFAULT NULL,
        image_prefix varchar(64) DEFAULT NULL,
        kappa float DEFAULT NULL,
        omega float DEFAULT NULL,
        osc_axis varchar(6) DEFAULT NULL,
        osc_range float DEFAULT NULL,
        osc_start float DEFAULT NULL,
        phi float DEFAULT NULL,
        pixel_size float DEFAULT NULL,
        rapd_detector_id varchar(64) DEFAULT NULL,
        robot_position varchar(16) DEFAULT NULL,
        run_id mediumint(8) unsigned DEFAULT NULL,
        run_number smallint(5) unsigned DEFAULT NULL,
        sample_id varchar(16) DEFAULT NULL,
        sample_pos_x float DEFAULT NULL,
        sample_pos_y float DEFAULT NULL,
        sample_pos_z float DEFAULT NULL,
        site_tag varchar(16) DEFAULT NULL,
        size1 smallint(5) unsigned DEFAULT NULL,
        size2 smallint(5) unsigned DEFAULT NULL,
        source_current float DEFAULT NULL,
        source_mode varchar(96) DEFAULT NULL,
        time float DEFAULT NULL,
        transmission float DEFAULT NULL,
        twotheta float DEFAULT NULL,
        timestamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (image_id),
        UNIQUE KEY blocker (fullname, date),
        KEY run_id (run_id),
        KEY timestamp (timestamp)"""

    create_table(hostname=hostname,
                 port=port,
                 username=username,
                 password=password,
                 database="rapd",
                 table="images",
                 table_definition=images,
                 drop=False)

    # Create integration tables

    # Changes from v4
    #
    # download_file >> file_download
    # hkl_file >> file_hkl
    # sample_id mediumint(8) >> sample_id varchar(16)
    # type >> request_type
    # image_end >> image_number_end
    # image_start >> image_number_start
    # merge_file >> file_merge
    # mtz_file >> file_mtz
    # parsed >> file_parsed
    # plots >> file_plots
    # sca_file >> file_sca
    # scala_log >> file_scala_log
    # summary_long >> file_summary_long
    # unmerged_sca_file >> file_unmerged_sca
    # wavelength >> energy
    # xds_log >> file_xds_log
    # xia_log >> file_xia_log
    #
    # DELETED
    # rd_analysis
    # rd_conclusion
    # twinscore
    # xscale_log

    integrate_results = """integrate_result_id mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
        a float DEFAULT NULL,
        alpha float DEFAULT NULL,
        b float DEFAULT NULL,
        beta float DEFAULT NULL,
        c float DEFAULT NULL,
        cc_anom float DEFAULT NULL,
        cc_cut_res float DEFAULT NULL,
        cc_cut_val float DEFAULT NULL,
        gamma float DEFAULT NULL,
        data_root_dir varchar(256) DEFAULT NULL,
        date datetime DEFAULT NULL,
        energy float DEFAULT NULL,
        file_download varchar(256) DEFAULT NULL,
        file_hkl varchar(256) DEFAULT NULL,
        file_merge varchar(256) DEFAULT NULL,
        file_mtz varchar(256) DEFAULT NULL,
        file_parsed varchar(256) DEFAULT NULL,
        file_plots varchar(256) DEFAULT NULL,
        file_sca varchar(256) DEFAULT NULL,
        file_scala_log varchar(256) DEFAULT NULL,
        file_summary_long varchar(256) DEFAULT NULL,
        file_unmerged_sca_ varchar(256) DEFAULT NULL,
        file_xds_log varchar(256) DEFAULT NULL,
        file_xia_log varchar(256) DEFAULT NULL,
        images_dir varchar(256) DEFAULT NULL,
        image_number_end smallint(5) unsigned DEFAULT NULL,
        image_number_start smallint(5) unsigned DEFAULT NULL,
        integrate_status varchar(12) DEFAULT NULL,
        pipeline varchar(12) DEFAULT NULL,
        proc_time time DEFAULT NULL,
        process_id mediumint(8) unsigned DEFAULT NULL,
        rcr_anom float DEFAULT NULL,
        rcr_cut_res float DEFAULT NULL,
        rcr_cut_val float DEFAULT NULL,
        repr varchar(128) DEFAULT NULL,
        request_id mediumint(8) unsigned DEFAULT NULL,
        request_type varchar(12) DEFAULT NULL,
        result_id mediumint(8) unsigned DEFAULT NULL,
        run_id mediumint(8) unsigned DEFAULT NULL,
        sample_id varchar(16) DEFAULT NULL,
        settings_id mediumint(8) unsigned DEFAULT NULL,
        shell_overall mediumint(8) unsigned DEFAULT NULL,
        shell_inner mediumint(8) unsigned DEFAULT NULL,
        shell_outer mediumint(8) unsigned DEFAULT NULL,
        spacegroup varchar(12) DEFAULT NULL,
        solved varchar(8) DEFAULT NULL,
        template varchar(256) DEFAULT NULL,
        version smallint(5) unsigned DEFAULT '0',
        work_dir varchar(256) DEFAULT NULL,
        timestamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (integrate_result_id),
        KEY result_id (result_id)"""

    create_table(hostname=hostname,
                 port=port,
                 username=username,
                 password=password,
                 database="rapd",
                 table="integrate_results",
                 table_definition=integrate_results,
                 drop=False)

    integrate_shell_results = """isr_id mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
        anom_completeness float DEFAULT NULL,
        anom_correlation float DEFAULT NULL,
        anom_multiplicity float DEFAULT NULL,
        anom_slope float DEFAULT NULL,
        cc_half float DEFAULT NULL,
        completeness float DEFAULT NULL,
        high_res float DEFAULT NULL,
        i_sigma float DEFAULT NULL,
        low_res float DEFAULT NULL,
        multiplicity float DEFAULT NULL,
        partial_bias float DEFAULT NULL,
        r_meas float DEFAULT NULL,
        r_meas_pm float DEFAULT NULL,
        r_merge float DEFAULT NULL,
        r_merge_anom float DEFAULT NULL,
        r_pim float DEFAULT NULL,
        r_pim_pm float DEFAULT NULL,
        shell_type varchar(8) DEFAULT NULL,
        total_obs int(10) unsigned DEFAULT NULL,
        unique_obs int(10) unsigned DEFAULT NULL,
        wilson_b float DEFAULT NULL,
        timestamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (isr_id)"""

    create_table(hostname=hostname,
                 port=port,
                 username=username,
                 password=password,
                 database="rapd",
                 table="integrate_shell_results",
                 table_definition=integrate_shell_results,
                 drop=False)

    # Create the runs table
    runs = """run_id mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
        anomalous varchar(6) DEFAULT NULL,
        directory varchar(128) DEFAULT NULL,
        distance float DEFAULT NULL,
        energy float DEFAULT NULL,
        image_prefix varchar(64) DEFAULT NULL,
        kappa float DEFAULT NULL,
        number_images mediumint(8) unsigned DEFAULT NULL,
        omega float DEFAULT NULL,
        osc_axis varchar(6) DEFAULT NULL,
        osc_start float DEFAULT NULL,
        osc_width float DEFAULT NULL,
        phi float DEFAULT NULL,
        run_number smallint(5) unsigned DEFAULT NULL,
        site_tag varchar(16) DEFAULT NULL,
        start_image_number mediumint(8) unsigned DEFAULT NULL,
        time float DEFAULT NULL,
        transmission float DEFAULT NULL,
        twotheta float DEFAULT NULL,
        timestamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (run_id)"""

    create_table(hostname=hostname,
                 port=port,
                 username=username,
                 password=password,
                 database="rapd",
                 table="runs",
                 table_definition=runs,
                 drop=False)

    return True

def perform_naive_install(hostname, port, username, password):
    """
    Orchestrate the installation of v2.0 of the RAPD MySQL database

    Keyword arguments
    hostname -- server where the database is accessed
    port -- port for the database
    username -- name to use accessing the database
    password -- the password
    """

    print text.blue+"Performing installation of RAPD database version %s" % VERSION + text.stop

    # Create the rapd database
    create_database(hostname=hostname,
                    port=port,
                    username=username,
                    password=password,
                    database="rapd",
                    drop=True)

    # Create the version table
    create_version_table(hostname=hostname,
                         port=port,
                         username=username,
                         password=password)

    # Create "data" tables
    create_data_tables(hostname=hostname,
                       port=port,
                       username=username,
                       password=password)


def main():
    """
    Orchestrate command-line running
    """

    print "\nrapd_createdatabase.py v%s" % VERSION
    print "==========================="

    # Get the host information
    hostname, port, username, password = get_host_info()

    # hostname = "rapd"
    # port = 3306
    # username = "rapd1"
    # password = "necatm)nster!"
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

    # Version is not understood
    else:
        print text.error+"RAPD database version %s is NOT understood." % database_version + text.stop

if __name__ == '__main__':

    main()
