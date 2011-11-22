<?php 
  require('./login/config.php');
  require('./login/functions.php');

  //Start handling the POST
  $datadir = $_GET[datadir];
  $lastid  = $_GET[id];
  //$datadir = "/gpfs3/users/cornell/Ealick_Aug10";
  //$lastid = 0;

  //$count = 0;

  //make the connection to the database
  $connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
  $db = @mysql_select_db(rapd_data,$connection)or die(mysql_error());        

  //build and issue the query
  $sql ="SELECT ir.result_id,ir.repr,ir.spacegroup,ir.a,ir.b,ir.c,ir.alpha,ir.beta,ir.gamma,
                isro.high_res,
                isr.completeness,isr.multiplicity,isr.r_pim,isr.anom_slope 
         FROM integrate_results AS ir 
              JOIN (integrate_shell_results AS isr 
                    CROSS JOIN integrate_shell_results AS isri 
                    CROSS JOIN integrate_shell_results AS isro) 
              ON (ir.shell_overall=isr.isr_id 
                  AND ir.shell_inner=isri.isr_id 
                  AND ir.shell_outer=isro.isr_id) 
         WHERE ir.data_root_dir='$datadir' 
              AND ir.result_id>$lastid 
              AND ir.integrate_status!='FAILED' 
         ORDER BY ir.result_id";
  $result = @mysql_query($sql,$connection) or die(mysql_error());
 
  $arr = array();
  if (mysql_num_rows($result) > 0) {
    while ($sql = mysql_fetch_object($result)) {
      $res_id     = $sql -> result_id;
      $id         = $sql -> integrate_result_id; 
      $repr       = $sql -> repr;
      $spacegroup = str_replace(' ','',$sql->spacegroup);
      $a          = $sql -> a; 
      $b          = $sql -> b;
      $c          = $sql -> c;
      $alpha      = $sql -> alpha;
      $beta       = $sql -> beta;
      $gamma      = $sql -> gamma;
      $res        = $sql -> high_res;
      $complete   = $sql -> completeness;
      $mult       = $sql -> multiplicity;
      $r_pim      = $sql -> r_pim;
      $anom_slp   = $sql -> anom_slope; 

      $arr[] = $repr;
      $arr[] = $spacegroup;
      $arr[] = $a;
      $arr[] = $b;
      $arr[] = $c;
      $arr[] = $alpha;
      $arr[] = $beta;
      $arr[] = $gamma;
      $arr[] = $res;
      $arr[] = $complete;
      $arr[] = $mult;
      $arr[] = $r_pim;
      $arr[] = $anom_slp;
      $arr[] = $res_id;
    }
  //Encode in JSON
  $out = json_encode($arr);
  print $out;
  } 
?>

