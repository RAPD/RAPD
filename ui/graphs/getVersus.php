<?php
include_once("../login/config.php");

// open a connection to the db
  $connection = @mysql_connect($server,$dbusername,$dbpassword) or die(mysql_error());
// select the db
  $db = @mysql_select_db(rapd_data,$connection) or die(mysql_error());

// set date range
  $start = $_POST[start] ." 00:00:00";
  $finish = $_POST[finish] ." 00:00:00";
  $cutoff = "images.timestamp > '$start' AND images.timestamp < '$finish'";

// set up the query
switch ($_POST['query']) {
  case xbeam:
   $sqlC = "SELECT images.image_id, ROUND(single_results.labelit_x_beam - images.beam_center_x, 2) as difference FROM single_results, images WHERE single_results.labelit_x_beam is not NULL AND images.image_id = single_results.image_id  AND images.beamline = '24_ID_C' AND $cutoff";
   $sqlE = "SELECT images.image_id, ROUND(single_results.labelit_x_beam - images.beam_center_x, 2) as difference FROM single_results, images WHERE single_results.labelit_x_beam is not NULL AND images.image_id = single_results.image_id  AND images.beamline = '24_ID_E' AND $cutoff";
   break;
  case pairxbeam:
   $sqlC = "SELECT images.image_id, ROUND(pair_results.labelit_x_beam - images.beam_center_x, 2) as difference FROM pair_results, images WHERE pair_results.labelit_x_beam is not NULL AND (images.image_id = pair_results.image1_id OR images.image_id = pair_results.image2_id) AND images.beamline = '24_ID_C' AND $cutoff ";
   $sqlE = "SELECT images.image_id, ROUND(pair_results.labelit_x_beam - images.beam_center_x, 2) as difference FROM pair_results, images WHERE pair_results.labelit_x_beam is not NULL AND (images.image_id = pair_results.image1_id OR images.image_id = pair_results.image2_id) AND images.beamline = '24_ID_E' AND $cutoff ";
   break;
  case calcxbeam:
   $sqlC = "SELECT images.image_id, ROUND(single_results.labelit_x_beam - images.calc_beam_center_x, 2) as difference FROM single_results, images WHERE single_results.labelit_x_beam is not NULL AND images.image_id = single_results.image_id  AND images.beamline = '24_ID_C' AND $cutoff";
   $sqlE = "SELECT images.image_id, ROUND(single_results.labelit_x_beam - images.calc_beam_center_x, 2) as difference FROM single_results, images WHERE single_results.labelit_x_beam is not NULL AND images.image_id = single_results.image_id  AND images.beamline = '24_ID_E' AND $cutoff";
   break;
  case ybeam:
   $sqlC = "SELECT images.image_id, ROUND(single_results.labelit_y_beam - images.beam_center_y, 2) as difference FROM single_results, images WHERE single_results.labelit_y_beam is not NULL AND images.image_id = single_results.image_id AND images.beamline = '24_ID_C' AND $cutoff ";
   $sqlE = "SELECT images.image_id, ROUND(single_results.labelit_y_beam - images.beam_center_y, 2) as difference FROM single_results, images WHERE single_results.labelit_y_beam is not NULL AND images.image_id = single_results.image_id AND images.beamline = '24_ID_E' AND $cutoff ";
   break;
  case pairybeam:
   $sqlC = "SELECT images.image_id, ROUND(pair_results.labelit_y_beam - images.beam_center_y, 2) as difference FROM pair_results, images WHERE pair_results.labelit_y_beam is not NULL AND (images.image_id = pair_results.image1_id OR images.image_id = pair_results.image2_id) AND images.beamline = '24_ID_C' AND $cutoff ";
   $sqlE = "SELECT images.image_id, ROUND(pair_results.labelit_y_beam - images.beam_center_y, 2) as difference FROM pair_results, images WHERE pair_results.labelit_y_beam is not NULL AND (images.image_id = pair_results.image1_id OR images.image_id = pair_results.image2_id) AND images.beamline = '24_ID_E' AND $cutoff " ;
   break;
  case calcybeam:
   $sqlC = "SELECT images.image_id, ROUND(single_results.labelit_y_beam - images.calc_beam_center_y, 2) as difference FROM single_results, images WHERE single_results.labelit_y_beam is not NULL AND images.image_id = single_results.image_id AND images.beamline = '24_ID_C' AND $cutoff ";
   $sqlE = "SELECT images.image_id, ROUND(single_results.labelit_y_beam - images.calc_beam_center_y, 2) as difference FROM single_results, images WHERE single_results.labelit_y_beam is not NULL AND images.image_id = single_results.image_id AND images.beamline = '24_ID_E' AND $cutoff ";
   break;
  case distance:
   $sqlC = "SELECT images.image_id, ROUND(pair_results.labelit_distance - images.distance, 2) as difference FROM pair_results, images WHERE pair_results.labelit_distance is not NULL AND (images.image_id = pair_results.image1_id OR images.image_id = pair_results.image2_id) AND images.beamline = '24_ID_C' AND $cutoff ";
   $sqlE = "SELECT images.image_id, ROUND(pair_results.labelit_distance - images.distance, 2) as difference FROM pair_results, images WHERE pair_results.labelit_distance is not NULL AND (images.image_id = pair_results.image1_id OR images.image_id = pair_results.image2_id) AND images.beamline = '24_ID_E' AND $cutoff ";
   break;

  default:

  };
$resultC = @mysql_query($sqlC);
$resultE = @mysql_query($sqlE);
echo '[{ label: "C", color: 0, data:[';
//create array of pairs of x and y values

//  $arr = array();

while($row = mysql_fetch_array($resultC))
  {
     //print_r($row);
   echo "[".$row['0'].",".$row['1']."],";

  }


echo ']},{ label: "E", color: 2, data:[';

while($row = mysql_fetch_array($resultE))
  {
     //print_r($row);
   echo "[".$row['0'].",".$row['1']."],";

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
