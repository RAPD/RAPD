<?php
  require('./login/config.php');
  require('./login/functions.php');

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());

	//determine the original result type (can currently be integrate or merge)
	$sql1 = "SELECT type,id FROM results WHERE result_id=$_POST[original_result_id]";
	$result1 =  @mysql_query($sql1,$connection) or die(mysql_error());
	$return1 = mysql_fetch_object($result1);
	$type =  $return1 -> type;
	$original_id = $return1 -> id;

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

  //Strip out whitespace from the sequence
  $raw_seq = $_POST[sequence];
  $new_seq = preg_replace('/\s/','',$raw_seq);

  //Now put the request into cloud_requests
  $db   = @mysql_select_db('rapd_cloud',$connection)or die(mysql_error());
  $sql3 = "INSERT INTO cloud_requests (request_type,original_result_id,original_type,original_id,data_root_dir,
                                       ha_type,ha_number,shelxd_try,sad_res,sequence,ip_address,status)
           VALUES ('$_POST[request_type]','$_POST[original_result_id]','$type','$original_id','$_POST[datadir]',
                   '$_POST[ha_type]','$_POST[ha_number]','$_POST[shelxd_try]','$_POST[sad_res]','$new_seq',
                   '$_POST[ip]','request')";
  $result3 = @mysql_query($sql3,$connection) or die(mysql_error());

?>
