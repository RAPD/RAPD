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
$sql ="SELECT * FROM favorites WHERE username= '$_SESSION[user_name]'";
$result = @mysql_query($sql,$connection) or die(mysql_error());

if ($_POST[nick] != "")
{
	//make query to database
	$sql ="INSERT INTO favorites VALUES ('$_SESSION[user_name]', '$_POST[nick]', '$_POST[link]')";
	$result = @mysql_query($sql,$connection) or die(mysql_error());
}

if ($_POST[del_fav] != "")
{
	//make query to database
	$sql ="DELETE FROM favorites WHERE username = '$_SESSION[user_name]' AND nickname = '$_POST[del_fav]'";
	$result = @mysql_query($sql,$connection) or die(mysql_error());
}

if ($_POST[this_fav] != "")
{
	//make query to database
	$sql ="DELETE FROM favorites WHERE username = '$_SESSION[user_name]' AND nickname = '$_POST[this_fav]'";
	$sql2 = "INSERT INTO favorites VALUES ('$_SESSION[user_name]', '$_POST[new_nick]', '$_POST[new_link]')";
	$result = @mysql_query($sql,$connection) or die(mysql_error());
	$result2 = @mysql_query($sql2,$connection) or die(mysql_error());
}

header("Location:links.php");

?>