<div id="auto_wrapper" class="dataTables_wrapper">

    <script language="javascript" type="text/javascript" src="./js/jquery.dataTables.1.7.1.min.js"></script>
  
<script id="source" language="javascript" type="text/javascript">
$(document).ready(function() {
	samplesTable = $('#samples').dataTable( {
		"bProcessing": true,
	        "sAjaxSource": "getSamples.php?username="+my_user+"&datadir="+my_datadir,
	        "aoColumns": [
			    /* Unique Sample ID */ { "bVisible": false },
			    /* Filename */ null,
			    /* Puck ID */ null,
			    /* Sample Number */ { "sWidth": "3px" },
			    /* Crystal ID */ null,
			    /* Protein */ null,
			    /* Comment */ null,
			    /* Freezing Condition */ null,
			    /* Crystal Condition */ null,
			    /* Metal */ null,
			    /* Solvent Content */ null,
			    /* Person */ null,
			    /* Username */ { "bVisible": false },
			    /* Timestamp */ { "bVisible": false },
                            ],
	        "bAutoWidth": false,
                "bJQueryUI": true,
	      "iDisplayLength": 50
	} );
    $("#id_hideFilename").click( function() {
        samplesTable.fnSetColumnVis(1, this.checked);
    });
    $("#id_hidePuck").click( function() {
	samplesTable.fnSetColumnVis(2, this.checked);
    });
    $("#id_hideNumber").click( function() {
	samplesTable.fnSetColumnVis(3, this.checked);
    });
    $("#id_hideCrystal").click( function() {
	samplesTable.fnSetColumnVis(4, this.checked);
    });
    $("#id_hideProtein").click( function() {
	samplesTable.fnSetColumnVis(5, this.checked);
    });
    $("#id_hideComment").click( function() {
	samplesTable.fnSetColumnVis(6, this.checked);
    });
    $("#id_hideFreezeCond").click( function() {
	samplesTable.fnSetColumnVis(7, this.checked);
    });
    $("#id_hideCrystalCond").click( function() {
	samplesTable.fnSetColumnVis(8, this.checked);
    });
    $("#id_hideMetal").click( function() {
	samplesTable.fnSetColumnVis(9, this.checked);
    });
    $("#id_hideSolvent").click( function() {
	samplesTable.fnSetColumnVis(10, this.checked);
    });
    $("#id_hidePerson").click( function() {
	samplesTable.fnSetColumnVis(11, this.checked);
    });
    //Refresh samplesTable when tab is clicked
        $("#tabs0-tab0-tabs1").bind('tabsselect', function (event,ui) {
	    if (ui.index == 7) {
    	      samplesTable.fnReloadAjax();
            };
        });
});
$.fn.dataTableExt.oApi.fnReloadAjax = function ( oSettings, sNewSource, fnCallback, bStandingRedraw )
{
	if ( typeof sNewSource != 'undefined' && sNewSource != null )
	{
		oSettings.sAjaxSource = sNewSource;
	}
	this.oApi._fnProcessingDisplay( oSettings, true );
	var that = this;
	var iStart = oSettings._iDisplayStart;
	
	oSettings.fnServerData( oSettings.sAjaxSource, null, function(json) {
		/* Clear the old information from the table */
		that.oApi._fnClearTable( oSettings );
		
		/* Got the data - add it to the table */
		for ( var i=0 ; i<json.aaData.length ; i++ )
		{
			that.oApi._fnAddData( oSettings, json.aaData[i] );
		}
		
		oSettings.aiDisplay = oSettings.aiDisplayMaster.slice();
		that.fnDraw( that );
		
		if ( typeof bStandingRedraw != 'undefined' && bStandingRedraw === true )
		{
			oSettings._iDisplayStart = iStart;
			that.fnDraw( false );
		}
		
		that.oApi._fnProcessingDisplay( oSettings, false );
		
		/* Callback user function - for event handlers etc */
		if ( typeof fnCallback == 'function' && fnCallback != null )
		{
			fnCallback( oSettings );
		}
	} );
}

</script>
<noscript>
    <h1 align="center"><font color="#FF0000">Javascript is required to view this page.</font></h1>
</noscript>


  <table class="ranking" width="100%" id="samples">
    <thead align="center">
      <tr>
        <th>Unique Sample ID</th>
        <th>Filename</th>
        <th>Puck ID</th>
        <th> &#35; </th>
        <th>Crystal ID</th>
        <th>Protein</th>
        <th>Comment</th>
        <th>Freezing Condition</th>
        <th>Crystal Condition</th>
        <th>Metal</th>
        <th>Solvent Content</th>
        <th>Person</th>
        <th>Username</th>
        <th>Timestamp</th>
      </tr>
    </thead>
  <tbody align="center">
      <tr>
	<td colspan="5" class="dataTables_empty">Loading data from server</td>
      </tr>
 </tbody>
</table>

<input type="checkbox" checked="checked" id="id_hideFilename">Filename
<input type="checkbox" checked="checked" id="id_hidePuck">Puck ID
<input type="checkbox" checked="checked" id="id_hideNumber">Number 
<input type="checkbox" checked="checked" id="id_hideCrystal">Crystal ID
<input type="checkbox" checked="checked" id="id_hideProtein">Protein
<input type="checkbox" checked="checked" id="id_hideComment">Comment
<input type="checkbox" checked="checked" id="id_hideFreezeCond">Freezing Condition
<input type="checkbox" checked="checked" id="id_hideCrystalCond">Crystal Condition
<input type="checkbox" checked="checked" id="id_hideMetal">Metal
<input type="checkbox" checked="checked" id="id_hideSolvent">Solvent Content
<input type="checkbox" checked="checked" id="id_hidePerson">Person
  
</div>

