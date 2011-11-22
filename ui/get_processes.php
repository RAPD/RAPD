<?php 
  require('./login/config.php');
  require('./login/functions.php');

  //Start handling the POST
  $datadir = $_GET[datadir];

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db(rapd_data,$connection)or die(mysql_error());        

  //build and issue the query
  $sql ="SELECT * FROM processes WHERE data_root_dir='$datadir' AND TIMESTAMPDIFF(SECOND,timestamp1,NOW())<1800 AND display='show' ORDER BY process_id";
  $result = @mysql_query($sql,$connection) or die(mysql_error());
  
  $arr = array();
  if (mysql_num_rows($result) > 0) {
    while ($sql = mysql_fetch_object($result)) {
      $pro_id  = $sql -> process_id;
      $type    = $sql -> type;
      $rtype   = $sql -> rtype;
      $repr    = $sql -> repr;
      $display = $sql -> display;
      $time    = $sql -> timestamp1;

      $arr[] = $type;
      $arr[] = $display;
      $arr[] = $pro_id;
      $arr[] = $rtype;
      $arr[] = "<div class=\"in_process_$pro_id\" id=\"in_process_$pro_id\"><img src=\"./css/images/ajax-loader.gif\"><a title=\"$time R-click for options\" class=\"in-process\" href=\"#\" id=\"$pro_id\" rel=\"\">$repr</a></br></div>\n";
    }
  }

  //Encode in JSON
  $out = json_encode($arr);
  print $out;  
?>

