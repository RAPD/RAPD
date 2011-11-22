<?php 
  require('./login/config.php');
  require('./login/functions.php');

  $res_id  = $_GET[res_id];
  $datadir = $_GET[datadir];
  $trip_id = $_GET[trip_id];
  //$datadir = "/gpfs5/users/columbia/Zhou_Feb11";
  //$res_id =  93617;
  //$trip_id = 688;

  //echo("datadir: $datadir  result id: $res_id\n");

  //create output array and store result id as 1st value
  $arr = array();
  $arr[] = $res_id;

  //
  // 1st - retreive the username from the database
  //
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db         = @mysql_select_db('rapd_users',$connection)or die(mysql_error());
  $sql        = "SELECT username FROM trips WHERE trip_id=$trip_id";
  $result     = @mysql_query($sql,$connection) or die(mysql_error());
  $sql        = mysql_fetch_object($result);
  $user       = $sql -> username;

  //
  // 2nd - grab the type of result and the respective id number
  //
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db('rapd_data',$connection)or die(mysql_error());
  $sql ="SELECT type,id,timestamp FROM results WHERE result_id=$res_id";
  $result = @mysql_query($sql,$connection) or die(mysql_error());
  $sql = mysql_fetch_object($result);
  $type   = $sql->type;
  $id     = $sql->id;

  //
  // 3rd - grab the image name(s) for labeling
  //
  if ($type == 'single')
  {
    $sql         = "SELECT repr,fullname,summary_stac,image_big,image_raw,image_preds,timestamp FROM single_results WHERE single_result_id=$id";
    $result      = @mysql_query($sql,$connection) or die(mysql_error());
    $sql         = mysql_fetch_object($result);
    $repr        = $sql -> repr;
    $fullname1   = $sql -> fullname;
    $sum_stac    = $sql -> summary_stac;
    $image_big   = $sql -> image_big;
    $image_raw   = $sql -> image_raw;
    $image_preds = $sql -> image_preds;

    //Put data into common variables
    $short = './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id.'_short.php';
    if (! (is_null($sum_stac) or ($sum_stac == 'None')))
    {
        $stac = './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id.'_stac.php';
    }
    else
    {
        $stac = 'None';
    }
    $long = './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id."_long.php";
    $images = array();
    if (is_null($image_raw))
    {
      $images[] = 'OLD';
      $images[] = '<html><body><h3 class="green">'.$fullname1.'</h3><a href="./users/'.$user.'/'.(string)$trip_id.'/single/'.(string)$id.'_big.jpg" class="jqzoom" title="Zoom" target="_blank"><IMG src="./users/'.$user.'/'.(string)$trip_id.'/single/'.(string)$id.'_small.jpg" style="border: 0px solid #666;"></a></body></html>';
    } else {
      $images[] = 'NEW';
      if ($image_preds == '0')
      {
        $images[] = 1;
      } else {
        $images[] = 2;
      }
      $images[]  = array($repr);
      $images[]  = '/var/www/html/rapd/users/'.$user.'/'.(string)$trip_id.'/single/'.(string)$id;
      $images[]  = $image_preds;
    }
    $plots =  './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id."_plots.php";
    $version = 0;
    $status = 'None';
    $timestamp = $sql -> timestamp;
    $repr = $sql -> repr;
  }
  elseif ($type == 'pair')
  {
    // Get information from the pair_results table
    $sql = "SELECT repr,fullname_1,fullname_2,summary_stac,image_big_1,image1_id,image2_id,image_raw_1,image_raw_2,image_preds_1,image_preds_2,timestamp FROM pair_results WHERE pair_result_id=$id";
    $result = @mysql_query($sql,$connection) or die(mysql_error());
    $sql = mysql_fetch_object($result);
    $fullname1     = $sql -> fullname_1;
    $fullname2     = $sql -> fullname_2;
    $image1_id     = $sql -> image1_id;
    $image2_id     = $sql -> image2_id;
    $sum_stac      = $sql -> summary_stac;
    $image_raw_1   = $sql -> image_raw_1;
    $image_preds_1 = $sql -> image_preds_1;
    $repr1         = basename($fullname1);
    $repr2         = basename($fullname2); 

    //Put data into common variables
    $short = './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id.'_short.php';
    $long = './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id."_long.php";
    if (! (is_null($sum_stac) or ($sum_stac == 'None')))
    {
      $stac = './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id.'_stac.php';
    }
    else
    {
      $stac = 'None';
    }
    $images = array();
    if (is_null($image_raw_1))
    {
        $images[] = 'OLD';
        $images[] = '<html><h3 class="green">'.$fullname1.'</h3><div><a href="./users/'.$user.'/'.(string)$trip_id.'/pair/'.(string)$id.'_big1.jpg" class="jqzoom" title="Zoom" target="_blank"><IMG src="./users/'.$user.'/'.(string)$trip_id.'/pair/'.(string)$id.'_small1.jpg" style="border: 0px solid #666;"></a></div><h3 class="green">'.$fullname2.'</h3><div><a href="./users/'.$user.'/'.(string)$trip_id.'/pair/'.(string)$id.'_big2.jpg" class="jqzoom" title="Zoom" target="_blank"><IMG src="./users/'.$user.'/'.(string)$trip_id.'/pair/'.(string)$id.'_small2.jpg" style="border: 0px solid #666;"></a></div></div></body></html>';
    } else {
      $images[] = 'NEW';
      if ($image_preds_1 == '0')
      {
        $images[] = 3;
      } else {
        $images[] = 4;
      }
      $reprs     = array($repr1,$repr2);
      $images[]  = $reprs;
      $images[]  = '/var/www/html/rapd/users/'.$user.'/'.(string)$trip_id.'/pair/'.(string)$id;
    }
    $plots =  './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id."_plots.php";
    $version = 0;
    $status = 'None';
    $timestamp = $sql -> timestamp;
    $repr = $sql -> repr;
  }
  elseif ($type == 'integrate')
  {
    // Get information from the integrate_results table
    $sql = "SELECT repr,version,integrate_status,solved,timestamp FROM integrate_results WHERE integrate_result_id=$id";
    $result = @mysql_query($sql,$connection) or die(mysql_error());
    $sql = mysql_fetch_object($result);
    $type = 'run';

    //Now put the data into common variables
    $short = './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id.'_short.php';
    $stac = 'None';
    $long = './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id.'_long.php';
    $images = "empty";
    $plots =  './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id."_plots.php";
    $status = $sql -> integrate_status;
    $version = $sql -> version;
    $solved = $sql -> solved;   
    $timestamp = $sql -> timestamp;   
    $my_repr = $sql -> repr;
    //Make a new link with new repr
    if ($status == 'WORKING')
    {
        $repr = "<img id=\"$res_id-gif\" src=\"./css/images/ajax-loader.gif\">$my_repr";    
    }
    elseif ($solved == 'Yes') 
    {
    	$repr = "$my_repr<img id=\"$res_id-more-icon\" src=\"./css/magnifying-glass-icon.png\">";
    }
    else 
    {
        $repr = $sql -> repr;
    }
  }
  elseif ($type == 'merge')
  {
    // Get information from the merge_results table
    $sql = "SELECT repr,merge_status,solved,timestamp FROM merge_results WHERE merge_result_id=$id";
    $result = @mysql_query($sql,$connection) or die(mysql_error());
    $sql = mysql_fetch_object($result);
    $type = 'merge';
    $solved = $sql -> solved;
    $version = 0;

    //Now put the data into common variables
    $short = './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id.'_short.php';
    $stac = 'None';
    $long = './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id.'_long.php';
    $images = "empty";
    $plots =  './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id."_plots.php";
    if ($sql -> merge_status == "SUCCESS") {
        $status = "SUCCESS";
    }
    $timestamp = $sql -> timestamp;
    if ($solved == 'Yes')
    {
    	$my_repr = $sql -> repr;
    	$repr = "$my_repr<img id=\"$res_id-more-icon\" src=\"./css/magnifying-glass-icon.png\">";
    }
    else
    {
    	$repr = $sql -> repr;
    }
//    $repr = $sql -> repr;
  }
  elseif ($type == 'sad')
  {
    // Get information from the integrate_results table
    $sql = "SELECT repr,version,sad_status,timestamp,TIMESTAMPDIFF(SECOND,timestamp,NOW()) AS result_age FROM sad_results WHERE sad_result_id=$id";
    $result = @mysql_query($sql,$connection) or die(mysql_error());
    $sql = mysql_fetch_object($result);
    $type = 'structure';

    //Now put the data into common variables
    $short = './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id.'_shelx.php';
    $stac = 'None';
    $long = './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id.'_autosol.php';
    $images = "empty";
    $plots =  './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id."_shelx_plots.php";
    $status = $sql -> sad_status;
    $version = $sql -> version;
    $timestamp = $sql -> timestamp;
    $result_age = $sql -> result_age;
    $my_repr = $sql -> repr;
    //Make a new link with new repr
    if ($status == 'WORKING' and $result_age < 1200)
    {
        $repr = "<img id=\"$res_id-gif\" src=\"./css/images/ajax-loader.gif\">$my_repr";
    }
    else
    {
        $repr = $sql -> repr;
    }
  }
  elseif ($type == 'mr')
  {
    // Get information from the integrate_results table
    $sql = "SELECT repr,version,mr_status,timestamp,TIMESTAMPDIFF(SECOND,timestamp,NOW()) AS result_age FROM mr_results WHERE mr_result_id=$id";
    $result = @mysql_query($sql,$connection) or die(mysql_error());
    $sql = mysql_fetch_object($result);
    $type = 'structure';

    //Now put the data into common variables
    $short = './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id.'_mr.php';
    $stac = 'None';
    $long = 'None';
    $images = "empty";
    $plots =  'None';
    $status = $sql -> mr_status;
    $version = $sql -> version;
    $timestamp = $sql -> timestamp;
    $result_age = $sql -> result_age;
    $my_repr = $sql -> repr;
    //Make a new link with new repr
    if ($status == 'WORKING' and $result_age < 1200)
    {
        $repr = "<img id=\"$res_id-gif\" src=\"./css/images/ajax-loader.gif\">$my_repr";
    }
    else
    {
        $repr = $sql -> repr;
    }
  }
  //
  // 4th - grab the sample info using sample_id from results
  //
  $sql = "SELECT samples.* FROM samples,results WHERE samples.sample_id = results.sample_id AND results.result_id = '".$res_id."'";
  $result = @mysql_query($sql,$connection) or die(mysql_error());     
  $sql = mysql_fetch_object($result);
  $sample_id = $sql -> sample_id;
  $crystal = $sql -> CrystalID;
  $project = $sql -> Project;
  $puck = $sql -> PuckID;
  $num = $sql -> sample;
  $protein = $sql -> Protein;
  $sample_text = "[".$puck."-".$num."] <b>Sample: ".$crystal."</b> (".$protein.") &nbsp;&nbsp; Project: ".$project;
  
  $arr[] = $short;
  $arr[] = $stac;
  $arr[] = $long;
  $arr[] = $images;
  $arr[] = $plots;
  $arr[] = $status;
  $arr[] = $version;
  $arr[] = $timestamp;
  $arr[] = $repr;
  $arr[] = $sample_id;
  $arr[] = $sample_text;
  
  //Encode in JSON
  $out = json_encode($arr);
  print $out;  

?>



