<?

//prevents caching
header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
header("Cache-Control: post-check=0, pre-check=0",false);
session_cache_limiter();

session_start();

//require the config file
require ("config.php");
require ("functions.php");

//checks password length
if (password_check($min_pass, $max_pass, $_POST[password]) == "no")
{
?>
<html>

<head>
<meta http-equiv="Content-Type" content="text/html; charset=windows-1252">
<meta http-equiv="refresh" content="0; url=javascript:history.go(-1)">
<title>Registration</title>
<style type="text/css" media="screen">
@import url("../css/rapd.css");
</style>
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

//make the connection to the database
$connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
$db = @mysql_select_db($db_name,$connection)or die(mysql_error());

//make query to database
$sql ="SELECT * FROM $table_name WHERE username= '$_POST[username]'";
$result = @mysql_query($sql,$connection) or die(mysql_error());

//get the number of rows in the result set
$num = mysql_num_rows($result);

//checks it see if that username already exists
if ($num != 0){

echo "<P>Sorry, that username already exists.</P>";
echo "<P><a href=\"#\" onClick=\"history.go(-1)\">Try Another Username.</a></p>";
exit;

}else{
$sql = "INSERT INTO $table_name VALUES
('$_POST[firstname]', '$_POST[lastname]', '$_POST[username]', password('$_POST[password]'), 'Users', '', '', '$pchange', 
'$_POST[email]', '$default_url', '$verify', '')";

$result = @mysql_query($sql,$connection) or die(mysql_error());
}

//checks to see if the user needs to verify their email address before accessing the site
if ($verify == "0")
{
	$mailheaders = "From: www$domain\n";
	$mailheaders .= "Your account has been created.\n";
	$mailheaders .= "Please activate your account now by visiting this page:\n";
	$mailheaders .= "$base_dir/activate.html\n";


	$to = "$_POST[email]";
	$subject = "Please activate your account";

mail($to, $subject, $mailheaders, "From: No Reply <$adminemail>\n");

}else{
	header('Location:login.html');
}



?>

<HTML>
<HEAD>
<TITLE>Add a User</TITLE>
</HEAD>
<BODY>
<H1>Please check your email to activate your account.</H1>
</BODY>
</HTML>
