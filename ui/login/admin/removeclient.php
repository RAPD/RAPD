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
<body class='banner' topmargin="0" leftmargin="10" rightmargin="0" bottommargin="0">
  <h1>RAPD Clients Administration</h1>

<?php
//check required fields
if ($_POST[client_ip] == "")
{
    echo "<P>Client IP Address is empty, please try again.</p>";
    echo "<P><a href=\"../../main.php\">Main Page</a></P>";
    echo "<P><a href=\"clients.php\">Back to clients</a></p>";
    echo "<P><a href=\"adminpage.php\">Back to the administrative control panel</a></p>";
    exit;
}

//make the connection to the database
$connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
$db = @mysql_select_db($db_name,$connection)or die(mysql_error());

//make query to database
$sql ="DELETE FROM authorized_clients WHERE client_ip='$_POST[client_ip]' AND beamline='$_POST[beamline]'";
$result = @mysql_query($sql,$connection) or die(mysql_error());

//get the number of rows in the result set
$num = mysql_num_rows($result);

//check if that username already exists
if ($num != 0)
  {
      echo "<P>Sorry, deletion unsuccessful.</P>";
      echo "<P><a href=\"../../main.php\">Main Page</a></P>";
      echo "<P><a href=\"clients.php\">Back to clients</a></p>";
      echo "<P><a href=\"adminpage.php\">Back to the administrative control panel</a></p>";
  }
else
  {
    mysql_close($connection);
    echo "<P>Client successfully deleted from the database.</P>";
    echo "<P><a href=\"../../main.php\">Main Page</a></P>";
    echo "<P><a href=\"../../data_main.php\">View Data - User Perspective</a></P>";
    echo "<P><a href=\"../../data_admin.php\">View Data - Administrator Perspective</a></P>";
    echo "<P><a href=\"clients.php\">Back to clients</a></p>";
    echo "<P><a href=\"adminpage.php\">Back to the administrative control panel</a></p>";
  }
?>
</body>
