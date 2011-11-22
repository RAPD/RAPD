<?php
include_once("phpsql_db.php");

// open a connection to the db
  $connection = @mysql_connect($server,$username,$password) or die(mysql_error());

// select the db
  $db = @mysql_select_db($database,$connection) or die(mysql_error());

// set up the query
  $sqlC = "SELECT images.md2_net_exp - (images.md2_prg_exp * 1000) as exp_time, date FROM images, runs WHERE images.directory = runs.directory AND images.image_prefix = runs.image_prefix and images.md2_prg_exp IS NOT NULL AND images.beamline = '24_ID_C' ORDER  BY date DESC LIMIT 400";
  $sqlE = "SELECT images.md2_net_exp - (images.md2_prg_exp * 1000) as exp_time, date FROM images, runs WHERE images.directory = runs.directory AND images.image_prefix = runs.image_prefix and images.md2_prg_exp IS NOT NULL AND images.beamline = '24_ID_E' ORDER  BY date DESC LIMIT 400";

$resultC = @mysql_query($sqlC);
$resultE = @mysql_query($sqlE);

echo '[{ label: "C Overhead Time", color: 0, data:[';
//create array of pairs of x and y values
$i = 0;
while($row = mysql_fetch_array($resultC))
  {
     //print_r($row);
   echo "[".$i.",".$row['exp_time']."],";
   $i = $i + 1;
  }
echo ']},{ label: "E Overhead Time", color: 1, data:[';

$i = 0;

while($row = mysql_fetch_array($resultE))
  {
     //print_r($row);
   echo "[".$i.",".$row['exp_time']."],";
   $i = $i + 1;

  }

mysql_free_result($resultC);
mysql_free_result($resultE);

echo ']}]';

?>