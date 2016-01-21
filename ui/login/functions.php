<?php

//function to get the date
function last_login()
{
	$date = gmdate("Y-m-d");
	return $date;
}

//function that sets the session variable
function sess_vars($base_dir, $server, $dbusername, $dbpassword, $db_name, $table_name, $user, $pass)
{
	//make connection to dbase
	$connection = @mysql_connect($server, $dbusername, $dbpassword)
				or die(mysql_error());
				
	$db = @mysql_select_db($db_name,$connection)
				or die(mysql_error());
				
	$sql = "SELECT * FROM $table_name WHERE username = '$user' and password = password('$pass')";

	$result = @mysql_query($sql, $connection) or die(mysql_error());


	//get the number of rows in the result set
	$num = mysql_num_rows($result);

	//set session variables if there is a match
	if ($num != 0) 
	{
		while ($sql = mysql_fetch_object($result)) 
		{
			$_SESSION[first_name] 	= $sql -> firstname;
			$_SESSION[last_name] 	= $sql -> lastname; 
			$_SESSION[username]  	= $sql -> username;       
			$_SESSION[password] 	= $sql -> password;
			$_SESSION[group1]	 	= $sql -> group1;
			$_SESSION[group2]	 	= $sql -> group2;
			$_SESSION[group3] 		= $sql -> group3;
			$_SESSION[pchange]		= $sql -> pchange;  
			$_SESSION[email] 		= $sql -> email;
			$_SESSION[redirect]		= $sql -> redirect;
			$_SESSION[verified]		= $sql -> verified;
			$_SESSION[last_login]	= $sql -> last_login;
		}
	}else{
		$_SESSION[redirect] = "$base_dir/errorlogin.html";
	}
}

//functions that will determine if access is allowed
function allow_access($group)
{
	if ($_SESSION[group1] == "$group" || $_SESSION[group2] == "$group" || $_SESSION[group3] == "$group" ||
		$_SESSION[group1] == "Administrators" || $_SESSION[group2] == "Administrators" || $_SESSION[group3] == "Administrators" ||
		$_SESSION[username] == "$group")
		{
			$allowed = "yes";
		}else{
			$allowed = "no";
		}
	return $allowed;
}

function allow_local()
{
  require('/var/www/html/rapd/login/config.php');
  $client_ip = $_SERVER['REMOTE_ADDR'];         
  //echo("<p>SERVER  $client_ip</p>");
  
  //make connection to dbase
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db($db_name,$connection) or die(mysql_error());
  $sql = "SELECT * FROM authorized_clients WHERE client_ip='$client_ip'";
  $result = @mysql_query($sql, $connection) or die(mysql_error());

  //get the number of rows in the result set
  $num = mysql_num_rows($result);
  if ($num != 0)
  {
    $sql = mysql_fetch_object($result);
    $allowed = $sql -> beamline;
    //echo("<p>$allowed</p>");
  } else {
    $allowed = "no";
  }
  return($allowed);  
}

function allow_local_data($data_root_dir)
{
  require('/var/www/html/rapd/login/config.php');

  //obtain the remote server ip address
  $client_ip = $_SERVER['REMOTE_ADDR'];

  //make connection to dbase
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db($db_name,$connection) or die(mysql_error());

  //get the beamlines this server is permitted to see
  $sql = "SELECT * FROM authorized_clients WHERE client_ip='$client_ip'";
  $result1 = @mysql_query($sql, $connection) or die(mysql_error());
  $num = mysql_num_rows($result1);
  if ($num != 0)
  {
    $sql1 = mysql_fetch_object($result1);
    $bl_allowed = $sql1 -> beamline;
  } else {
    return("no");
  }

  //now check if the drd is in current
  $db = @mysql_select_db('rapd_data',$connection) or die(mysql_error());
  $sql = "SELECT * FROM current WHERE data_root_dir='$data_root_dir'";
  $result2 = @mysql_query($sql, $connection) or die(mysql_error());
  //get the number of rows in the result set
  $num = mysql_num_rows($result2);
  if ($num != 0)
  {
    if($bl_allowed == 'ALL')
    {
      return("yes");
    }
    else
    {
      while($sql2 = mysql_fetch_object($result2))
      {
        $bl = $sql2 -> beamline;
        if($bl == $bl_allowed)
        {
          return("yes");
        }
      }
      return("no");  
    }

  } else {
    return("no");
  }
}

function allow_user()
{
  require('/var/www/html/rapd/login/config.php');

  //make connection to dbase
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db($db_name,$connection) or die(mysql_error());
  $sql = "SELECT * FROM $table_name WHERE username = '$_SESSION[username]' and password = '$_SESSION[password]'";
  $result = @mysql_query($sql, $connection) or die(mysql_error());
  //get the number of rows in the result set
  $num = mysql_num_rows($result);
  //set session variables if there is a match
  if ($num != 0) 
  {
    $allowed = "yes";
  }else{
    $allowed = "no";
  }
  return $allowed;
}

function clear_candidate_dirs()
{
  require('/var/www/html/rapd/login/config.php');

  //make connection to dbase
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db($db_name,$connection) or die(mysql_error());
  $sql = "DELETE FROM candidate_dirs";
  $result = @mysql_query($sql, $connection) or die(mysql_error());
}

//function to check the length of the requested password
function password_check($min_pass, $max_pass, $pass)
{
	$valid = "yes";
	if ($min_pass > strlen($pass) || $max_pass < strlen($pass))
	{
		$valid = "no";
	}

	return $valid;
}

?>
