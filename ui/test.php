<?php
   include_once("./login/config.php");
// open a connection to the db
  $connection = @mysql_connect("rapd.nec.aps.anl.gov","rapd1","necatm)nsteR!") or die(mysql_error());

// select the db
$db = @mysql_select_db(rapd_data,$connection) or die(mysql_error());

$sql = "SELECT DISTINCT rapd_data.samples.*,rapd_users.trips.* FROM rapd_data.samples,rapd_data.results,rapd_users.trips WHERE rapd_data.samples.username='SBMRI_Jin' AND rapd_data.samples.sample_id = rapd_data.results.sample_id AND rapd_users.trips.data_root_dir=rapd_data.results.data_root_dir AND rapd_users.trips.username=rapd_data.samples.username";
$result = @mysql_query($sql);
  $arr = array();
     
     while($row = mysql_fetch_array($result, MYSQL_NUM))
       {
           array_push($arr, $row );
       };

//     print json_encode($arr);

$blanks = array(" "," "," "," "," "," "," ");
      
$sql2 = "SELECT rapd_data.samples.* FROM rapd_data.samples WHERE rapd_data.samples.sample_id NOT IN (SELECT DISTINCT rapd_data.samples.sample_id FROM rapd_data.samples,rapd_data.results,rapd_users.trips WHERE rapd_data.samples.username='SBMRI_Jin' AND rapd_data.samples.sample_id = rapd_data.results.sample_id AND rapd_users.trips.data_root_dir=rapd_data.results.data_root_dir AND rapd_users.trips.username=rapd_data.samples.username) AND rapd_data.samples.username='SBMRI_Jin'";
$result2 = @mysql_query($sql2);
  $arr2 = array();
     
     while($row = mysql_fetch_array($result2, MYSQL_NUM))
       {
        $padded = array_merge($row,$blanks);
       	array_push($arr2, $padded);
       };

$joined = array_merge($arr,$arr2);
$aaData = array("aaData" => $joined);
//Encode in JSON
$json = json_encode($aaData);
print $json;

 mysql_free_result($result);
mysql_free_result($result2);     
?>