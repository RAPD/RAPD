<?php
   include_once("./login/config.php");
// open a connection to the db
  $connection = @mysql_connect($server,$dbusername,$dbpassword) or die(mysql_error());

// select the db
  $db = @mysql_select_db(rapd_data,$connection) or die(mysql_error());

if ( $_GET['username'] != "" )
  {
    $user = "rapd_data.samples.username='".$_GET['username']."'";
  } else {
  	$user = "rapd_data.samples.username LIKE '%'";
  }
  

// Get all the samples associated with a trip
$sql = "SELECT DISTINCT rapd_data.samples.*,rapd_users.trips.trip_id,rapd_users.trips.trip_start,rapd_users.trips.trip_finish,rapd_users.trips.data_root_dir,rapd_users.trips.beamline FROM rapd_data.samples,rapd_data.results,rapd_users.trips WHERE rapd_data.samples.sample_id = rapd_data.results.sample_id AND $user AND rapd_users.trips.data_root_dir=rapd_data.results.data_root_dir AND rapd_users.trips.username=rapd_data.samples.username";

$result = @mysql_query($sql);
  $arr = array();
     
     while($row = mysql_fetch_array($result, MYSQL_NUM))
       {
           array_push($arr, $row );
       };

//$blanks = array(" "," "," "," "," ");

// Get all the samples not associated with a trip      
$sql2 = "SELECT rapd_data.samples.*, ' ',' ',' ',' ',' ' FROM rapd_data.samples WHERE rapd_data.samples.sample_id NOT IN (SELECT DISTINCT rapd_data.samples.sample_id FROM rapd_data.samples,rapd_data.results,rapd_users.trips WHERE rapd_data.samples.sample_id = rapd_data.results.sample_id AND $user AND rapd_users.trips.data_root_dir=rapd_data.results.data_root_dir AND rapd_users.trips.username=rapd_data.samples.username) AND $user";
$result2 = @mysql_query($sql2);
  $arr2 = array();
     
     while($row = mysql_fetch_array($result2, MYSQL_NUM))
       {
       	// Add blank columns for the missing trip info
//        $padded = array_merge($row,$blanks);
//       	array_push($arr2, $padded);
       	array_push($arr2, $row);
       };

// combine the 2 arrays
$joined = array_merge($arr,$arr2);

//Encode in JSON
$aaData = array("aaData" => $joined);
$json = json_encode($aaData);
print $json;

 mysql_free_result($result);
mysql_free_result($result2);     
?>