<?php

//prevents caching
header("Expires: Sat, 01 Jan 2000 00:00:00 GMT");
header("Last-Modified: ".gmdate("D, d M Y H:i:s")." GMT");
header("Cache-Control: post-check=0, pre-check=0",false);
session_cache_limiter();
session_start();

require('./login/config.php');
require('./login/functions.php');

if (is_null($url)) { 
   $url = "e_trip_data_main.php";
};

//this is group name or username of the group or person that you wish to allow access to
// - please be advise that the Administrators Groups has access to all pages.

//if (allow_access(Administrators) != "yes")
//{
//    include ('./login/no_access.html');
//    exit;
//}

if(allow_user() != "yes")
{
    include ('./login/no_access.html');
    exit();
}

?>

<head>
  <meta http-equiv="Content-Language" content="en-us">
  <!-- The dataTables css -->
  <link type="text/css" href="css/ndemo_table.css"  rel="stylesheet" />
  <link type="text/css" href="css/ndemo_page.css"   rel="stylesheet" />
  <!-- The jquery UI css -->
  <link type="text/css" href="css/south-street/njquery-ui-1.7.2.custom.css" rel="stylesheet" />
  <!-- The custom rapd css -->
  <link type="text/css" href="css/rapd.css"         rel="stylesheet" /> 

  <title>RAPD</title>
  <link rel="shortcut icon" href="./css/favicon.ico" type="image/x-icon">
  <script src="http://www.google.com/jsapi?key=ABQIAAAArmeu5LmO0GnPE-nZ0Fe1qhQOqcOQgkuU1c5Ip7P-iLN3BAQyDBR1yNT4dNxyOxjnbWKQzT76MupHkw"></script>
  <script>
    google.load("jquery", "1.4.2");
    google.load("jqueryui", "1.7.2");
  </script>
  <script type="text/javascript" language="javascript" src="./js/jquery.dataTables.1.7.1.min.js">  </script>
</head>

<body class='banner'>
<h1>RAPD Trips</h1>

  <table border="0" width="100%" id="table1">
    <tr valign="top">
      <td>
        <table>
          <tr>
            <td><b>Logged in as <?php echo $_SESSION[username]; ?></b></td>
          </tr>
          <tr>
            <td><i><a href="main.php">Go to Main Page</a></i></td>
          </tr>
<?
    if (allow_access(Administrators) == "yes")
    {
        echo('             <tr>');
        echo('               <td><i><a href="./login/admin/adminpage.php">Go to Administrative Control Panel</a></i></td>');
        echo('             </tr>');
    }
?>
          <tr>
            <td><i><a href="./login/logout.php">Logout</a></i></td>
          </tr>
        </table>
    </td>
    <td>
    <div id="auto_wrapper" class="dataTables_wrapper">
      <table id='trip_table' class='ranking'>
        <thead>
          <tr>
            <th class='sorting'>User</th>
            <th class='sorting'>Start Date</th>
            <th class='sorting'>End Date</th>
            <th class='sorting'>Trip_ID</th>
            <th class='sorting'>Root Data Dir</th>
            <th class='sorting'>Beamline</th>
          </tr>
        </thead>
        <tbody>
          <tr>
	    <td colspan="5" class="dataTables_empty">Loading data from server</td>
	  </tr>
        </tbody>
      </table>
    </div>
      </td>
    </tr>
  </table>

  <script type='text/javascript'>
    $(document).ready(function() {
	tripTable = $('#trip_table').dataTable( {
		"bProcessing": true,
		"bServerSide": false,
		"sAjaxSource": "./data_edevel_serverside.php",
                "aaSorting": [[ 2, "desc" ]],
                "aoColumns": [ 
<?
     if (allow_access(Administrators) == "yes")
     {
       echo('                               {"sType":"string","sWidth":"20%"},');
     } else {
       echo('                               {"sType":"string","sWidth":"20%", "bVisible":false},');
     }
?>
                               {"sType":"date","sWidth":"10%","sClass":"center"},
                               {"sType":"date","sWidth":"10%","sClass":"center"},
                               {"bVisible":false},
                               {"sType":"string","sWidth":"50%"},
                               {"sType":"string","sWidth":"10%","sClass":"center"}],
                 "bJQueryUI": true,
                 "iDisplayLength": 50,
	      "fnServerData": function ( sSource, aoData, fnCallback ) {
              if ("<?php echo(allow_access(Administrators)) ?>" != "yes" ) {
                 aoData.push({"name":"sSearch", "value": "<?php echo $_SESSION[username]; ?>"});
              };
	      $.ajax( {
		  "dataType": 'json',
		    "type": "GET",
                    "url": sSource,
                    "data": aoData,
                    "success": fnCallback
		    });
	    },
                "fnDrawCallback": function() {
				clickRowHandler();
		}
	} );
    

        // Handler for click events on the trip table
        function clickRowHandler() {
    	/* Highlight selected row on single click */
	    $('#trip_table tbody tr').click(function(event) {
	        $(tripTable.fnSettings().aoData).each(function (){
		    $(this.nTr).removeClass('row_selected');
		});
		$(event.target.parentNode).toggleClass('row_selected');
	    });
    	
    	    /* Link to detail page of selected row on double click */
            $('#trip_table tbody tr').bind('dblclick', function () {
                var aData = tripTable.fnGetData( this );
                //alert(aData);
                //Now move to the new page
                var url='<?php echo $url; ?>';
                var params = { user:aData[0], trip_id:aData[3], data:aData[4], beamline:aData[5]};
                $.doPost(url,params); 
            });
        }  //Close the clickRowHandler

                $.extend({
                    doGet: function(url, params) {
                        document.location = url + '?' + $.param(params);
                    },
                    doPost: function(url, params) {
                        var $div = $("<div>").css("display","none");
                        var $form = $("<form method='POST'>").attr("action", url);
                        $.each(params, function(name, value) {
                            $("<input type='hidden'>")
                            .attr("name", name)
                            .attr("value", value)
                            .appendTo($form);
                        });
                        $form.appendTo($div);
                        $form.appendTo("body");
                        $form.submit();
                    }
                });


    });  //Close the document ready function
  </script>

</body>
