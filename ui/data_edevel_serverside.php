<?php

require('./login/config.php');
require('./login/functions.php');

//make the connection to the database
$connection = @mysql_connect($server, $dbusername, $dbpassword) or die(mysql_error());
$db = @mysql_select_db($db_name,$connection)or die(mysql_error());

/* Array of database columns which should be read and sent back to DataTables. Use a space where
 * you want to insert a non-database field (for example a counter or static image)
 */
$aColumns = array('username','trip_start','trip_finish','trip_id','data_root_dir','beamline');
	
/* Indexed column (used for fast and accurate table cardinality) */
$sIndexColumn = "trip_id";

/* DB table to use */
$sTable = "trips";

/* Paging */
$sLimit = "";
if ( isset( $_GET['iDisplayStart'] ) && $_GET['iDisplayLength'] != '-1' )
{
    $sLimit = "LIMIT ".mysql_real_escape_string( $_GET['iDisplayStart'] ).", ".
    	      mysql_real_escape_string( $_GET['iDisplayLength'] );
}

/* Ordering */
if ( isset( $_GET['iSortCol_0'] ) )
{
    $sOrder = "ORDER BY  ";
    for ( $i=0 ; $i<intval( $_GET['iSortingCols'] ) ; $i++ )
    {
        if ( $_GET[ 'bSortable_'.intval($_GET['iSortCol_'.$i]) ] == "true" )
        {
            $sOrder .= $aColumns[ intval( $_GET['iSortCol_'.$i] ) ]."
                       ".mysql_real_escape_string( $_GET['sSortDir_'.$i] ) .", ";
        }
    }

    $sOrder = substr_replace( $sOrder, "", -2 );
    if ( $sOrder == "ORDER BY" )
    {
        $sOrder = "";
    }
}

/* 
 * Filtering
 * NOTE this does not match the built-in DataTables filtering which does it
 * word by word on any field. It's possible to do here, but concerned about efficiency
 * on very large tables, and MySQL's regex functionality is very limited
 */
$sWhere = "";
if ( $_GET['sSearch'] != "" )
{
    $sWhere = "WHERE (";
    for ( $i=0 ; $i<count($aColumns) ; $i++ )
    {
        $sWhere .= $aColumns[$i]." LIKE '%".mysql_real_escape_string( $_GET['sSearch'] )."%' OR ";
    }
    $sWhere = substr_replace( $sWhere, "", -3 );
    $sWhere .= ')';
}
	
/* Individual column filtering */
for ( $i=0 ; $i<count($aColumns) ; $i++ )
{
    if ( $_GET['bSearchable_'.$i] == "true" && $_GET['sSearch_'.$i] != '' )
    {
        if ( $sWhere == "" )
        {
            $sWhere = "WHERE ";
        }
        else
        {
            $sWhere .= " AND ";
        }
        $sWhere .= $aColumns[$i]." LIKE '%".mysql_real_escape_string($_GET['sSearch_'.$i])."%' ";
    }
}

//build and issue the query
$sql ="
        SELECT SQL_CALC_FOUND_ROWS username, trip_start, trip_finish, trip_id, data_root_dir, beamline 
        FROM trips 
        $sWhere
        $sOrder
        $sLimit
      ";
$rResult = @mysql_query($sql,$connection) or die(mysql_error());

//Count the number of filtered rows
$sQuery = "
	    SELECT FOUND_ROWS()
	  ";
$rResultFilterTotal = mysql_query( $sQuery, $connection ) or die(mysql_error());
$aResultFilterTotal = mysql_fetch_array($rResultFilterTotal);
$iFilteredTotal = $aResultFilterTotal[0];

//how many total rows are there?
$sql2 = "SELECT COUNT(trip_id) FROM trips";
$result2 = @mysql_query($sql2,$connection) or die(mysql_error());
$array2 = mysql_fetch_array($result2);
$iTotal = $array2[0];

//Construct the return
$sOutput = '{';
$sOutput .= '"sEcho": '.intval($_GET['sEcho']).', ';
$sOutput .= '"iTotalRecords": '.$iTotal.', ';
$sOutput .= '"iTotalDisplayRecords": '.$iFilteredTotal.', ';
$sOutput .= '"aaData": [ ';
//now all the data in the table 
while ($aRow = mysql_fetch_array($rResult))	
{
    $sOutput .= "[";
    $sOutput .= '"'.addslashes($aRow['username']).'",';
    $sOutput .= '"'.addslashes($aRow['trip_start']).'",'; 
    $sOutput .= '"'.addslashes($aRow['trip_finish']).'",';
    $sOutput .= '"'.addslashes($aRow['trip_id']).'",';
    $sOutput .= '"'.addslashes($aRow['data_root_dir']).'",';
    $sOutput .= '"'.addslashes($aRow['beamline']).'"';
    $sOutput .= "],";
}

$sOutput = substr_replace( $sOutput, "", -1 );
$sOutput .= '] }';
echo $sOutput;


function fnColumnToField( $i )
{
    if ($i == 0)
        return("username");
    else if ($i == 1)
        return("trip_start");
    else if ($i == 2)
        return("trip_finish");
    else if ($i == 3)
        return("trip_id");
    else if ($i == 4)
        return("data_root_dir");
    else if ($i == 5)
        return("beamline");
}
?>
