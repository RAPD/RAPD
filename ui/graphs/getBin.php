<?php
include_once("../login/config.php");

// open a connection to the db
  $connection = @mysql_connect($server,$dbusername,$dbpassword) or die(mysql_error());
// select the db
  $db = @mysql_select_db(rapd_data,$connection) or die(mysql_error());

// set date range
  $start = $_POST[start] ." 00:00:00";
  $finish = $_POST[finish] ." 00:00:00";
  $cutoff = "timestamp > '$start' AND timestamp < '$finish'";

// set up the query
switch ($_POST['query']) {
  case bin:
    $sqlC = "SELECT binning, count(*) as count FROM images WHERE beamline = '24_ID_C' AND $cutoff GROUP BY binning";
    $sqlE = "SELECT binning, count(*) as count FROM images WHERE beamline = '24_ID_E' AND $cutoff GROUP BY binning";
    $sql = "SELECT binning, count(*) as count FROM images WHERE $cutoff GROUP BY binning";
   break;
  case robot:
    $sqlC = "SELECT puck, count(*) as count FROM images WHERE beamline = '24_ID_C' AND puck != 'R' AND puck != '1' AND $cutoff GROUP BY puck";
    $sqlE = "SELECT puck, count(*) as count FROM images WHERE beamline = '24_ID_E' AND puck != 'R' AND puck != '1' AND $cutoff GROUP BY puck";
    $sql = "SELECT puck, count(*) as count FROM images WHERE $cutoff AND puck != 'R' AND puck != '1' GROUP BY puck";
   break;

  default:

  };
$resultC = @mysql_query($sqlC);
$resultE = @mysql_query($sqlE);
$result = @mysql_query($sql);
echo '[{ label: "Total", color: 0, data:[';
//create array of pairs of x and y values

//  $arr = array();
$i = 0;
while($row = mysql_fetch_array($result))
  {
     //print_r($row);
   echo "[$i,".$row['1']."],";
   $i++;
  }

  echo ']},{ label: "C", color: 1, data:[';

$i = 0;
while($row = mysql_fetch_array($resultC))
  {
     //print_r($row);
   echo "[$i,".$row['1']."],";
   $i++;

  }
echo ']},{ label: "E", color: 2, data:[';

$i = 0;
while($row = mysql_fetch_array($resultE))
  {
     //print_r($row);
   echo "[$i,".$row['1']."],";
   $i++;

  }
// while($row = mysql_fetch_array($result, MYSQL_NUM))
//    {
//            array_push($arr, $row );
//    }

mysql_free_result($resultC);
mysql_free_result($resultE);
mysql_free_result($result);

echo ']}]';
?>
