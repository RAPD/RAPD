<?php

  //prevents caching
  header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
  header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
  header("Cache-Control: post-check=0, pre-check=0",false);
  session_cache_limiter();
  session_start();

  //clear session variables
  session_unset();

  //require the functions file
  require ("config.php");
  require ("functions.php");

  //check to see if cookies are already set, remember me
  if ((!$lr_user) || (!$lr_pass))
  {
    $username = $_POST[username];
    $password = $_POST[password];
  } else {
    $username = $lr_user;
    $password = $lr_pass;
  }

  //if username or password is blank, send to errorlogin.html
  if ((!$username) || (!$password)) 
  {
    header("Location:$base_dir/errorlogin.html");
    exit;
  }

  //sets cookies to remember this computer if the user asks to
  if ($_POST[remember] == "Yes")
  {
    setcookie("lr_user", $username, $duration, "/", $domain);
    setcookie("lr_pass", $password, $duration, "/", $domain);
  }

  if ($_POST[activate] == "Yes")
  {
    //make the connection to the database
    $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
    $db = @mysql_select_db($db_name,$connection)or die(mysql_error());
				
    //build and issue the query
    $sql ="UPDATE $table_name SET verified = '1' WHERE username = '$_POST[username]'";
    $result = @mysql_query($sql,$connection) or die(mysql_error());
  }

  //sets session variables
  sess_vars($base_dir, $server, $dbusername, $dbpassword, $db_name, $table_name, $username, $password);

  //check to see if the user has to change their password
  if ($_SESSION[pchange] == "1")
  {
    $_SESSION[redirect] = "$base_dir/pass_change.html";
  }

  //check to see if the user has activated the account
  if ($_SESSION[verified] == "0")
  {
    $_SESSION[redirect] = "$base_dir/not_activated.html";
  }

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db($db_name,$connection)or die(mysql_error());
		
  //build and issue the query
  $sql ="SELECT * FROM banned";
  $result = @mysql_query($sql,$connection) or die(mysql_error());

  while ($sql = mysql_fetch_object($result)) 
  {
    $banned = $sql -> no_access;
    if ($username == $banned || $REMOTE_ADDR == $banned)
    {
      include ('banned.html');
      exit;
    }
  }

  $last_log = last_login();

  //updates table with last log as now
  $sql = "UPDATE $table_name SET last_login = '$last_log' WHERE username = '$_SESSION[username]'";
  $result = @mysql_query($sql,$connection) or die(mysql_error());

  if (($_SESSION[redirect] != "$base_dir/errorlogin.html") && ($log_login == "1"))
  {
    include('loglogin.php');
  }

  //redirects the user	
  header("Location:$_SESSION[redirect]");
?>

<head><title>Redirect</title></head>
