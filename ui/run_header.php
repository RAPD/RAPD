<?php
  //session_start();

  $result_id    = $_GET[result_id];
  $start_repr   = $_GET[start_repr];
  //$result_id    = 33244;
  //$start_repr   = 'thaumatin2_1_1-360';

  require('./login/config.php');
  require('./login/functions.php');

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());

  //retrive the type, id and setting_id for the given result_id
  $sql1    = "SELECT images.* FROM results,integrate_results,images WHERE results.result_id=$result_id AND results.id=integrate_results.integrate_result_id AND integrate_results.run_id=images.run_id ORDER BY images.image_number LIMIT 1";
  $result1 = @mysql_query($sql1,$connection) or die(mysql_error());
  $return1 = mysql_fetch_object($result1);

  //Assign variables
  $fullname      = $return1 -> fullname;
  $name          = basename($fullname);
  $date          = $return1 -> date;
  $puck          = $return1 -> puck;
  $sample        = $return1 -> sample;
  $osc_start     = $return1 -> osc_start;
  $osc_range     = $return1 -> osc_range;
  $time          = $return1 -> time;
  $transmission  = $return1 -> transmission;
  $wavelength    = $return1 -> wavelength;
  $md2_aperture  = $return1 -> md2_aperture;
  $distance      = $return1 -> distance;
  $beam_center_x = $return1 -> calc_beam_center_x;
  $beam_center_y = $return1 -> calc_beam_center_y;
  $binning       = $return1 -> binning;
  $ring_current  = $return1 -> ring_current;
  $ring_mode     = $return1 -> ring_mode;

?>

<html>
  <head>
    <style type="text/css">
      h3 {
        color: green;
        font-size:1.5em;
        margin-bottom: 0.25em;
      }
    </style>
  </head>

  <body>
    <div id="content">
      <table>
        <tr>
          <td align='center' width='550'>
            <h3>Header Information for <?echo($start_repr);?></h3>
          </td>
        </tr>
      </table>
      <div id='settings_table'>
        <table>
          <tr>
            <td align='right' width='200' style="font-size:1em;">
              Image
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo($name);?>
            </td>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;"> 
              Date     
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo($date);?>
            </td>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              Puck position
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo("$puck$sample");?>
            </td>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              Oscillation start
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo(number_format($osc_start,1)."&deg;");?>
            </td>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              Oscillation range
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo(number_format($osc_range,1)."&deg;");?>
            </td>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              Exposure time
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo(number_format($time,1)." s");?>
            </td>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              Transmission
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo(number_format($transmission,2)."%");?>
            </td>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              Wavelength
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo(number_format($wavelength,2)." &Aring;");?>
            </td>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              MD2 Aperture
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo("$md2_aperture &micro;m");?>
            </td>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              Distance
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo(number_format($distance,1)." mm");?>
            </td>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              Beam Center X
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo(number_format($beam_center_x,2)." mm");?>
            </td>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              Y           
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo(number_format($beam_center_y,2)." mm");?>
            </td>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              Binning 
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo($binning);?>
            </td>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              Ring Current
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo(number_format($ring_current,1)." mA");?>
            </td>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              Ring Mode
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo($ring_mode);?>
          </tr>
        </table>
      </div>
    </div>
  </body>
</html>
