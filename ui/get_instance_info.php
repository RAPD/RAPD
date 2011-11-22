<?php 

  require('./login/config.php');
  require('./login/functions.php');

  $datadir = $_GET[datadir];
  $ip      = $_GET[ip];

  //$datadir = '/gpfs2/users/necat/david/NewcomerC_Mar10';
  //$ip = '164.54.212.237';

  //create output array and store result id as 1st value
  $arr = array();

  //
  // 1st - Check to see if the directory is active
  //
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db         = @mysql_select_db('rapd_data',$connection)or die(mysql_error());
  $sql        = "SELECT beamline FROM current WHERE data_root_dir=\"$datadir\"";
  $result     = @mysql_query($sql,$connection) or die(mysql_error());
  $num        = mysql_num_rows($result);
  if ($num > 0)
  {
      $arr[] = 'True';
  }
  else
  {
      $arr[] = 'False';
  }

  //
  // 2nd - Check to see if the remote client is in the same domain as the server
  //
  $server_ip = $_SERVER['SERVER_ADDR'];
  //$server_ip = '164.54.212.170';
 
  //echo "$server_ip\n";
  //echo "$ip\n";

  if (substr($server_ip,0,10) == substr($ip,0,10))
  {
      $arr[] = 'True';
  }
  else
  {
      $arr[] = 'False';
  }

  //Encode in JSON
  $out = json_encode($arr);
  print $out;  

?>



