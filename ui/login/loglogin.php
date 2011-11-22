<?
  //echo("one\n");
  session_start();

  //include config file
  include ('config.php');

  //sets date and time variables
  $last = gmdate("Y-m-d");
  $time = gmdate("H:i", time() + $zone);

  //echo("two\n");

  $viewer = $_SERVER['HTTP_USER_AGENT'];
  //echo($viewer);
  //echo('three');

  //checks to see if the browser the user is using is determinable
  $browser = "unknown";
  if (preg_match("/Netscape/", $viewer))
  {
    $browser = "Netscape";
  }
  else if (preg_match("/Opera/", $viewer))
  {
    $browser = "Opera";
  }else if (preg_match("/Firefox/", $viewer))
  {
    $browser = "Firefox";
  }else if (preg_match("/MSIE/", $viewer))
  {
    $browser = "Internet Explorer";
  }

  //echo($browser);

  //checks to see if the OS the user is using is determinable
  $platform = "unknown";
  if (preg_match("/Windows/", $viewer))
  {
    $platform = "Windows";
  }
  else if (preg_match("/Linux/", $viewer))
  {
    $platform = "Linux";
  }
  else if (preg_match("/Mac/", $viewer))
  {
    $platform = "Mac";
  }

  //echo($platform);

  $ip_address = $_SERVER['REMOTE_ADDR'];

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db($db_name,$connection)or die(mysql_error());
		
  //build and issue the query
  //echo("<br>$_SESSION[username]");
  //echo("<br>$last");
  //echo("<br>$time");
  //echo("<br>$ip");

  $sql ="INSERT INTO log_login VALUES
  	('$_SESSION[username]', '$last', '$time', '$ip_address', '$platform', '$browser')";
  $result = @mysql_query($sql,$connection) or die(mysql_error());
?>
