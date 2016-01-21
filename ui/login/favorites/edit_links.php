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
$result1 = @mysql_query($sql,$connection) or die(mysql_error());

?>
<html>

<head>
<meta http-equiv="Content-Language" content="en-us">
<meta http-equiv="Content-Type" content="text/html; charset=windows-1252">
<title>Edit Favorites</title>
</head>

<body>

<form method="POST" action="edit_links_2.php">
	<p><font face="Tahoma" size="2"><u><b><font color="#000080">Add a Favorite:</font></b></u><br>
	Nickname: <br>
	</font><font face="Tahoma">
	<input type="text" name="nick" size="20" style="font-family: Tahoma; font-size: 10pt"><br>
	<font size="2">URL: <br>
	</font>
	<input type="text" name="link" size="20" value="http://" style="font-family: Tahoma; font-size: 10pt"></font></p>
	<p><font face="Tahoma" size="2"><u><b><font color="#000080">Delete a 
	Favorite:</font></b></u>
	<br>
	<select size="1" name="del_fav" style="font-family: Tahoma; font-size: 10pt">
	<option></option>
<?php
while ($sql = mysql_fetch_object($result))
{
	$_nickname = $sql -> nickname; 
	
	echo "<option value=\"$_nickname\">$_nickname</option>";
	
}
?>	
	</select></font></p>
	<p><font face="Tahoma" size="2"><u><font color="#000080"><b>Edit a Favorite:</b></font></u><br>
	Edit this Favorite:<br>
	<select size="1" name="this_fav" style="font-family: Tahoma; font-size: 10pt">
	<option></option>
<?php
while ($sql = mysql_fetch_object($result1))
{
	$_nick = $sql -> nickname; 
	
	echo "<option value=\"$_nick\">$_nick</option>";
	
}
?>
	</select><br>
	To this Nickname: <br>
	</font><font face="Tahoma">
	<input type="text" name="new_nick" size="20" style="font-family: Tahoma; font-size: 10pt"><br>
	<font size="2">And this URL: <br>
	</font>
	<input type="text" name="new_link" size="20" value="http://" style="font-family: Tahoma; font-size: 10pt"><br>
	<br>
	</font>
	<input type="submit" value="Submit" name="B1" style="font-family: Tahoma; font-size: 10pt"></p>
</form>

</body>

</html>