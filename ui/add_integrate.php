<?php
  require('./login/config.php');
  require('./login/functions.php');

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());

  //Now get the approximate position in the queue for processing
  $db   = @mysql_select_db('rapd_cloud',$connection)or die(mysql_error());
  $sql5 = "SELECT remote_concurrent_allowed,current_queue FROM cloud_state";
  $result5 = @mysql_query($sql5,$connection) or die(mysql_error());
  $return5 =  mysql_fetch_object($result5);
  $current_queue = $return5 -> current_queue;
  $allowed = $return5 -> remote_concurrent_allowed;

  $sql6 = "SELECT count(*) as cloud_count FROM cloud_current";
  $result6 = @mysql_query($sql6,$connection) or die(mysql_error());
  $return6 =  mysql_fetch_object($result6);
  $cloud_count = $return6 -> cloud_count; 

  //Now put the request into cloud_requests
  $db   = @mysql_select_db('rapd_cloud',$connection)or die(mysql_error());
  $sql3 = "INSERT INTO cloud_requests (request_type,
                                       original_result_id,
                                       original_type,
                                       original_id,
                                       frame_start,
                                       frame_finish,
                                       data_root_dir,
                                       ip_address,
                                       status)
                               VALUES ('$_POST[request_type]',
                                       '$_POST[original_result_id]',
                                       '$_POST[original_type]',
                                       '$_POST[original_id]',
                                       $_POST[start_frame],
                                       $_POST[finish_frame],
                                       '$_POST[datadir]',
                                       '$_POST[ip]',
                                       'request')";
  $result3 = @mysql_query($sql3,$connection) or die(mysql_error());

?>
