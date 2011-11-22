<?php 
	require('./login/config.php');
	require('./login/functions.php');

	$res_id   = $_GET[res_id];
	$datadir  = $_GET[datadir];
	$trip_id  = $_GET[trip_id];
	$username = $_GET[username];
	
	if (! $username) {
		// Retreive the username from the database
	  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
	  $db         = @mysql_select_db('rapd_users',$connection)or die(mysql_error());
	  $sql        = "SELECT username FROM trips WHERE trip_id=$trip_id";
	  $result     = @mysql_query($sql,$connection) or die(mysql_error());
	  $sql        = mysql_fetch_object($result);
	  $username   = $sql -> username;
	}

	//create output array and store result id as 1st value
	$arr = array();
	$arr[] = $res_id;

	//look for an analysis_result
	$connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db         = @mysql_select_db('rapd_data',$connection)or die(mysql_error());
	$sql        = "SELECT stats_result_id FROM stats_results JOIN results ON stats_results.process_id=results.process_id WHERE results.result_id=$res_id";
	$result     = @mysql_query($sql,$connection) or die(mysql_error());
	//test for a result
	if (mysql_num_rows($result) > 0) {
		$arr[] = './users/'.$username.'/'.(string)$trip_id.'/run/'.(string)$res_id."_stats_cellsum.php";
		$arr[] = './users/'.$username.'/'.(string)$trip_id.'/run/'.(string)$res_id."_stats_xtriagesum.php";
		$arr[] = './users/'.$username.'/'.(string)$trip_id.'/run/'.(string)$res_id."_stats_xtriageplots.php";
		$arr[] = './users/'.$username.'/'.(string)$trip_id.'/run/'.(string)$res_id."_stats_molrepsum.php";
		$arr[] = './users/'.$username.'/'.(string)$trip_id.'/run/'.(string)$res_id."_stats_molrep.jpg";
	}

	//Encode in JSON
	$out = json_encode($arr);
	print $out;  

?>



