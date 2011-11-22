<?php 
  require('./login/config.php');
  require('./login/functions.php');

  $res_id  = $_GET[res_id];
  $datadir = $_GET[datadir];
  $trip_id = $_GET[trip_id];
//$datadir = "/gpfs1/users/necat/Feb02_2008_test";
//$res_id =  15944;
//$trip_id = 158;

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
  $sql ="SELECT type,id FROM results WHERE result_id=$res_id";
  $result = @mysql_query($sql,$connection) or die(mysql_error());
  $sql = mysql_fetch_object($result);
  $type   = $sql -> type;
  $id     = $sql -> id;

  //
  // 3rd - grab the image name(s) for labeling
  //
  if ($type == 'single')
  {
    $sql         = "SELECT repr,fullname,summary_stac,image_big,image_raw,image_preds FROM single_results WHERE single_result_id=$id";
    $result      = @mysql_query($sql,$connection) or die(mysql_error());
    $sql         = mysql_fetch_object($result);
    $repr        = $sql -> repr;
    $fullname1   = $sql -> fullname;
    $sum_stac    = $sql -> summary_stac;
    $image_big   = $sql -> image_big;
    $image_raw   = $sql -> image_raw;
    $image_preds = $sql -> image_preds;
  }
  elseif ($type == 'pair')
  {
    // Get information from the pair_results table
    $sql = "SELECT fullname_1,fullname_2,summary_stac,image_big_1,image1_id,image2_id,image_raw_1,image_raw_2,image_preds_1,image_preds_2 FROM pair_results WHERE pair_result_id=$id";
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
  }
  elseif ($type = 'integrate')
  {
    $type = 'run';
    $sum_stac = 'None';
  }

  //the parsed tab
  $short = './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id.'_short.php';

  //the MiniKappa tab
  if (! (is_null($sum_stac) or ($sum_stac == 'None')))
  {
    $stac = './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id.'_stac.php';
  }
  else
  {
    $stac = 'None';
  }


  //the full tab
  if ($type == 'single')
  {
    $long = './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id."_long.php";
  } 
  elseif ($type == 'pair') 
  {
    $long = './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id."_long.php";
  } 
  elseif ($type == 'run') 
  {
    $long = array('./users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id."_xia2.log",'./users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id."_xscale.log",'./users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id."_scala.log");
  } 


  //the images tab
  if ($type == 'single') 
  { 
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
  } 
  elseif ($type == 'pair') 
  {
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
  } 
  elseif ($type == 'run') 
  {
    $images = "empty";
  }

  //the plots tab
  $plots =  './users/'.$user.'/'.(string)$trip_id.'/'.$type.'/'.(string)$id."_plots.php";


  $arr[] = $short;
  $arr[] = $stac;
  $arr[] = $long;
  $arr[] = $images;
  $arr[] = $plots;

  //Encode in JSON
  $out = json_encode($arr);
  print $out;  

?>



