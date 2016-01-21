<?php

//start session
session_start();

//include config and functions files
include ("../config.php");
include ("../functions.php");

echo "<p><b><font face=\"Tahoma\" size=\"2\"><a href=\"edit_links.php\">Add/Change Favorites</a></font></b></p>";

//make the connection to the database
$connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
$db = @mysql_select_db($db_name,$connection)or die(mysql_error());

//make query to database
$sql ="SELECT * FROM favorites WHERE username= '$_SESSION[user_name]'";
$result = @mysql_query($sql,$connection) or die(mysql_error());

while ($sql = mysql_fetch_object($result))
{
	$_link = $sql -> link;
	$_nickname = $sql -> nickname; 
	echo "<font face=\"Tahoma\" size=\"2\"><a target=\"_blank\" href=\"$_link\">$_nickname</a></font><br>";
}

?>
