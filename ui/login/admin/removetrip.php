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
require ("./admin_functions.php");

if ($page == ""){$page = 1;}
	
//check for authority to view this page
if (allow_access(Administrators) != "yes")
  {
    echo "You are not authorized to perform this function";
    exit;
  }
?>

<head>
<meta http-equiv="Content-Language" content="en-us">

<style type="text/css" media="screen">
@import url("../../css/rapd.css");
</style>
</head>
<body topmargin="0" leftmargin="10" rightmargin="0" bottommargin="0">
  <h1>RAPD Trip Administration</h1>

<?php
remove_trip($_SESSION[username1],$_POST[data]);

echo "<P><a href=\"trips.php\">Back to trips</a></p>";
echo "<P><a href=\"adminpage.php\">Back to the administrative control panel</a></p>";
?>
