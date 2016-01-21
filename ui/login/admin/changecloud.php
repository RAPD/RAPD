<?php

//prevents caching
header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
header("Cache-Control: post-check=0, pre-check=0",false);
session_cache_limiter();

session_start();

//require the config file
require ("../config.php");
require ("../functions.php");

//check for authority to view this page
if (allow_access(Administrators) != "yes")
{
	echo "not authorized to perform this function";
}

//make the connection to the database
$connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
$db = @mysql_select_db("rapd_cloud",$connection)or die(mysql_error());

//make query to database
$sql ="UPDATE cloud_state SET everything = '$_POST[everything]',
                              processing = '$_POST[processing]',
                              download = '$_POST[download]',
                              remote_proccessing = '$_POST[remote_proccessing]',
                              remote_download = '$_POST[remote_download]',
                              remote_concurrent_allowed = '$_POST[remote_concurrent_allowed]'";

$result = @mysql_query($sql,$connection) or die(mysql_error());

?>

<html>
  <head>
    <meta http-equiv="refresh" content="0; url=adminpage.php">
  </head>
</html>

