<?php

require('./login/config.php');
require('./login/functions.php');

//make the connection to the database
  $connection = @mysql_connect(rapd, $dbusername, $dbpassword) or die(mysql_error());
//$db = @mysql_select_db($db_name,$connection)or die(mysql_error());
  $db = @mysql_select_db(rapd_data,$connection) or die(mysql_error());

/* Array of database columns which should be read and sent back to DataTables. Use a space where
 * you want to insert a non-database field (for example a counter or static image)
 */
$aColumns = array('sheetname','PuckID','sample','CrystalID','Protein','Comment','FreezingCondition','CrystalCondition','Metal','Solvent','Person');
	
/* Indexed column (used for fast and accurate table cardinality) */
$sIndexColumn = $_GET['sIndex'];

/* DB table to use */
$sTable = $_GET['sTable'];

/* Column to select */
$sCategory = $_GET['sCategory'];

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
        SELECT $sCategory
        FROM $sTable 
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
$sql2 = "SELECT COUNT($sIndexColumn) FROM $sTable";
$result2 = @mysql_query($sql2,$connection) or die(mysql_error());
$array2 = mysql_fetch_array($result2);
$iTotal = $array2[0];

//Construct the return
$sOutput = '{';
$sOutput .= '"sEcho": '.intval($_GET['sEcho']).', ';
$sOutput .= '"iTotalRecords": '.$iTotal.', ';
$sOutput .= '"iTotalDisplayRecords": '.$iFilteredTotal.', ';
//now all the data in the table
$arr = array();
while ($aRow = mysql_fetch_array($rResult, MYSQL_NUM))	
   {
      array_push($arr,$aRow);
   }

$aaData = array("aaData" => $arr);
$json = json_encode($aaData);
$sOutput .= $json;
$sOutput .= ' }';
echo $sOutput;


?>
