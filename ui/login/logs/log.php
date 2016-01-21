<?php

session_start();

include("../config.php");
include("../functions.php");


//make connection to dbase
$connection = @mysql_connect($server, $dbusername, $dbpassword)
	or die(mysql_error());
				
$db = @mysql_select_db($db_name,$connection)
	or die(mysql_error());

$sql="SELECT * FROM log_login ORDER BY '$_POST[D1]'";
$result = @mysql_query($sql, $connection) or die(mysql_error());

while ($sql = mysql_fetch_object($result)) 
{
	$user = $sql -> username;
	$whend	=	$sql -> date;
	$whent	=	$sql -> time;
	$ip_add	=	$sql -> ip_addr;
	$operat	= 	$sql -> oper_sys;
	$browse	=	$sql -> brow;
	
	echo "<p><font size=\"1\" face=\"Tahoma\"><b>Username: </b>$user</font><br>";
	echo "<font size=\"1\" face=\"Tahoma\"><b>Date: </b>$whend</font><br>";
	echo "<font size=\"1\" face=\"Tahoma\"><b>Time: </b>$whent</font><br>";
	echo "<font size=\"1\" face=\"Tahoma\"><b>IP Address: </b>$ip_add</font><br>";
	echo "<font size=\"1\" face=\"Tahoma\"><b>O/S:	</b>$operat</font><br>";
	echo "<font size=\"1\" face=\"Tahoma\"><b>Browser: </b>$browse</font></p>";
}

?>
