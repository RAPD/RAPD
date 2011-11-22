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
  case date:
    //    echo 'date';
    $sqlC = "SELECT FLOOR(UNIX_TIMESTAMP(timestamp)/86400)*86400000 as dates, count(*) as count FROM images WHERE beamline = '24_ID_C' AND $cutoff GROUP BY dates";
    $sqlE = "SELECT FLOOR(UNIX_TIMESTAMP(timestamp)/86400)*86400000 as dates, count(*) as count FROM images WHERE beamline = '24_ID_E' AND $cutoff GROUP BY dates";
    $sql = "SELECT FLOOR(UNIX_TIMESTAMP(timestamp)/86400)*86400000 as dates, count(*) as count FROM images WHERE $cutoff GROUP BY dates";
    break;
  case day:
    //    echo 'day';
    $sqlC = "SELECT DATE_FORMAT(date, '%w') as day, count(*) as count FROM images WHERE beamline = '24_ID_C' AND $cutoff GROUP BY day";
    $sqlE = "SELECT DATE_FORMAT(date, '%w') as day, count(*) as count FROM images WHERE beamline = '24_ID_E' AND $cutoff GROUP BY day";
    $sql = "SELECT DATE_FORMAT(date, '%w') as day, count(*) as count FROM images WHERE $cutoff GROUP BY day";
    break;
  case hour:
    //    echo 'hour';
    $sqlC = "SELECT DATE_FORMAT(date, '%H') as hour, count(*) as count FROM images WHERE beamline = '24_ID_C' AND $cutoff GROUP BY hour";
    $sqlE = "SELECT DATE_FORMAT(date, '%H') as hour, count(*) as count FROM images WHERE beamline = '24_ID_E' AND $cutoff GROUP BY hour";
    $sql = "SELECT DATE_FORMAT(date, '%H') as hour, count(*) as count FROM images WHERE $cutoff GROUP BY hour";
    break;
  case wavelength:
    $sqlC = "SELECT ROUND(wavelength, 4) as wavelength, count(*) as count FROM images WHERE wavelength > 0.4 AND beamline = '24_ID_C' AND $cutoff GROUP BY ROUND(wavelength, 4)";
    $sqlE = "SELECT ROUND(wavelength, 4) as wavelength, count(*) as count FROM images WHERE wavelength > 0.4 AND beamline = '24_ID_E' AND $cutoff GROUP BY ROUND(wavelength, 4)";
    $sql = "SELECT ROUND(wavelength, 4) as wavelength, count(*) as count FROM images WHERE wavelength > 0.4 AND $cutoff GROUP BY ROUND(wavelength, 4)";
    break;
  case energy:
    //    echo $_POST['query'];
    $sqlC = "SELECT TRUNCATE(12400/ROUND(wavelength, 4),0) as energy, count(*) as count FROM images WHERE wavelength > 0.4 AND beamline = '24_ID_C' AND $cutoff GROUP BY energy";
    $sqlE = "SELECT TRUNCATE(12400/ROUND(wavelength, 4),0) as energy, count(*) as count FROM images WHERE wavelength > 0.4 AND beamline = '24_ID_E' AND $cutoff GROUP BY energy";
    $sql = "SELECT TRUNCATE(12400/ROUND(wavelength, 4),0) as energy, count(*) as count FROM images WHERE wavelength > 0.4 AND $cutoff GROUP BY energy";
    break;
  case distance:
    $sqlC = "SELECT ROUND(distance/5, 0)*5 as distance, count(*) as count FROM images WHERE beamline = '24_ID_C' AND $cutoff GROUP BY ROUND(distance/5, 0)*5";
    $sqlE = "SELECT ROUND(distance/5, 0)*5 as distance, count(*) as count FROM images WHERE beamline = '24_ID_E' AND $cutoff GROUP BY ROUND(distance/5, 0)*5";
    $sql = "SELECT ROUND(distance/5, 0)*5 as distance, count(*) as count FROM images WHERE $cutoff GROUP BY ROUND(distance/5, 0)*5";
    break;
 case aperture:
    $sqlC = "SELECT md2_aperture, count(*) as count FROM images WHERE beamline = '24_ID_C' AND $cutoff GROUP BY md2_aperture";
    $sqlE = "SELECT md2_aperture, count(*) as count FROM images WHERE beamline = '24_ID_E' AND $cutoff GROUP BY md2_aperture";
    $sql = "SELECT md2_aperture, count(*) as count FROM images WHERE $cutoff GROUP BY md2_aperture";
    break;
 case transmission:
    $sqlC = "SELECT TRUNCATE(transmission, 2) as lowE, count(*) as count FROM images WHERE transmission <= 1 and beamline = '24_ID_C' AND $cutoff GROUP BY lowE UNION SELECT TRUNCATE(transmission,0) as highE, count(*) as count FROM images WHERE transmission > 1 and beamline = '24_ID_C' AND $cutoff GROUP BY highE";
    $sqlE = "SELECT TRUNCATE(transmission, 2) as lowE, count(*) as count FROM images WHERE transmission <= 1 and beamline = '24_ID_C' AND $cutoff GROUP BY lowE UNION SELECT TRUNCATE(transmission,0) as highE, count(*) as count FROM images WHERE transmission > 1 and beamline = '24_ID_E' AND $cutoff GROUP BY highE";
    $sql = "SELECT TRUNCATE(transmission, 2) as lowE, count(*) as count FROM images WHERE transmission <= 1 AND $cutoff GROUP BY lowE UNION SELECT TRUNCATE(transmission,0) as highE, count(*) as count FROM images WHERE transmission > 1 AND $cutoff GROUP BY highE";
    break;
 case osc:
    $sqlC = "SELECT osc_range, count(*) as count FROM images WHERE beamline = '24_ID_C' AND osc_range <= 90 AND $cutoff GROUP BY osc_range";
    $sqlE = "SELECT osc_range, count(*) as count FROM images WHERE beamline = '24_ID_E' AND osc_range <= 90 AND $cutoff GROUP BY osc_range";
    $sql = "SELECT osc_range, count(*) as count FROM images WHERE osc_range <= 90 AND $cutoff GROUP BY osc_range";
    break;
 case exposure:
    $sqlC = "SELECT time, count(*) as count FROM images WHERE beamline = '24_ID_C' AND time < 300 AND $cutoff GROUP BY time";
    $sqlE = "SELECT time, count(*) as count FROM images WHERE beamline = '24_ID_E' AND time < 300 AND $cutoff GROUP BY time";
    $sql = "SELECT time, count(*) as count FROM images WHERE time < 300 AND $cutoff GROUP BY time";
    break;
 case last24:
    $sqlC = "SELECT FLOOR(UNIX_TIMESTAMP(timestamp)/3600)*3600000 as last24, count(*) as count FROM images WHERE beamline = '24_ID_C' AND timestamp > DATE_SUB(NOW(),INTERVAL 1 DAY) GROUP BY last24";
    $sqlE = "SELECT FLOOR(UNIX_TIMESTAMP(timestamp)/3600)*3600000 as last24, count(*) as count FROM images WHERE beamline = '24_ID_E' AND timestamp > DATE_SUB(NOW(),INTERVAL 1 DAY) GROUP BY last24";
    $sql = "SELECT FLOOR(UNIX_TIMESTAMP(timestamp)/3600)*3600000 as last24, count(*) as count FROM images WHERE timestamp > DATE_SUB(NOW(),INTERVAL 1 DAY) GROUP BY last24";
    break;
  case datasets:
    $sqlC = "SELECT FLOOR(UNIX_TIMESTAMP(timestamp)/86400)*86400000 as dates, count(*) as count FROM runs WHERE beamline = 'C' AND $cutoff GROUP BY dates";
    $sqlE = "SELECT FLOOR(UNIX_TIMESTAMP(timestamp)/86400)*86400000 as dates, count(*) as count FROM runs WHERE beamline = 'E' AND $cutoff GROUP BY dates";
    $sql = "SELECT FLOOR(UNIX_TIMESTAMP(timestamp)/86400)*86400000 as dates, count(*) as count FROM runs WHERE $cutoff GROUP BY dates";
    break;
  case degrees:
    $sqlC = "SELECT ROUND(total*width,0) as degrees, count(*) as count FROM runs WHERE beamline = 'C' AND $cutoff GROUP BY degrees";
    $sqlE = "SELECT ROUND(total*width,0) as degrees, count(*) as count FROM runs WHERE beamline = 'E' AND $cutoff GROUP BY degrees";
    $sql = "SELECT ROUND(total*width,0) as degrees, count(*) as count FROM runs WHERE $cutoff GROUP BY degrees";
    break;
  case resolution:
    $sqlC = "SELECT ROUND(integrate_shell_results.high_res,1) as resolution, count(*) as count FROM integrate_shell_results, integrate_results, runs WHERE integrate_shell_results.shell_type='overall' AND integrate_results.integrate_status !='FAILED' AND integrate_results.shell_overall = integrate_shell_results.isr_id AND integrate_results.run_id = runs.run_id AND runs.beamline = 'C' AND runs.timestamp > '$start' AND runs.timestamp < '$finish' GROUP BY resolution";
    $sqlE = "SELECT ROUND(integrate_shell_results.high_res,1) as resolution, count(*) as count FROM integrate_shell_results, integrate_results, runs WHERE integrate_shell_results.shell_type='overall' AND integrate_results.integrate_status !='FAILED' AND integrate_results.shell_overall = integrate_shell_results.isr_id AND integrate_results.run_id = runs.run_id AND runs.beamline = 'E' AND runs.timestamp > '$start' AND runs.timestamp < '$finish' GROUP BY resolution";
    $sql = "SELECT ROUND(integrate_shell_results.high_res,1) as resolution, count(*) as count FROM integrate_shell_results, integrate_results, runs WHERE integrate_shell_results.shell_type='overall' AND integrate_results.integrate_status !='FAILED' AND integrate_results.shell_overall = integrate_shell_results.isr_id AND integrate_results.run_id = runs.run_id AND runs.timestamp > '$start' AND runs.timestamp < '$finish' GROUP BY resolution";
    break;
  case redundancy:
  	$sqlC = "SELECT ROUND(integrate_shell_results.multiplicity,1) as redundancy, count(*) as count FROM integrate_shell_results, integrate_results, runs WHERE integrate_shell_results.shell_type='overall' AND integrate_results.integrate_status !='FAILED' AND integrate_results.shell_overall = integrate_shell_results.isr_id AND integrate_results.run_id = runs.run_id AND runs.beamline = 'C' AND runs.timestamp > '$start' AND runs.timestamp < '$finish' GROUP BY redundancy";
  	$sqlE = "SELECT ROUND(integrate_shell_results.multiplicity,1) as redundancy, count(*) as count FROM integrate_shell_results, integrate_results, runs WHERE integrate_shell_results.shell_type='overall' AND integrate_results.integrate_status !='FAILED' AND integrate_results.shell_overall = integrate_shell_results.isr_id AND integrate_results.run_id = runs.run_id AND runs.beamline = 'E' AND runs.timestamp > '$start' AND runs.timestamp < '$finish' GROUP BY redundancy";
  	$sql = "SELECT ROUND(integrate_shell_results.multiplicity,1) as redundancy, count(*) as count FROM integrate_shell_results, integrate_results, runs WHERE integrate_shell_results.shell_type='overall' AND integrate_results.integrate_status !='FAILED' AND integrate_results.shell_overall = integrate_shell_results.isr_id AND integrate_results.run_id = runs.run_id AND runs.timestamp > '$start' AND runs.timestamp < '$finish' GROUP BY redundancy";
  	break;
  case completeness:
  	$sqlC = "SELECT ROUND(integrate_shell_results.completeness,1) as complete, count(*) as count FROM integrate_shell_results, integrate_results, runs WHERE integrate_shell_results.shell_type='overall' AND integrate_results.integrate_status !='FAILED' AND integrate_results.shell_overall = integrate_shell_results.isr_id AND integrate_results.run_id = runs.run_id AND runs.beamline = 'C' AND runs.timestamp > '$start' AND runs.timestamp < '$finish' GROUP BY complete";
  	$sqlE = "SELECT ROUND(integrate_shell_results.completeness,1) as complete, count(*) as count FROM integrate_shell_results, integrate_results, runs WHERE integrate_shell_results.shell_type='overall' AND integrate_results.integrate_status !='FAILED' AND integrate_results.shell_overall = integrate_shell_results.isr_id AND integrate_results.run_id = runs.run_id AND runs.beamline = 'E' AND runs.timestamp > '$start' AND runs.timestamp < '$finish' GROUP BY complete";
  	$sql = "SELECT ROUND(integrate_shell_results.completeness,1) as complete, count(*) as count FROM integrate_shell_results, integrate_results, runs WHERE integrate_shell_results.shell_type='overall' AND integrate_results.integrate_status !='FAILED' AND integrate_results.shell_overall = integrate_shell_results.isr_id AND integrate_results.run_id = runs.run_id AND runs.timestamp > '$start' AND runs.timestamp < '$finish' GROUP BY complete";
  	break;
  case r_merge:
  	$sqlC = "SELECT ROUND(integrate_shell_results.r_merge,2) as Rmerge, count(*) as count FROM integrate_shell_results, integrate_results, runs WHERE integrate_shell_results.shell_type='overall' AND integrate_results.integrate_status !='FAILED' AND integrate_results.shell_overall = integrate_shell_results.isr_id AND integrate_results.run_id = runs.run_id AND r_merge > 0 AND runs.beamline = 'C' AND runs.timestamp > '$start' AND runs.timestamp < '$finish' GROUP BY Rmerge";
  	$sqlE = "SELECT ROUND(integrate_shell_results.r_merge,2) as Rmerge, count(*) as count FROM integrate_shell_results, integrate_results, runs WHERE integrate_shell_results.shell_type='overall' AND integrate_results.integrate_status !='FAILED' AND integrate_results.shell_overall = integrate_shell_results.isr_id AND integrate_results.run_id = runs.run_id AND r_merge > 0 AND runs.beamline = 'E' AND runs.timestamp > '$start' AND runs.timestamp < '$finish' GROUP BY Rmerge";
  	$sql = "SELECT ROUND(integrate_shell_results.r_merge,2) as Rmerge, count(*) as count FROM integrate_shell_results, integrate_results, runs WHERE integrate_shell_results.shell_type='overall' AND integrate_results.integrate_status !='FAILED' AND integrate_results.shell_overall = integrate_shell_results.isr_id AND integrate_results.run_id = runs.run_id AND r_merge > 0 AND runs.timestamp > '$start' AND runs.timestamp < '$finish' GROUP BY Rmerge";
  	break;
  case r_pim:
  	$sqlC = "SELECT ROUND(integrate_shell_results.r_pim,2) as Rpim, count(*) as count FROM integrate_shell_results, integrate_results, runs WHERE integrate_shell_results.shell_type='overall' AND integrate_results.integrate_status !='FAILED' AND integrate_results.shell_overall = integrate_shell_results.isr_id AND integrate_results.run_id = runs.run_id AND r_pim > 0 AND runs.beamline = 'C' AND runs.timestamp > '$start' AND runs.timestamp < '$finish'GROUP BY Rpim";
  	$sqlE = "SELECT ROUND(integrate_shell_results.r_pim,2) as Rpim, count(*) as count FROM integrate_shell_results, integrate_results, runs WHERE integrate_shell_results.shell_type='overall' AND integrate_results.integrate_status !='FAILED' AND integrate_results.shell_overall = integrate_shell_results.isr_id AND integrate_results.run_id = runs.run_id AND r_pim > 0 AND runs.beamline = 'E' AND runs.timestamp > '$start' AND runs.timestamp < '$finish' GROUP BY Rpim";
  	$sql = "SELECT ROUND(integrate_shell_results.r_pim,2) as Rpim, count(*) as count FROM integrate_shell_results, integrate_results, runs WHERE integrate_shell_results.shell_type='overall' AND integrate_results.integrate_status !='FAILED' AND integrate_results.shell_overall = integrate_shell_results.isr_id AND integrate_results.run_id = runs.run_id AND r_pim > 0 AND runs.timestamp > '$start' AND runs.timestamp < '$finish' GROUP BY Rpim";
  	break;
  case samples:
    $sqlC = "SELECT FLOOR(UNIX_TIMESTAMP(t1.timestamp)/86400)*86400000 as dates , count(*) as count FROM images as t1, images as t2 WHERE t1.image_id+1 = t2.image_id AND t1.sample != t2.sample AND t2.sample != 0 AND t1.beamline = t2.beamline AND t1.beamline='24_ID_C' AND t1.timestamp > '$start' AND t1.timestamp < '$finish'GROUP BY dates";
    $sqlE = "SELECT FLOOR(UNIX_TIMESTAMP(t1.timestamp)/86400)*86400000 as dates, count(*) as count FROM images as t1, images as t2 WHERE t1.image_id+1 = t2.image_id AND t1.sample != t2.sample AND t2.sample != 0 AND t1.beamline = t2.beamline AND t1.beamline='24_ID_E' AND t1.timestamp > '$start' AND t1.timestamp < '$finish'GROUP BY dates";
    $sql = "SELECT FLOOR(UNIX_TIMESTAMP(t1.timestamp)/86400)*86400000 as dates, count(*) as count FROM images as t1, images as t2 WHERE t1.image_id+1 = t2.image_id AND t1.sample != t2.sample AND t2.sample != 0 AND t1.beamline = t2.beamline AND t1.timestamp > '$start' AND t1.timestamp < '$finish' GROUP BY dates";
    break;
  case avgmount:
    $sqlC = "SELECT ROUND((UNIX_TIMESTAMP(t2.date)-UNIX_TIMESTAMP(t1.date))/60,1) as diff, count(*) as count FROM images as t1, images as t2 WHERE t1.image_id+1 = t2.image_id AND t1.sample != t2.sample AND t2.sample != 0 AND t1.beamline = t2.beamline AND t1.run_id IS NULL AND t2.run_id IS NULL AND (UNIX_TIMESTAMP(t2.date)-UNIX_TIMESTAMP(t1.date)) < 3600 AND (UNIX_TIMESTAMP(t2.date)-UNIX_TIMESTAMP(t1.date)) > 0 AND t1.beamline='24_ID_C' AND t1.timestamp > '$start' AND t1.timestamp < '$finish'GROUP BY diff";
    $sqlE = "SELECT ROUND((UNIX_TIMESTAMP(t2.date)-UNIX_TIMESTAMP(t1.date))/60,1) as diff, count(*) as count FROM images as t1, images as t2 WHERE t1.image_id+1 = t2.image_id AND t1.sample != t2.sample AND t2.sample != 0 AND t1.beamline = t2.beamline AND t1.run_id IS NULL AND t2.run_id IS NULL AND (UNIX_TIMESTAMP(t2.date)-UNIX_TIMESTAMP(t1.date)) < 3600 AND (UNIX_TIMESTAMP(t2.date)-UNIX_TIMESTAMP(t1.date)) > 0 AND t1.beamline='24_ID_E' AND t1.timestamp > '$start' AND t1.timestamp < '$finish'GROUP BY diff";
    $sql = "SELECT ROUND((UNIX_TIMESTAMP(t2.date)-UNIX_TIMESTAMP(t1.date))/60,1) as diff, count(*) as count FROM images as t1, images as t2 WHERE t1.image_id+1 = t2.image_id AND t1.sample != t2.sample AND t2.sample != 0 AND t1.beamline = t2.beamline AND t1.run_id IS NULL AND t2.run_id IS NULL AND (UNIX_TIMESTAMP(t2.date)-UNIX_TIMESTAMP(t1.date)) < 3600 AND (UNIX_TIMESTAMP(t2.date)-UNIX_TIMESTAMP(t1.date)) > 0 AND t1.timestamp > '$start' AND t1.timestamp < '$finish' GROUP BY diff";
    break;


  default:

  };
$resultC = @mysql_query($sqlC);
$resultE = @mysql_query($sqlE);
$result = @mysql_query($sql);
echo '[{ label: "Total", color: 0, data:[';
//create array of pairs of x and y values

//  $arr = array();

while($row = mysql_fetch_array($result))
  {
     //print_r($row);
   echo "[".$row['0'].",".$row['1']."],";

  }

if (($_POST['query']) == 'wavelength' or ($_POST['query']) == 'energy')
  {
  mysql_data_seek($result, 0);
  $wavestart = mysql_fetch_row($result);
  echo ']},{ label: "Metal", color: 3, data: [['.$wavestart['0'].',0],[ ';
  mysql_data_seek($result, mysql_num_rows($result)-1);
  $waveend = mysql_fetch_row($result);
  echo $waveend['0'].',0]], xaxis: 2},{ label: "C", color: 1, data:[';
  }
else
  echo ']},{ label: "C", color: 1, data:[';

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
