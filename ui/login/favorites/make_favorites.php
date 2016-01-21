<?php

//prevent caching
header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
header("Cache-Control: post-check=0, pre-check=0",false);
session_cache_limiter();

//start session
session_start();

//include config and functions files
include ("../config.php");
include ("../functions.php");

//make the connection to the database
$connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
$db = @mysql_select_db($db_name,$connection)or die(mysql_error());

//make query to database
$sql ="CREATE TABLE IF NOT EXISTS favorites
(
	username	VARCHAR(20),
	nickname	VARCHAR(20),
	link		VARCHAR(100)
)";
$result = @mysql_query($sql,$connection) or die(mysql_error());

if ($result)
{
	echo "<font face=\"Tahoma\" size=\"2\">Your Favorites table has been created.</font><br>";
}

?>
<html>
<meta http-equiv="refresh" content="3; url=index.htm">
</html>