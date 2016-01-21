<?php

session_start(install);

include ('header.html');
include ('../functions.php');

$admin_username = $_POST[username];

if (!$_POST[first_name] || !$_POST[last_name] || !$_POST[user_name] || !$_POST[password] || !$_POST[redirect_to])
{
	echo "<p>You must complete all of the fields, please <a href=\"create_admin.php\">Go Back </a>and complete all of the fields.</p>";
	exit;
}



$pass_len = password_check($_SESSION[min_pass_len], $_SESSION[max_pass_len], $_POST[password]);
if ($pass_len == "no")
{
	echo "<p>You must use a password between $_SESSION[min_pass_len] and $_SESSION[max_pass_len] characters in length, please <a href=\"create_admin.php\">Go Back </a>and try again.</p>";
	exit;
}

//make connection to dbase
$connection = @mysql_connect($_SESSION[dbase_server], $_SESSION[dbase_username], $_SESSION[dbase_password])
				or die(mysql_error());
				
$db = @mysql_select_db($_SESSION[dbase_name],$connection)
				or die(mysql_error());
				
$check_name = "SELECT * FROM $_SESSION[table_name] WHERE username = '$_POST[user_name]'";
$name_result = @mysql_query($check_name,$connection) or die(mysql_error());

//get the number of rows in the result set
$num = mysql_num_rows($name_result);

if ($num != 0)
{
	echo "<p>That username already exists.  Please <a href=\"create_admin.php\">Go Back </a>and enter a different username.</p>";
	exit;
}

$date = last_login();

//enter information into table
$sql = "INSERT INTO $_SESSION[table_name] VALUES 
		('$_POST[first_name]', '$_POST[last_name]', '$_POST[user_name]', 
		   password('$_POST[password]'), 'Administrators', '', '', '0', '$_SESSION[admin_email]',
		  '$_POST[redirect_to]', '1', '$date')";
		  
$result = @mysql_query($sql,$connection) or die(mysql_error());

if($result)
{
?>
<html>

<head>
<meta http-equiv="Content-Language" content="en-us">
<meta http-equiv="Content-Type" content="text/html; charset=windows-1252">
<title>Login - Redirect Installation</title>
<link rel="stylesheet" type="text/css" href="../style.css">
</head>

<?php
	echo "<p>The Administrators Account has been Successfully Created.</p>";
	echo "<p>The last step is to create a file named config.php.<br>";
	echo "Copy and paste the below into this file and upload to $_SESSION[install_dir].</p>";
	echo "<textarea rows=\"47\" name=\"S1\" cols=\"120\" style=\"font-family: Tahoma; font-size: 8pt\">$_SESSION[config]</textarea></p>";
	echo "<p>For a sample of the header of each secure page, please <a href=\"../smpl_sec_header.php\">Click Here</a></p>";
	echo "<p>Should you have any difficulties, please visit the Help Forum:";
	echo "<br><a href=\"http://www.mpdolan.com/bb\">MPDolan.com Help Forum</a></p>";
	echo "<p>Please login as with the Adminstrator's Account to complete testing.";
	echo "<br><a href =\"$_SESSION[install_dir]/login.html\">Login Now</a></p><br>";
}


?>

</html>