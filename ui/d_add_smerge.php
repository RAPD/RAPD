<?php

  $merging_dataset    = $_POST[merging_dataset];
  $request_type       = $_POST[request_type];
  $original_result_id = $_POST[original_result_id]; 
  $original_type      = $_POST[original_type]; 
  $original_id        = $_POST[original_id]; 
  $start_repr         = $_POST[start_repr]; 
  $data_root_dir      = $_POST[data_root_dir]; 
  $ip_address         = $_POST[ip_address]; 

/*  $merging_dataset    = '3070::255a16b_2_1-160'; 
  $request_type       = 'smerge';
  $original_result_id = '48935';
  $original_type      = 'integrate';
  $original_id        = '3075';
  $start_repr         = '255a17p_1_1-260';
  $data_root_dir      = '/gpfs3/users/GU/Aihara_Aug10';
  $ip_address         = '164.54.212.22';
*/
  $tmp = preg_split('/\:\:/',$merging_dataset);
  $additional_id = $tmp[0];
  $additional_repr = $tmp[1];

  require('./login/config.php');
  require('./login/functions.php');

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db   = @mysql_select_db('rapd_cloud',$connection)or die(mysql_error());
/*
  //Now get the approximate position in the queue for processing
  $sql1 = "SELECT remote_concurrent_allowed,current_queue FROM cloud_state";
  $result1 = @mysql_query($sql1,$connection) or die(mysql_error());
  $return1 =  mysql_fetch_object($result1);
  $current_queue = $return1 -> current_queue;
  $allowed = $return1 -> remote_concurrent_allowed;

  $sql2 = "SELECT count(*) as cloud_count FROM cloud_current";
  $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
  $return2 =  mysql_fetch_object($result2);
  $cloud_count = $return2 -> cloud_count; 

  if ($current_queue > 0)
  {
      $position = $current_queue + 1;
      echo("<h3>This process is currently number $position in the queue</h3>"); 
  } else if ($cloud_count == $allowed) {
      echo("<h3>This process is currently first in the queue</h3>");
  } else {
      echo("<h3>This process will be dispatched immediately</h3>");
  }
*/
  //Now put the request into cloud_requests
  $sql3 = "INSERT INTO cloud_requests (request_type,original_result_id,original_type,original_id,data_root_dir,
                                       ip_address,additional_image,new_setting_id,status)
           VALUES ('$request_type','$original_result_id','$original_type','$original_id',
                   '$data_root_dir','$ip_address','$additional_id',0,'request')";
  $result3 = @mysql_query($sql3,$connection) or die(mysql_error());
/*
  //The table of settings
  echo("<table>");
  echo("  <tr><td align=center width=450>Merging $start_repr & $additional_repr</td></tr>\n");
  echo("</table>\n");
  echo("<hr><br>\n");
*/


?>
<p><a href="#" onclick="window.parent.tb_remove(); return false">Continue</a>




