<?php
  //session_start();

  $result_id    = $_POST[result_id];
  $start_repr   = $_POST[start_repr];

  //Determine if this is a pair of a single image
  //type == 0 for single, 1 for pair
  $pattern = '/\+/';
  $type = 0;
  $start_repr = preg_replace($pattern,'+',$start_repr,-1,$type);
  require('./login/config.php');
  require('./login/functions.php');

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());

  //retrive the type, id and setting_id for the given result_id
  if ($type == 0)
  {
    $sql1    = "SELECT images.* FROM results,single_results,images WHERE results.type='single' AND results.result_id=$result_id AND results.id=single_results.single_result_id and single_results.image_id=images.image_id";
    $result1 = @mysql_query($sql1,$connection) or die(mysql_error());
    $return1 = mysql_fetch_object($result1);
    //Assign variables
    $fullname           = $return1 -> fullname;
    $name               = basename($fullname);
    $date               = $return1 -> date;
    $puck               = $return1 -> puck;
    $sample             = $return1 -> sample;
    $sample_id          = $return1 -> sample_id;
    $osc_start          = $return1 -> osc_start;
    $osc_range          = $return1 -> osc_range;
    $time               = $return1 -> time;
    $transmission       = $return1 -> transmission;
    $wavelength         = $return1 -> wavelength;
    $md2_aperture       = $return1 -> md2_aperture;
    $distance           = $return1 -> distance;
    $beam_center_x      = $return1 -> beam_center_x;
    $beam_center_y      = $return1 -> beam_center_y;
    $calc_beam_center_x = $return1 -> calc_beam_center_x;
    $calc_beam_center_y = $return1 -> calc_beam_center_y;
    $binning            = $return1 -> binning;
    $ring_current       = $return1 -> ring_current;
    $ring_mode          = $return1 -> ring_mode;
  }
  else
  {
    $sql1    = "SELECT images.* FROM results,pair_results,images WHERE results.type='pair' AND results.result_id=$result_id AND results.id=pair_results.pair_result_id and pair_results.image1_id=images.image_id";
    $result1 = @mysql_query($sql1,$connection) or die(mysql_error());
    $return1 = mysql_fetch_object($result1);

    //Assign variables
    $fullname      = $return1 -> fullname;
    $name          = basename($fullname);
    $date          = $return1 -> date;
    $puck          = $return1 -> puck;
    $sample        = $return1 -> sample;
    $sample_id     = $return1 -> sample_id;
    $osc_start     = $return1 -> osc_start;
    $osc_range     = $return1 -> osc_range;
    $time          = $return1 -> time;
    $transmission  = $return1 -> transmission;
    $wavelength    = $return1 -> wavelength;
    $md2_aperture  = $return1 -> md2_aperture;
    $distance      = $return1 -> distance;
    $beam_center_x = $return1 -> beam_center_x;
    $beam_center_y = $return1 -> beam_center_y;
    $calc_beam_center_x = $return1 -> calc_beam_center_x;
    $calc_beam_center_y = $return1 -> calc_beam_center_y;
    $binning       = $return1 -> binning;
    $ring_current  = $return1 -> ring_current;
    $ring_mode     = $return1 -> ring_mode;

    $sql2    = "SELECT images.* FROM results,pair_results,images WHERE results.type='pair' AND results.result_id=$result_id AND results.id=pair_results.pair_result_id and pair_results.image2_id=images.image_id";
    $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
    $return2 = mysql_fetch_object($result2);

    //Assign variables
    $fullname2      = $return2 -> fullname;
    $name2          = basename($fullname2);
    $date2          = $return2 -> date;
    $puck2          = $return2 -> puck;
    $sample2        = $return2 -> sample;
    $sample_id2     = $return2 -> sample_id;
    $osc_start2     = $return2 -> osc_start;
    $osc_range2     = $return2 -> osc_range;
    $time2          = $return2 -> time;
    $transmission2  = $return2 -> transmission;
    $wavelength2    = $return2 -> wavelength;
    $md2_aperture2  = $return2 -> md2_aperture;
    $distance2      = $return2 -> distance;
    $beam_center_x2 = $return2 -> beam_center_x;
    $beam_center_y2 = $return2 -> beam_center_y;
    $calc_beam_center_x2 = $return1 -> calc_beam_center_x;
    $calc_beam_center_y2 = $return1 -> calc_beam_center_y;
    $binning2       = $return2 -> binning;
    $ring_current2  = $return2 -> ring_current;
    $ring_mode2     = $return2 -> ring_mode;
  }
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
      <div id='settings_table'>
        <table>
<?
  if ($type == 1)
  {
?>
          <tr>
            <td align='right' width='150' style="font-size:1em;">
              Image
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo($name);?>
            </td>
            <td style='font-size:1em; padding:5px; color:green;'>
              <?echo($name2);?>
            </td>
          </tr>
<?
  }
?>
          <tr>
            <td align='right' style="font-size:1em;"> 
              Date     
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo($date);?>
            </td>
            <? if ($type == 1)
               {
                  echo("<td style='font-size:1em; padding:5px; color:green;'>$date2</td>");
               }
            ?>
          </tr>
<?
  if ($sample != 0)
  {
?>
          <tr>
            <td align='right' style="font-size:1em;">
              Puck position
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo("$puck$sample");?>
            </td>
            <? if ($type == 1)
               {
                  echo("<td style='font-size:1em; padding:5px; color:green;'>$puck2$sample2</td>");
               }
            ?>
          </tr>
<?
  }
?>
          <tr>
            <td align='right' style="font-size:1em;">
              Oscillation start
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo(number_format($osc_start,1)."&deg;");?>
            </td>
            <? if ($type == 1)
               {
                  echo("<td style='font-size:1em; padding:5px; color:green;'>".number_format($osc_start2,1)."&deg;</td>");
               }
            ?>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              Oscillation range
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo(number_format($osc_range,1)."&deg;");?>
            </td>
            <? if ($type == 1)
               {
                  echo("<td style='font-size:1em; padding:5px; color:green;'>".number_format($osc_range2,1)."&deg;</td>");
               }
            ?>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              Exposure time
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo(number_format($time,1)." s");?>
            </td>
            <? if ($type == 1)
               {
                  echo("<td style='font-size:1em; padding:5px; color:green;'>".number_format($time2,1)." s</td>");
               }
            ?>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              Transmission
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo(number_format($transmission,2)."%");?>
            </td>
            <? if ($type == 1)
               {
                  echo("<td style='font-size:1em; padding:5px; color:green;'>".number_format($transmission2,2)."%</td>");
               }
            ?>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              Wavelength
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo(number_format($wavelength,2)." &Aring;");?>
            </td>
            <? if ($type == 1)
               {
                  echo("<td style='font-size:1em; padding:5px; color:green;'>".number_format($wavelength2,2)." &Aring;</td>");
               }
            ?>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              MD2 Aperture
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo("$md2_aperture &micro;m");?>
            </td>
            <? if ($type == 1)
               {
                  echo("<td style='font-size:1em; padding:5px; color:green;'>$md2_aperture &micro;m</td>");
               }
            ?>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              Distance
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo(number_format($distance,1)." mm");?>
            </td>
            <? if ($type == 1)
               {
                  echo("<td style='font-size:1em; padding:5px; color:green;'>".number_format($distance2,1)." mm</td>");
               }
            ?>
          </tr>
          <? if (! is_null($calc_beam_center_x))
             {
                 echo("<tr>");
                 echo("  <td align='right' style='font-size:1em;'>Beam Center X</td>");
                 echo("  <td style='font-size:1em; padding:5px; color:green;'>".number_format($calc_beam_center_x,2)." mm</td>");
                 if ($type == 1)
                 {
                     echo("<td style='font-size:1em; padding:5px; color:green;'>".number_format($calc_beam_center_x2,2)." mm</td>");
		 }
                 echo("</tr>");
                 echo("<tr>");
                 echo("  <td align='right' style='font-size:1em;'>Y</td>");
                 echo("  <td style='font-size:1em; padding:5px; color:green;'>".number_format($calc_beam_center_y,2)." mm</td>");
                 if ($type == 1)
                 {
                     echo("<td style='font-size:1em; padding:5px; color:green;'>".number_format($calc_beam_center_y2,2)." mm</td>");
                 }      
                 echo("</tr>");
             }
          ?>   
          <tr>
            <td align='right' style="font-size:1em;">
              Binning 
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo($binning);?>
            </td>
            <? if ($type == 1)
               {
                  echo("<td style='font-size:1em; padding:5px; color:green;'>$binning2</td>");
               }
            ?>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              Ring Current
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo(number_format($ring_current,1)." mA");?>
            </td>
            <? if ($type == 1)
               {
                  echo("<td style='font-size:1em; padding:5px; color:green;'>$ring_current2</td>");
               }
            ?>
          </tr>
          <tr>
            <td align='right' style="font-size:1em;">
              Ring Mode
            </td>
            <td style="font-size:1em; padding:5px; color:green;">
              <?echo($ring_mode);?>
            </td><? if ($type == 1)
               {
                  echo("<td style='font-size:1em; padding:5px; color:green;'>$ring_mode2</td>");
               }
            ?>
          </tr>



        </table>
      </div>
    </div>
  </body>
</html>
