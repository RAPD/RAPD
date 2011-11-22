<?php
  //include_once("./login/config.php");
include_once("graphs/phpsql_db.php");
// open a connection to the db
  $connection = @mysql_connect($server,$username,$password) or die(mysql_error());
// select the db
  $db = @mysql_select_db(rapd_data,$connection) or die(mysql_error());
$user = $_GET['user'];
$sheet= $_GET['sheet'];
//build and issue the query
     $sql ="SELECT sample_id,CrystalID FROM samples WHERE username='$user' AND sheetname LIKE '%$sheet'";
  $result = @mysql_query($sql,$connection) or die(mysql_error());

//create array of sample info

 
  $arr = array();
  while ($row = mysql_fetch_array($result, MYSQL_NUM))
   {
            array_push($arr, $row);
   }


//Encode in JSON
$json = json_encode($arr);
print $json;


mysql_free_result($result);

?>
