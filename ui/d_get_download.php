<?php 
require('./login/config.php');
require('./login/functions.php');

  $data_root_dir = $_GET[datadir];
  $result_id     = $_GET[id];
  $download_type = $_GET[type];
  $ip            = $_GET[ip];

  //$data_root_dir = '/gpfs1/users/necat/Raster1_Nov10';
  //$result_id     = 1;
  //$download_type = 'mr';
  //$ip            = '164.54.212.43';




  if ($download_type == "mr")
  {
    //make the connection to the database
    $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
    $db = @mysql_select_db('rapd_cloud',$connection)or die(mysql_error());

    //build and issue the query
    $sql1 = "INSERT INTO cloud_requests (request_type,original_result_id,original_type,original_id,data_root_dir,ip_address,status,option1) 
             VALUES (\"download_mr\",\"$result_id\",\"$download_type\",\"0\",\"$data_root_dir\",\"$ip\",\"request\",\"$_GET[spacegroup]\")";
    //echo($sql1);         
    $result1 = @mysql_query($sql1,$connection) or die(mysql_error());
  }
  else if ($download_type == "sad")
  {
    //make the connection to the database
    $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
    $db = @mysql_select_db('rapd_cloud',$connection)or die(mysql_error());

    //build and issue the query
    $sql1 = "INSERT INTO cloud_requests (request_type,original_result_id,original_type,original_id,data_root_dir,ip_address,status,option1) 
             VALUES (\"downsadcell\",\"$result_id\",\"$download_type\",\"0\",\"$data_root_dir\",\"$ip\",\"request\",\"$_GET[spacegroup]\")";
    //echo($sql1);         
    $result1 = @mysql_query($sql1,$connection) or die(mysql_error());
  }
  else if ($download_type == "integrate") {
		//make the connection to the database
    $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
    $db = @mysql_select_db('rapd_cloud',$connection)or die(mysql_error());

    //build and issue the query
    $sql1 = "INSERT INTO cloud_requests (request_type,original_result_id,original_type,original_id,data_root_dir,ip_address,status,option1) 
             VALUES (\"download_int\",\"$result_id\",\"$download_type\",\"0\",\"$data_root_dir\",\"$ip\",\"request\",\"$_GET[spacegroup]\")";
    //echo($sql1);         
    $result1 = @mysql_query($sql1,$connection) or die(mysql_error());
	}
  else if ($result_id > 0)
  {
    //make the connection to the database
    $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
    $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());

    //build and issue the query
    $sql ="SELECT type,id FROM results WHERE result_id=\"$result_id\"";
    //echo("$sql\n");
    $result = @mysql_query($sql,$connection) or die(mysql_error());
    $sql = mysql_fetch_object($result);
  
    $type = $sql -> type;
    $id   = $sql -> id;
  
    //switch to rapd_cloud db
    $db = @mysql_select_db('rapd_cloud',$connection)or die(mysql_error());
  
    //build and issue the query
    $sql2 = "INSERT INTO cloud_requests (request_type,original_result_id,original_type,original_id,data_root_dir,ip_address,status) 
           VALUES (\"$download_type\",\"$result_id\",\"$type\",\"$id\",\"$data_root_dir\",\"$ip\",\"request\")";
    //echo("$sql2\n");
    $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
  }

?>
