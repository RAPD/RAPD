<?php
  //session_start();

  $datadir = $_GET[datadir];
//  $datadir = "/gpfs4/users/necat/Test_Nov1809";
  $beamline  = $_GET[beamline];
//  $beamline = 'E';
  $form_type = "current";

  require('./login/config.php');
  require('./login/functions.php');
  require('./custom.php');

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());
  //look at current table for this data_root_dir
  $sql = "SELECT setting_id FROM current WHERE data_root_dir='$datadir'";
  $result = @mysql_query($sql,$connection) or die(mysql_error());
  $num = mysql_num_rows($result); 
  if ($num == 0)
  {
    //echo("<p>Not Current</p>");
    //no row means we are not working on an active data_root_directory
    //see if there is an entry in presets table for this drd
    $form_type = 'preset';
    $sql2 = "SELECT setting_id FROM presets WHERE data_root_dir='$datadir'";
    $result2 = @mysql_query($sql2,$connection) or die(mysql_error());
    $num2 = mysql_num_rows($result2); 
    if ($num2 == 0) 
    {
      //echo("<p>Naive</p>");
      //$form_type = 'naive';
      //get the setting_id from the DEFAULTS presets entry
      $sql3 = "SELECT setting_id FROM presets WHERE data_root_dir='DEFAULTS' AND beamline='$beamline'";
      $result2 = @mysql_query($sql3,$connection) or die(mysql_error());
    } else {
      //echo("<p>Preset</p>");
    }
    //my_return will come from either presets for the drd OR DEFAULTS entry for the beamline 
    $my_return = mysql_fetch_object($result2);
    $setting_id =  $my_return->setting_id; 
    
 
  } else { 
    //the data_root_directory is active, pull info from current->settings_id
    $return = mysql_fetch_object($result);
    $setting_id = $return -> setting_id;
  }

  //query for the settings of the retrieved data
  $sql = "SELECT * FROM settings WHERE setting_id='$setting_id'";
  $result = @mysql_query($sql,$connection) or die(mysql_error());
  $return = mysql_fetch_object($result);

  //now grab the data to fill the form
  $multiprocessing   = $return -> multiprocessing;
  $spacegroup        = $return -> spacegroup;
  $sample_type       = $return -> sample_type;
  $solvent_content   = $return -> solvent_content;
  $susceptibility    = $return -> susceptibility;
  $crystal_size_x    = $return -> crystal_size_x;
  $crystal_size_y    = $return -> crystal_size_y;
  $crystal_size_z    = $return -> crystal_size_z;
  $a                 = $return -> a;
  $b_cell            = $return -> b;
  $c                 = $return -> c;
  $alpha             = $return -> alpha;
  $beta              = $return -> beta;
  $gamma             = $return -> gamma;
  $work_dir_override = $return -> work_dir_override;
  $work_directory    = $return -> work_directory;
  $beam_flip         = $return -> beam_flip;
  $x_beam            = $return -> x_beam;
  $y_beam            = $return -> y_beam;
  $index_hi_res      = $return -> index_hi_res;
  $strategy_type     = $return -> strategy_type;
  $best_complexity   = $return -> best_complexity;
  $mosflm_seg        = $return -> mosflm_seg;
  $mosflm_rot        = $return -> mosflm_rot;
  $aimed_res         = $return -> aimed_res;
  $min_exposure_per  = $return -> min_exposure_per;
  $integrate         = $return -> integrate;

?>

<html>
  <head>
    <style type="text/css">
      h3 {
        color: green;
        font-size: 1em;
        margin-bottom: 0.25em;
      }
    </style>
    <script type="text/javascript">
      jQuery(function($){
        $('#myForm').submit(function(){ 
          $.post($(this).attr('action'), $(this).serialize(), function(html) { 
            $('#content').html(html)
          })
          return false
        })
      })
    </script>


  </head>

  <body>
  <div id="content">
  <form id='myForm' action='./d_add_settings.php' method='POST'>
  <!-- HIDDEN VARIABLES POSTED -->
  <input type="hidden" name="form_type"         value="<? echo($form_type);?>"> 
  <input type="hidden" name="data_dir"          value="<? echo($datadir);?>">
  <input type="hidden" name="beamline"          value="<? echo($beamline);?>">
  <input type="hidden" name="work_dir_override" value="<? echo($work_dir_override);?>">
  <input type="hidden" name="work_directory"    value="<? echo($work_directory);?>">

  <table>
    <tr>
      <td align='center' width='350'>
<?
  if ($form_type == 'naive')
  {
    echo("        <h3>Directory NOT Active - Creating Presets</h3>\n");
  } elseif ($form_type == 'preset') {
    echo("        <h3>Directory NOT Active - Creating Presets</h3>\n");
  } elseif ($form_type == 'current') {
    echo("        <h3>Directory Active - Changing Current Settings</h3>\n");
  }
?>
        <h3>Computing Settings</h3>
      </td>
    </tr>
  </table>
  <table>
    <tr>
      <td align="right" width="175">
        Multiprocessing 
      </td>
      <td width="75">
        <select name="multiprocessing">
<?
  if ($multiprocessing == 'True') {
      echo("          <option value='True' selected='True'>True</option>\n");
      echo("          <option value='False'>False</option>\n");
    } else {
      echo("          <option value='True'>True</option>\n");
      echo("          <option value='False' selected='False'>False</option>\n");
    }
?>
        </select>
      </td>
    </tr>
  </table>



  <table>
    <tr>
      <td align='center' width='350'>
        <h3>Project Settings</h3>
      </td>
    </tr>
  </table>
  <table>
    <tr>
      <td align="right" width="175">
        Spacegroup Overide 
      </td>
      <td width="100">
        <select name="spacegroup">
<?php
  if ($spacegroup == "None") {
    echo("          <option value='None' selected='selected'>None</option>\n");
  } else { 
    echo("          <option value='None'>None</option>\n");
  }
  foreach ($bravais as $b) {
    if ($spacegroup == $intl2std[$b]) {
      echo("          <option value='$intl2std[$b]' selected='$intl2std[$b]'>$intl2std[$b]</option>\n");
    } else {
      echo("          <option value='$intl2std[$b]'>$intl2std[$b]</option>\n");
    }
    foreach ($subgroups[$b] as $s) {
      if ($spacegroup == $intl2std[$s]) {
        echo("          <option value='$intl2std[$s]' selected='$intl2std[$s]'>$intl2std[$s]</option>\n");
      } else {
        echo("          <option value='$intl2std[$s]'>$intl2std[$s]</option>\n");
      }
    }
  }

?>
        </select>
      </td>
    </tr>
  </table>
  <table>
    <tr>
      <td align="right" width="175">
        Sample Type
      </td>
      <td>
        <select name="sample_type">
<?
  foreach ($types as $t) {
    if ($sample_type == $t) {
      echo("          <option value='$t' selected='$t'>$t</option>\n");
    } else {
      echo("          <option value='$t'>$t</option>\n");
    }
  }
?>
        </select>
      </td>
    </tr>
    <tr>
      <td align="right" width="175">
        Solvent Fraction (0.00-1.00)
      </td>
      <td>
        <input type="text" name="solvent_content" value="<?echo($solvent_content);?>" size=5> 
      </td>
    </tr>
    <tr>
      <td align="right" width="175">
        Radiation Susceptibility
      </td>
      <td>
        <input type="text" name="susceptibility" value="<?echo($susceptibility);?>" size=5> 
      </td>
    </tr>
  </table>
  <table>
    <tr>
      <td align="right" width="175">
        Crystal Size (um) X
      </td>
      <td>
        <input type="text" name="crystal_size_x" value="<?echo($crystal_size_x);?>" size=5>
      </td>
      <td>Y</td>
      <td>
        <input type="text" name="crystal_size_y" value="<?echo($crystal_size_y);?>" size=5>
      </td>
      <td>Z</td>
      <td>
        <input type="text" name="crystal_size_z" value="<?echo($crystal_size_z);?>" size=5>
      </td>
    </tr>
  </table>


  <table>
    <tr>
      <td align="right" width="175">
        Cell Parameters a
      </td>
      <td>
        <input type="text" name="a" value="<?echo($a);?>" size=5>
      </td>
      <td>b</td>
      <td>
        <input type="text" name="b" value="<?echo($b_cell);?>" size=5>
      </td>
      <td>c</td>
      <td>
        <input type="text" name="c" value="<?echo($c);?>" size=5>
      </td>
    </tr>
    <tr>
      <td align="right" width="175">
        &alpha 
      </td>
      <td>
        <input type="text" name="alpha" value="<?echo($alpha);?>" size=5>
      </td>
      <td>&beta</td>
      <td>
        <input type="text" name="beta" value="<?echo($beta);?>" size=5>
      </td>
      <td>&gamma</td>
      <td>
        <input type="text" name="gamma" value="<?echo($gamma);?>" size=5>
      </td>
    </tr>
  </table>

  <table>
    <tr>
      <td align="right" width="175">
        Flip Beam Coordinates
      </td>
      <td width="75">
        <select name="beam_flip">
<?
  if ($beam_flip == 'True') {
      echo("          <option value='True' selected='True'>True</option>\n");
      echo("          <option value='False'>False</option>\n");
    } else {
      echo("          <option value='True'>True</option>\n");
      echo("          <option value='False' selected='False'>False</option>\n");
    }
?>
        </select>
      </td>
    </tr>
  </table>
  <table>
    <tr>
      <td align="right" width="175">
        Override Beam X
      </td>
      <td>
        <input type="text" name="x_beam" value="<? echo $x_beam; ?>" size=5>
      </td>
      <td width=5>
        Y
      </td>
      <td>
        <input type="text" name="y_beam" value="<? echo $y_beam; ?>" size=5>
      </td>
    </tr>
  </table>


  <table>
    <tr>
      <td align='center' width='350'>
        <h3>Autoindexing Settings</h3>
      </td>
    </tr>
  </table>
  <table>
    <tr>
      <td align="right" width="175">
        Hi Res Cutoff - Peak Picking
      </td>
      <td>
        <input type="text" name="index_hi_res" value="<? echo $index_hi_res; ?>" size=5> 
      </td>
    </tr>
    <tr>
      <td align="right" width="175">
        Strategy type
      </td>
      <td width="75">
        <select name="strategy_type">
<?
  if ($strategy_type == 'mosflm') {
      echo("          <option value='best'>Best</option>\n");
      echo("          <option value='mosflm' selected='mosflm'>Mosflm</option>\n");
  } else {
      echo("          <option value='best' selected='best'>Best</option>\n");
      echo("          <option value='mosflm'>Mosflm</option>\n");
    }
?>
        </select>
      </td>
    </tr>
    <tr>
      <td align="right" width="175">
        Best Complexity
      </td>
      <td width="75">
        <select name="best_complexity">
<?
  foreach ($best_set as $b) {
    if ($best_complexity == $b) {
      echo("          <option value='$b' selected='$b'>$b</option>\n");
    } else {
      echo("          <option value='$b'>$b</option>\n");
    }
  }
?>
        </select>
      </td>
    </tr>
  </table>
  <table> 
    <tr>
      <td align="right" width="175">
        Mosflm Segments
      </td>
      <td width="75">
        <select name="mosflm_seg">
<?
  foreach ($seg_set as $s) {
    if ($mosflm_seg == $s) {
      echo("          <option value='$s' selected='$s'>$s</option>\n");
    } else {
      echo("          <option value='$s'>$s</option>\n");
    }
  }
?>
        </select>
      </td>
      <td>&nbsp;Rotation Range</td>
      <td>
        <input type="text" name="mosflm_rot" value="<?echo($mosflm_rot);?>" size=5>
      </td>
  </table>
  <table>
    <tr>
      <td align="right" width="175">
        Aimed Resolution 
      </td>
      <td>
        <input type="text" name="aimed_res" value="<? echo $aimed_res; ?>" size=5>
      </td>
    </tr>
  </table>
  <table>
    <tr>
      <td align="right" width="175">
        Min Exposure per Image
      </td>
      <td>
        <input type="text" name="min_exposure_per" value="<? echo $min_exposure_per; ?>" size=5> 
      </td>
    </tr>
    <tr>
      <td align="right" width="175">
        Integrate              
      </td>
      <td width="75">
        <select name="integrate">
<?
  if ($integrate == 'True') {
      echo("          <option value='True' selected='True'>True</option>\n");
      echo("          <option value='False'>False</option>\n");
    } else {
      echo("          <option value='True'>True</option>\n");
      echo("          <option value='False' selected='False'>False</option>\n");
    }
?>
        </select>
      </td>
    </tr>

  </table>

  <table align="center">
    <tr>
      <td width="175">&nbsp</td>
      <td>
        <input type="submit" value="OK">
      </td>
    </tr>
  </table>


</form>
</div>
</body>
</html>
