<?php

//store variables into a session
session_start(install);

$_SESSION[dbase_name] 		= $_POST[dbase_name];
$_SESSION[dbase_server] 	= $_POST[dbase_server];
$_SESSION[dbase_username] 	= $_POST[dbase_username];
$_SESSION[dbase_password] 	= $_POST[dbase_password];
$_SESSION[table_name] 		= "authorize";
$_SESSION[install_dir] 		= $_POST[install_dir];
$_SESSION[time_zone] 		= $_POST[time_zone];
$_SESSION[verify_email] 	= $_POST[verify_email];
$_SESSION[default_url] 		= $_POST[default_url];
$_SESSION[min_pass_len] 	= $_POST[min_pass_len];
$_SESSION[max_pass_len] 	= $_POST[max_pass_len];
$_SESSION[log_login] 		= $_POST[log_login];
$_SESSION[group_number]         = $_POST[num_groups];
$_SESSION[domain]		= "."."$_POST[dom_name]"."$_POST[tld1]"."$_POST[tld2]";
$_SESSION[admin_email]		= $_POST[admin_email];

if (!$_POST[num_groups])
{
	header("Location:install_2.php");
}

echo "<link rel=\"stylesheet\" type=\"text/css\" href=\"../style.css\">";
include ('header.html');

if (!$_POST[dbase_name] || !$_POST[dbase_server] || !$_POST[dbase_username] || !$_POST[dbase_password] || 
	!$_POST[install_dir] || !$_POST[time_zone] ||  
	!$_POST[default_url] || !$_POST[min_pass_len] || !$_POST[max_pass_len] || !$_POST[dom_name] || !$_POST[admin_email])
{
	echo "<p>You must complete all of the fields, please <a href=\"javascript:history.go(-1)\">Go Back </a>and complete all of the fields.</p>";
	exit;
}


?>

<html>

<head>
<meta http-equiv="Content-Language" content="en-us">
<meta http-equiv="Content-Type" content="text/html; charset=windows-1252">
<link rel="stylesheet" type="text/css" href="../style.css">
<title>Login - Redirect Installation</title>
</head>

<body>

Enter the names of your Groups:<br>
(Do not use Administrators or Users as a Group Name as there are pre-configured groups)<br>
<form method="POST" action="install_2.php">
<?php
$i = 1;
while ($i <= $_SESSION[group_number])
{
echo "<p>Group $i<br><input type=\"text\" name=\"group$i\" size=\"20\"></p>";
$i++;
}
?>

<p><input type="submit" value="Submit" name="B1"></p>
</form>		


</body>

</html>
