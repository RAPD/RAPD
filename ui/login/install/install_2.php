<?php

session_start(install);

echo "<link rel=\"stylesheet\" type=\"text/css\" href=\"../style.css\">";

include ('header.html');

$group_array = array();

$i = 1;
while ($i <= $_SESSION[group_number])
{
	$group = "group$i";
	array_push($group_array, "$_POST[$group]");
	$i++;
}

$i = 1;

//test connection to dbase verifing dbase name, server, username and password

$connection = @mysql_connect($_SESSION[dbase_server], $_SESSION[dbase_username], $_SESSION[dbase_password])
				or die(mysql_error());
				
$db = @mysql_select_db($_SESSION[dbase_name],$connection)
				or die(mysql_error());
				
//create a message to be displayed at the end of the installation
if ($db)
{
	echo "Connection to Database $_SESSION[dbase_name] Successful.<br>";
}else{
	echo "<p>There was an error connecting to the database.</p>";
	echo "<p><a href=\"javascript:history.go(-2)\">Please go back and check your Database information.</a></p>";
	exit;
}

//create a table in that dbase
$sql ="
CREATE TABLE IF NOT EXISTS $_SESSION[table_name]
(
	firstname	VARCHAR(20),
	lastname	VARCHAR(20),
	username	VARCHAR(20),
	password	VARCHAR(50),
	group1		VARCHAR(20),
	group2		VARCHAR(20),
	group3		VARCHAR(20),
	pchange		VARCHAR(1),
	email		VARCHAR(100),
	redirect	VARCHAR(100),
	verified	VARCHAR(1),
	last_login	DATE
)";

$result = @mysql_query($sql,$connection) 
			or die(mysql_error());

if ($result)
{
	echo "Table $_SESSION[table_name] has been created.<br>";
}else{
	echo "<p>There was an error creating the table.</p>";
	echo "<p><a href=\"javascript:history.go(-2)\">Please go back and check your information.</a></p>";
	exit;
}	

//create a table in that dbase
$sql_log ="
CREATE TABLE IF NOT EXISTS log_login
(
	username	VARCHAR(20),
	date		VARCHAR(20),
	time		VARCHAR(20),
	ip_addr		VARCHAR(20),
	oper_sys	VARCHAR(20),
	brow		VARCHAR(20)
)
";

$result_log = @mysql_query($sql_log,$connection) 
			or die(mysql_error());

if ($result_log)
{
	echo "Table log_login has been created.<br>";
}else{
	echo "<p>There was an error creating the table.</p>";
	echo "<p><a href=\"javascript:history.go(-2)\">Please go back and check your information.</a></p>";
	exit;
}

//create a table in that dbase
$sql_ban ="
CREATE TABLE IF NOT EXISTS banned
(
	no_access	VARCHAR(30),
	type		VARCHAR(10)
)
";

$result_ban = @mysql_query($sql_ban,$connection) 
			or die(mysql_error());

if ($result_ban)
{
	echo "Table banned has been created.<br>";
}else{
	echo "<p>There was an error creating the table.</p>";
	echo "<p><a href=\"javascript:history.go(-2)\">Please go back and check your information.</a></p>";
	exit;
}

//create a table in that dbase
$sql_trash ="
CREATE TABLE IF NOT EXISTS trash
(
	firstname	VARCHAR(20),
	lastname	VARCHAR(20),
	username	VARCHAR(20),
	password	VARCHAR(50),
	group1		VARCHAR(20),
	group2		VARCHAR(20),
	group3		VARCHAR(20),
	pchange		VARCHAR(1),
	email		VARCHAR(100),
	redirect	VARCHAR(100),
	verified	VARCHAR(1),
	last_login	DATE,
	del_date	DATE
	)
";

$result_trash = @mysql_query($sql_trash,$connection) 
			or die(mysql_error());

if ($result_trash)
{
	echo "Table trash has been created.<br>";
}else{
	echo "<p>There was an error creating the table.</p>";
	echo "<p><a href=\"javascript:history.go(-2)\">Please go back and check your information.</a></p>";
	exit;
}


//create a table in that dbase
$sql_trips ="
CREATE TABLE IF NOT EXISTS trips
(       trip_id        MEDIUMINT UNSIGNED NOT NULL, 
        user_name      VARCHAR(20),
        trip_start     DATETIME,
        trip_finish    DATETIME,
        data_root_dir  VARCHAR(128),
        beamline       VARCHAR(16),
        PRIMARY KEY (trip_id)
	)
";

$result_trips = @mysql_query($sql_trips,$connection) 
			or die(mysql_error());

if ($result_trips)
{
	echo "Table trips has been created.<br>";
}else{
	echo "<p>There was an error creating the table.</p>";
	echo "<p><a href=\"javascript:history.go(-2)\">Please go back and check your information.</a></p>";
	exit;
}



?>

<html>

<head>
<meta http-equiv="Content-Language" content="en-us">
<meta http-equiv="Content-Type" content="text/html; charset=windows-1252">
<title>Login - Redirect Installation</title>
<link rel="stylesheet" type="text/css" href="../style.css">
</head>

<body>

<table border="1" width="100%" id="table1">
	<tr>
		<td width="100%">
		
<?php
$_SESSION[config] = "
&lt;?

//set up the names of the database and table
\$db_name =\"$_SESSION[dbase_name]\";
\$table_name =\"$_SESSION[table_name]\";

//connect to the server and select the database
\$server = \"$_SESSION[dbase_server]\";
\$dbusername = \"$_SESSION[dbase_username]\";
\$dbpassword = \"$_SESSION[dbase_password]\";

//domain information
\$domain = \"$_SESSION[domain]\";

//Change to \"0\" to turn off the login log
\$log_login = \"$_SESSION[log_login]\";

//base_dir is the location of the files, ie http://www.yourdomain/login
\$base_dir = \"$_SESSION[install_dir]\";

//length of time the cookie is good for - 7 is the days and 24 is the hours
//if you would like the time to be short, say 1 hour, change to 60*60*1
\$duration = time()+(60*60*24*30);

//the site administrator\'s email address
\$adminemail = \"$_SESSION[admin_email]\";

//sets the time to EST
\$zone=3600*$_SESSION[time_zone];

//do you want the verify the new user through email if the user registers themselves?
//yes = \"0\" :  no = \"1\"
\$verify = \"$_SESSION[verify_email]\";

//default redirect, this is the URL that all self-registered users will be redirected to
\$default_url = \"$_SESSION[default_url]\";

//minimum and maximum password lengths
\$min_pass = $_SESSION[min_pass_len];
\$max_pass = $_SESSION[max_pass_len];


\$num_groups = $_SESSION[group_number]+2;
\$group_array = array(";
$i = 0;
while ($i < $_SESSION[group_number])
{
	$group = "group$i";
	$_SESSION[config] .= "\"$group_array[$i]\", ";
	$i++;
}
$_SESSION[config] .= "\"Users\",";
$_SESSION[config] .= "\"Administrators\");

?>";

include ('create_admin.php');

?></tr>
</table>


</body>

</html>


