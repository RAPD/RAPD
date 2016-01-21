<?php

//prevents caching
header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
header("Cache-Control: post-check=0, pre-check=0",false);
session_cache_limiter();

session_start();

//include config and functions files
include ('config.php');
include ('functions.php');

//if user tries to access this page without logging in, this will send the user back to login.html
if (!$_SESSION[username])
{
	header('Location:login.html');
	exit;
}

//checks password length
if (password_check($min_pass, $max_pass, $_POST[p_word]) == "no")
{
?>
<html>

<head>
<meta http-equiv="Content-Type" content="text/html; charset=windows-1252">
<meta http-equiv="refresh" content="0; url=pass_change.html">
<title>Password Change</title>
<script language="JavaScript">
<!--
function FP_popUpMsg(msg) {//v1.0
 alert(msg);
}
// -->
</script>
</head>

<body onload="FP_popUpMsg('Your password must be between <? echo $min_pass; ?> & <? echo $max_pass; ?> characters.')">

</body>

</html>
<?
exit;
}

//make connection to dbase
$connection = @mysql_connect($server, $dbusername, $dbpassword)
				or die(mysql_error());
				
$db = @mysql_select_db($db_name,$connection)
				or die(mysql_error());

//updates the table with the new password				
	$sql = "UPDATE $table_name SET 
			password = password('$_POST[p_word]') 
			WHERE username = '$_SESSION[username]'";
	$result = @mysql_query($sql, $connection) or die(mysql_error());

//update the password
        $sql = "SELECT password from $table_name WHERE username = '$_SESSION[username]'";
        $result = @mysql_query($sql, $connection) or die(mysql_error());
        $sql = mysql_fetch_object($result);        
	$_SESSION[password] = $sql -> password;

//resets the password change required to no	
	$set_chng = "UPDATE $table_name SET
			pchange = '0' WHERE username = '$_SESSION[username]'";
	$result1 = @mysql_query($set_chng, $connection) or die(mysql_error());			

//gets that users redirect to	
	$get_redir = "SELECT * FROM $table_name WHERE username = '$_SESSION[username]'";
	$result2 = @mysql_query($get_redir, $connection) or die(mysql_error());
	while ($get_redir = mysql_fetch_object($result2)) 
		{	
			$_SESSION[redirect] = $get_redir -> redirect;
		}

//sends the user to their redirect to
	header("Location:$_SESSION[redirect]");
	exit;
?>
