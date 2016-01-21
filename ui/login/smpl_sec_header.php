<?php

$abs = getcwd();
$viewer = $HTTP_USER_AGENT;

echo "&lt;?php<br><br>
//prevents caching<br>
header(\"Expires: Sat, 01 Jan 2000 00:00:00 GMT\");<br>
header(\"Last-Modified: \".gmdate(\"D, d M Y H:i:s\").\" GMT\");<br>
header(\"Cache-Control: post-check=0, pre-check=0\",false);<br>
session_cache_limiter();<br>
session_start();<br>
<br>";

if (preg_match("/Windows NT/", $viewer))
{
	echo "require('$abs\config.php');<br>
	<br>
	require('$abs\functions.php'); <br>
	<br>";
}
else
{
	echo "require('$abs/config.php');<br>
	<br>
	require('$abs/functions.php'); <br>
	<br>";
}

echo "
//this is group name or username of the group or person that you wish to allow access to<br>
// - please be advise that the Administrators Groups has access to all pages.<br>
if (allow_access(Administrators) != \"yes\")<br>
{                       <br>
";
if (preg_match("/Windows NT/", $viewer))
{
	echo "
	include ('$abs\\no_access.html'); <br>
	";
}
else
{
	echo "include ('$abs/no_access.html'); <br>";
}
echo "
exit;<br>
}<br>
?>";

?>
