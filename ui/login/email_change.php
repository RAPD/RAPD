<?php

//prevents caching
header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
header("Cache-Control: post-check=0, pre-check=0",false);
session_cache_limiter();

session_start();

//include config and functions pages
include ('config.php');
include ('functions.php');

//if a user is trying to access this page without logging in first - send them back to login
if (!$_SESSION[username])
{
	header('Location:login.html');
	exit;
}

//make connection to dbase
$connection = @mysql_connect($server, $dbusername, $dbpassword)
				or die(mysql_error());
				
$db = @mysql_select_db($db_name,$connection)
				or die(mysql_error());

//update the table with the new email address				
	$sql = "UPDATE $table_name SET 
			email = '$_POST[email]' 
			WHERE username = '$_SESSION[username]'";
	$result = @mysql_query($sql, $connection) or die(mysql_error());

//after table is updated, send the use back to their redirect to page
	header("Location:$_SESSION[redirect]");
	exit;
?>
