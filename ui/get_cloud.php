<?php 
  require('./login/config.php');
  require('./login/functions.php');

  //Start handling the POST
  $datadir = $_GET[datadir];
  $lastid  = $_GET[id];
  $ip      = $_GET[ip_address];
  $user    = $_GET[user];
  $trip_id = $_GET[trip_id];

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db(rapd_cloud,$connection)or die(mysql_error());        
  
  //build and issue the query
  $sql ="SELECT cloud_complete_id,request_type,result_id,archive FROM cloud_complete WHERE status='new' AND ip_address='$ip' AND data_root_dir='$datadir' AND cloud_complete_id>$lastid";
  $result = @mysql_query($sql,$connection) or die(mysql_error());
  
  $arr = array();
  if (mysql_num_rows($result) > 0) {

    while ($sql = mysql_fetch_object($result)) {
      $cloud_id = $sql -> cloud_complete_id;
      $type     = $sql -> request_type;
      $id       = $sql -> result_id; 
      $archive  = $sql -> archive;
      if ($type == 'downimage')
      {
        $file    = './users/'.$user.'/'.(string)$trip_id.'/download/'.$archive;
        $arr[]   = "download";
        $arr[]   = $file; 
        $arr[]   = "new"; 
        $arr[] = $cloud_id;
      }
      else if ($type == 'downpackage')
      {
        $file    = './users/'.$user.'/'.(string)$trip_id.'/download/'.$archive;
        $arr[]   = "download";
        $arr[]   = $file;
        $arr[]   = "new";
        $arr[] = $cloud_id;
      }
      else if ($type == 'downproc')
      {
        $file    = './users/'.$user.'/'.(string)$trip_id.'/download/'.$archive;
        $arr[]   = "download";
        $arr[]   = $file;
        $arr[]   = "new";
        $arr[] = $cloud_id;
      }
      else if ($type == 'downshelx')
      {
        $file    = './users/'.$user.'/'.(string)$trip_id.'/download/'.$archive;
        $arr[]   = "download";
        $arr[]   = $file;
        $arr[]   = "new";
        $arr[]   = $cloud_id;
      }
      else if ($type == 'downsad')
      {
        $file    = './users/'.$user.'/'.(string)$trip_id.'/download/'.$archive;
        $arr[]   = "download";
        $arr[]   = $file;
        $arr[]   = "new";
        $arr[]   = $cloud_id;
      }
      else if ($type == 'download_mr')
      {
        $file    = './users/'.$user.'/'.(string)$trip_id.'/download/'.$archive;
        $arr[]   = "download";
        $arr[]   = $file;
        $arr[]   = "new";
        $arr[]   = $cloud_id;
      }
      else if ($type == 'downsadcell')
      {
        $file    = './users/'.$user.'/'.(string)$trip_id.'/download/'.$archive;
        $arr[]   = "download";
        $arr[]   = $file;
        $arr[]   = "new";
        $arr[]   = $cloud_id;
      }
      else if ($type == 'download_int')
      {
        $file    = './users/'.$user.'/'.(string)$trip_id.'/download/'.$archive;
        $arr[]   = "download";
        $arr[]   = $file;
        $arr[]   = "new";
        $arr[]   = $cloud_id;
      }
    }
  }

  //update the status of the cloud if there are no downloads to interject...
  else {
    // Check to see if the remote client is in the same domain as the server
    $server_ip = $_SERVER['SERVER_ADDR'];
    if (substr($server_ip,0,10) == substr($ip,0,10))
    {
      $sql     ="SELECT processing,download FROM cloud_state";
      $result  = @mysql_query($sql,$connection) or die(mysql_error());
      $sql_obj = mysql_fetch_object($result);
      $arr[] = 'local';
      $arr[] = $sql_obj -> download;
      $arr[] = $sql_obj -> processing;
    }
    else
    {
      $sql     ="SELECT remote_processing,remote_download FROM cloud_state";
      $result  = @mysql_query($sql,$connection) or die(mysql_error());
      $sql_obj = mysql_fetch_object($result);
      $arr[] = 'remote';
      $arr[] = $sql_obj -> remote_download;
      $arr[] = $sql_obj -> remote_processing;
    }
  }

  //Encode in JSON
  $out = json_encode($arr);
  print $out;  
?>

