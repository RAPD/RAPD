<?

//prevents caching
header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
header("Cache-Control: post-check=0, pre-check=0",false);
session_cache_limiter();
session_start();

//require config and functions files
require('../config.php');
require('../functions.php');

//check for administrative rights
if (allow_access(Administrators) != "yes")
{
	include ('../no_access.html');
	exit;
}

//make the connection to the database
$connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
$db = @mysql_select_db($db_name,$connection)or die(mysql_error());

//make the dbase query selecting only email address
$sql ="SELECT * FROM $table_name";
$result = @mysql_query($sql,$connection) or die(mysql_error());

echo "Your Message Has Been Sent to the Following Users:<br><br>";
	while ($sql = mysql_fetch_object($result)) 
	{
	    $e_addr = $sql -> email;
		$e_user = $sql -> username;
		$subject = $_POST[e_subject];
		$mailheaders = $_POST[e_message]; 
		mail($e_addr, $subject, $mailheaders, "From: No Reply <$adminemail>\n");
		echo "$e_user<br>";
	}
	
?>