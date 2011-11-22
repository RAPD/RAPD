    include("./js/jquery.flot.0.6.min.js")
    include("./js/jquery.dataTables.1.7.1.min.js")
    //include("./js/dataTables.fnDisplayRow.min.js")
    //include("./js/jquery.jeegoocontext.1.2.2.min.js")
    include("./js/thickbox.js")
    //include("./js/jquery.livequery.js") 
    include("./js/ajaxfileupload/ajaxfileupload.js")
    //include("./js/jmol-12.1.13/Jmol.js")
    include("./js/jquery.datatables.reload.js")

    lastresultID = 0;
    lastresultTime = '0';
    lastsnaprankID = 0;
    lastrunrankID = 0;
    lastcloudID = 0;
    lastsettingID = 0;

    currentresultID = 0;
    currentresultType = 'None';
    currentanalysisID = 0;
    
    currentstructureresultID = 0;
    currentstructureresultType = 'None';

    snapsSortTable = '' ;
    runsSortTable = '';

    number_images = 0;
    image_repr = '';
    image_string = '';
    image_mode = 'NONE';
    image_shown = 'False';

    waiting_for_run = 0;
    waiting_for_sad = 0;


    // Is the cloud open for business? 1 = yes, 0 = no
    cloud_download  = '1';
    cloud_process   = '1';

    // Keep a count of downloads that are currently running
    downloads_active = 0;

    // Is this an administrator?
    admin = 'no';

    //Variables for modifying behavior based on state
    instance_local  = 'False';
    instance_active = 'False';
    waiting_for_cloud = 'False';

    function closeDownloadDialog(){
        if (downloads_active == 0) 
        {
            $('#download_active').slideToggle('slow');
        }
        var tmp = setTimeout(closedownloaddialog, 5000); 
    };
    function closedownloaddialog(){
        $download_dialog.dialog('close');
    }

    //
    // The main document ready function
    // 
    $(document).ready(function(){
        //Debugging
        //alert(my_beamline);
        //alert(my_ip);
        //alert(my_user);
        //alert(my_datadir);
        //alert(my_trip_id);

		//Elements repeteadly called
		$snap_menu_in_process = $("#snap_menu_in_process");
		$snap_menu = $("#snap_menu");
		$run_menu = $("#run_menu");
		

        //Make sure we are scrolled to the correct position
        $(window).scrollTop(0);
        $(window).scrollLeft(0);

        //Hide the dialogs
        $download_dialog = $('#download-dialog').dialog( { autoOpen: false,
                                        title: 'Download Initiated' });

        $dialog_generic = $('#dialog-generic').dialog({autoOpen:false,
                                                       modal:true});

        $('#dialog-transient').dialog({autoOpen:false,
                                       modal:false,
                                       dialogClass:'transient',
                                       show:'clip',
                                       hide:'clip'});
        //
        // 
        //Data-Merging-Structure Tab Set
        $('#tabs0').tabs({remote:true,selected:0});
        
            //The Snaps/Runs Tab Set
            $("#tabs0-tab0-tabs0").tabs({remote:true,selected:0});
        
            //The Results Tab Set
            $("#tabs0-tab0-tabs1").tabs({
                remote:true,
                selected:0,
            });

          //Merging tab
          $('#tabs0-tab1').hide();
        
          //Structure tab
            //The SAD/MR/Ligand Tab Set
            $('#tabs0-tab2-tabs0').tabs({remote:true});
            //$("#tabs0-tab2-tabs0-1").hide();  //Hide the MR tab
            $("#tabs0-tab2-tabs0-2").hide();  //Hide the Ligand tab
            
            //The Results Tab Set
            $('#tabs0-tab2-tabs1').tabs({remote:true});
        
		$("#analysis_tabs").tabs();

        //Controls tab
        $('#tabs1').tabs({remote:true});
        
        //The image viewer - if clicked on make sure image loads
        $('#tabs0-tab0-tabs1').bind('tabsselect', function(event, ui) {
            if (ui.index == 3) {
                if (image_shown == 'False')
                {
                    image_shown = 'True';
                    if (image_mode == 'NEW')
                    {
                        $("#mooviewer").show();
                        $("#old_images").empty();
                        load_images(number_images,image_repr,image_string);
                    }
                }
            }
//            else if (ui.index == 8){
                //alert("Samples Tab Clicked.");
				// RELOAD_SAMPLES
                //samplesTable.dataTable().fnReloadAjax();
//            }
        });


        // start the refreshing of images on the left
        var timeoutID = setTimeout(GetInfoAndStart, 1);

        // load up the splash page
        $("#summary").load("splash.php");

        // Hide various elements
        $('#download_active').hide();
        $('#reference_data_active').hide();
        $('#mooviewer').hide();

        // The indicators for live usage
        $('#controller').prepend("<img src='css/images/LEDs/green-off-16.png'");
        $('#cluster').prepend("<img src='css/images/LEDs/green-off-16.png'");
        $('#dataserver').prepend("<img src='css/images/LEDs/green-off-16.png'");
        $('#led_button').hide();

        // hover states on the static widgets
        $('#dialog_link, ul#icons li').hover(
            function() { $(this).addClass('ui-state-hover'); },
            function() { $(this).removeClass('ui-state-hover'); }
        );

        //React to clicks in the image tabs for snaps
        $snap_menu.delegate('a','click',function(e){
          if( (!$.browser.msie && e.button == 0) || ($.browser.msie && e.button == 1) ) {
                res_id = $(this).attr("id");

                //Mark the current click as being viewed and clear the rest
                $snap_menu.children().removeClass("clicked");
                $run_menu.find('a').removeClass("clicked");
                $snap_menu.find('#'+res_id).addClass("clicked");
                //Load the data
                loadSnap(res_id);
                //Update the highlighting in the ranking table
                //take highlight from other rows
                $(snapsSortTable.fnSettings().aoData).each(function (){
                    if ($(this._aData)[11] == res_id)
                    {
                        $(this.nTr).addClass('row_selected');
                    } else {
                        $(this.nTr).removeClass('row_selected');
                    }
                });
                return false;
            }
        });

        $run_menu.delegate('a','click',function(e){
            if( (!$.browser.msie && e.button == 0) || ($.browser.msie && e.button == 1) ) {
                //Mark the current click as being viewed and clear the rest
                $snap_menu.children().removeClass("clicked");
                $("#run_menu_in_process").children().removeClass("clicked");
                $run_menu.find('a').removeClass("clicked");
                $(this).addClass("clicked");
                //Load the data
				currentanalysisID = 0;
                loadRun($(this).attr("id"),-1,false);
            }
        });
        $run_menu_in_process = $('#run_menu_in_process').delegate('a','click',function(e){
            if( (!$.browser.msie && e.button == 0) || ($.browser.msie && e.button == 1) ) {
                //Mark the current click as being viewed and clear the rest
                $("#snap_menu_wrapper").children().removeClass("clicked");
                $("#run_menu_wrapper").find('a').removeClass("clicked");
                $(this).parent().addClass("clicked");
                //Note that we are waiting for this process to come in
                waiting_for_run = this.id;
                //Load the data
                //alert("Waiting for process "+this.id);
                // Summary tab 
                $("#tabs0-tab0-tabs1-0").css("display","list-item");
                $("#summary").empty().append("<h1 class=\"green\">Waiting</h1>");
                // If focus is on STAC tab, change focus since the tab will soon disappear 
                if ($('#tabs0-tab0-tabs1').tabs('option', 'selected') == 1)
                {
                    $('#tabs0-tab0-tabs1').tabs('select', 0 );
                }
                else if ($('#tabs0-tab0-tabs1').tabs('option', 'selected') == 3)
                {
                    $('#tabs0-tab0-tabs1').tabs('select', 0 );
                }
                // Make sure the STAC display is gone
                $("#stac-summary").empty();
                $("#tabs0-tab0-tabs1-tab1").css("display","none");
                // Details tab 
                $("#tabs0-tab0-tabs1-2").css("display","list-item");
                $("#detail").empty();
                // Load the images - none right now 
                $("#tabs0-tab0-tabs1-tab3").css("display","none");
                // Load the plots
                $("#tabs0-tab0-tabs1-4").css("display","list-item");
                $("#plots").empty();
            }
        });


        $('#sad_menu').delegate('a','click',function(e){
            if( (!$.browser.msie && e.button == 0) || ($.browser.msie && e.button == 1) ) {
                //Mark the current click as being viewed and clear the rest
                $("#sad_menu_wrapper").children().removeClass("clicked");
                $("#mr_menu_wrapper").children().removeClass("clicked");
                $(this).addClass("clicked");
                //Load the data
                loadSad($(this).attr("id"),-1,false);
            }
        });
        $('#sad_menu_in_process').delegate('a','click',function(e){
            if( (!$.browser.msie && e.button == 0) || ($.browser.msie && e.button == 1) ) {
                //Mark the current click as being viewed and clear the rest
                $("#sad_menu_wrapper").children().removeClass("clicked");
                $("#mr_menu_wrapper").children().removeClass("clicked");
                $(this).parent().addClass("clicked");
                //Note that we are waiting for this process to come in
                waiting_for_sad = this.id;
                //alert("Waiting for "+waiting_for_sad);
                //Clear out the tabs and load waiting message
                $("#shelx-results").empty().append("<h1 class=\"green\">Waiting</h1>");
                $("#shelx-plots").empty();
                $("#autosol-results").empty();
            }
        });

        $('#mr_menu').delegate('a','click',function(e){
            if( (!$.browser.msie && e.button == 0) || ($.browser.msie && e.button == 1) ) {
                //Mark the current click as being viewed and clear the rest
                $("#mr_menu_wrapper").find('a').removeClass("clicked");
                $(this).addClass("clicked");
                //Load the data
                loadMr($(this).attr("id"),-1,false);
            }
        });
		
		//Download out of one of the tables of results
        $("#tabs0-tab2-tabs1-0").delegate('button','click',function(event,context){
            var tmp = this.id.split(':');
            if (tmp[0] == 'mr' || tmp[0] == 'sad')
            {
              //alert(currentstructureresultID+" "+tmp[1]);
              if (cloud_download == '1')
              {
                  $.get('get_download.php',{ datadir : my_datadir,
                                             id : currentstructureresultID,
                                             spacegroup : tmp[1],
                                             type : tmp[0],
                                             ip : my_ip });                                    
                  $download_dialog.dialog('open')
                      .parents(".ui-dialog")
                      .find(".ui-dialog-titlebar")
                      .remove();
                  $download_dialog.dialog( "option", "height", 'auto');
                  waiting_for_cloud = 'True';
                  closeDownloadDialog();
                  downloads_active += 1;
              } else {
                  alert('Sorry - downloading not currently enabled');
              }
            }
        });

		//Download out of an analysis MR table
		$("#analysis-cell-tab").delegate('button','click',function(event,context){
            var tmp = this.id.split(':');
            if (tmp[0] == 'mr' || tmp[0] == 'sad')
            {
              //alert(currentstructureresultID+" "+tmp[1]);
              if (cloud_download == '1')
              {
                  $.get('get_download.php',{ datadir : my_datadir,
                                             id : currentanalysisID,
                                             spacegroup : tmp[1],
                                             type : "integrate",
                                             ip : my_ip });                                    
                  $download_dialog.dialog('open')
                      .parents(".ui-dialog")
                      .find(".ui-dialog-titlebar")
                      .remove();
                  $download_dialog.dialog( "option", "height", 'auto');
                  waiting_for_cloud = 'True';
                  closeDownloadDialog();
                  downloads_active += 1;
              } else {
                  alert('Sorry - downloading not currently enabled');
              }
            }
        });
		

        //React to control button presses
        $('#go_to_main').click(function () {
            document.location.href = 'main.php';
        });

        $('#go_to_trips').click(function () {
            document.location.href = 'data_devel.php';
        });

        $('#go_to_logout').click(function () {
            document.location.href = 'login/logout.php';
        });

        $('#button_global_settings').click(function(){
            //new-style modal dialog
            $dialog_generic.load("global_settings.php",
                {datadir:my_datadir,
                 beamline:my_beamline},
                function(response, status, xhr) {
                    $(this).dialog( "option", "title", "Global Settings");
                    $dialog_generic.dialog("option","width",400);
                    $dialog_generic.dialog("option","height",650);
                    $(this).dialog("option", "buttons", {
                        'Submit': function() {
                            //alert($('#form-global-settings').serialize());
                            $.ajax({
                                type:"POST",
                                url:"add_settings.php",
                                data:$('#form-global-settings').serialize(),
                                success:function(){
                                    $dialog_generic.dialog("close");
                                    PopupSuccessDialog("Global settings changed");
                                },
                                error:function(textStatus){
                                    $dialog_generic.dialog("close");
                                    PopupFailureDialog("Error while changing global settings: "+textStatus);
                                }
                            });
                            $(this).dialog('close');
                        },
                        'Cancel': function() {$(this).dialog('close');}
                    });
                    $(this).dialog('open');
                }
            );

        });

        //Puck Selection Dialog
        $('#puck-dialog').click(function() {
            $dialog_generic.dialog( "option", "title", "Assign Pucks" );
            $dialog_generic.dialog( "option", "width", 700 );
            $dialog_generic.dialog( "option", "height", 400 );
            $dialog_generic.load("puck_settings.php", {beamline:my_beamline,
                                                            username:my_user,
                                                            datadir:my_datadir});
            $dialog_generic.dialog("option", "buttons", {
                'OK': function() {
                                  var form = $('#SelectPuck');
                                  //Assemble the variables to be passed on
                                  var valueA = $('select[name=PuckA]').val();
                                  var valueB = $('select[name=PuckB]').val();
                                  var valueC = $('select[name=PuckC]').val();
                                  var valueD = $('select[name=PuckD]').val();
                                  if ((valueA != "None") && 
                                     (valueA == valueB || valueA == valueC || valueA == valueD)) {
                                          alert("Two pucks have the same assignment.");
                                          return false;
                                  } else if ((valueB != "None") && (valueB == valueC || valueB == valueD)) {
                                          alert("Two pucks have the same assignment.");
                                          return false;
                                  } else if ((valueC !="None") && (valueC == valueD)) {
                                          alert ("Two pucks have the same assignment.");
                                          return false;
                                  } else if ((valueA == "None") && (valueB == "None") && (valueC == "None") &&
                                      (valueD == "None")) {
                                      $(this).dialog('close');
                                  } else {
                                      var data_root_dir = $('input[name=datadir]').val();
                                      var beamline = $('input[name=beamline]').val();
                                      //Send it off
                                      $.ajax({
                                          type: "POST",
                                          url: "select_puck.php",
                                          data: {datadir:data_root_dir,
                                                 beamline:beamline,
                                                 PuckA:valueA,
                                                 PuckB:valueB,
                                                 PuckC:valueC,
                                                 PuckD:valueD,
                                                }
                                      });
                                      $(this).dialog('close');
                                  }
                                 },
                'Cancel': function() {$(this).dialog('close');}
            }); 
            $dialog_generic.dialog('open');
        });
 
        //Ranking datatables
        snapsSortTable = $('#snaps-sort-table').dataTable({
                           "aoColumns": [ null,
                                          null,
                                          null,
                                          null,
                                          null,
                                          null,
                                          null,
                                          null,
                                          null,
                                          null,
                                          null,
                                          {"bVisible":false} ],
                           "aaSorting": [[ 10, "desc" ]],
                           "bJQueryUI": true,
                           "iDisplayLength": 25
        });
        runsSortTable = $('#runs-sort-table').dataTable({
                        "aoColumns": [ null,
                                       null,
                                       null,
                                       null,
                                       null,
                                       null,
                                       null,
                                       null,
                                       null,
                                       null,
                                       null,
                                       null,
                                       null,
                                       {"bVisible":false}],
                        "aaSorting": [[ 8, "asc" ]],
                        "bJQueryUI": true,
                        "iDisplayLength": 25
        });

        // Handlers for click events on the ranking tables
        $("#snaps-sort-table tbody").click(function(event) {
            //take highlight from other rows
            $(snapsSortTable.fnSettings().aoData).each(function (){
                $(this.nTr).removeClass('row_selected');
            });
            //highlight the clicked row
            $(event.target.parentNode).addClass('row_selected');
            //get the result id from the hidden column of the table
            var res_id = snapsSortTable.fnGetData(snapsSortTable.fnGetPosition(event.target.parentNode))[11];
            //simulate a click on the snap_menu item which has this res_id
            //Make sure the selected from is in view
            $('#tabs0-tab0-tabs0').tabs('select', 0 );
            $('#snap_menu_wrapper').animate({scrollTop: $snap_menu.children('.'+res_id).offset().top-$('.snap_menu').offset().top-100},500);
            //Mark the current click as being viewed and clear the rest
            $snap_menu.children('.clicked').removeClass("clicked");
            $run_menu.children('.clicked').removeClass("clicked");
            $snap_menu.children('.'+res_id).addClass("clicked");
            //Load the data
            loadSnap(res_id);
        }); //Close for  $("#snaps-sort-table tbody").click(function(event) {

        $('#runs-sort-table tbody').click(function(event) {
            //take highlight from other rows
            $(runsSortTable.fnSettings().aoData).each(function (){
                $(this.nTr).removeClass('row_selected');
            });
            //highlight the clicked row
            $(event.target.parentNode).addClass('row_selected');
            //get the result id from the hidden column of the table
            var res_id = runsSortTable.fnGetData(runsSortTable.fnGetPosition(event.target.parentNode))[13];
            //console.log(res_id);
            //simulate a click on the run_menu item which has this res_id
            //Make sure the selected from is in view
            $('#tabs0-tab0-tabs0').tabs('select', 1 );
            $('#run_menu_wrapper').animate({scrollTop: $('#run_menu, #'+res_id).offset().top-$('.run_menu').offset().top-100},500);
            //Mark the current click as being viewed and clear the rest
            $snap_menu.children('.clicked').removeClass("clicked");
            $run_menu.children('.clicked').removeClass("clicked");
            $('#'+res_id).addClass("clicked");
            //Load the data
			currentanalysisID = 0;
            loadRun(res_id,-1,false);
        }); //Close for  $('#runs-sort-table tbody").click(function(event) {

        //$('#pdb').delegate('tr','click',function(e){
        //    alert("Click");
        //});

        //Tooltips for the ranking tables
        $('#snaps-sort-table thead th').each(function(){
            switch ($(this).text()) {
                case 'Mos':
                    this.setAttribute('title','mosaicity estimate');
                    break;
                case 'Res':
                    this.setAttribute('title','resolution estimate');
                    break;
                case 'Stat':
                    this.setAttribute('title','0.6=Good & Higher=Better');
                    break;
            }
        }); //Close for $('#snaps-sort-table thead th').each(function(){
        $('#runs-sort-table thead th').each(function(){
            switch ($(this).text()) {
                case 'Res':
                    this.setAttribute('title','high resolution limit');
                    break;
                case 'Comp':
                    this.setAttribute('title','overall completeness');
                    break;
                case 'Mult':
                    this.setAttribute('title','overall multiplicity');
                    break;
                case 'Rpim':
                    this.setAttribute('title','overall precision-indicating merging R factor');
                    break;
                case 'AnomSlope':
                    this.setAttribute('title','anomalous slope');
                    break;
            }
        }); //Close for $('#runs-sort-table thead th').each(function(){


        //Contextual menus
        $('#snap_menu_in_process > div').jeegoocontext('inprocessmenu',{
                    livequery: true,
                    widthOverflowOffset: 0,
                    heightOverflowOffset: 1,
                    submenuLeftOffset: -4,
                    submenuTopOffset: -5,
                    onSelect: function(e, context){
                        alert('1');
                    }
        });

        $('#snap_menu > a').jeegoocontext('snapmenu',{
                    livequery: true,
                    widthOverflowOffset: 0,
                    heightOverflowOffset: 1,
                    submenuLeftOffset: -4,
                    submenuTopOffset: -5,
                    onSelect: function(e, context){
                        if ($(context).attr('id') > 0)
                        {
                            switch($(this).attr('id'))
                            {
                                case 'hide-this-snap':
                                    //Hide immediately in the UI
                                    $snap_menu.find('.'+$(context).attr('id')).hide('slow');
                                    //Change database entry for display as hidden
                                    $.get('hide-this-snap.php',{res_id : $(context).attr('id') });
                                    //
                                    break;

                                case 'hide-all-snaps':
                                    //Delete the entries from the DOM
                                    $snap_menu.find('.grayed').hide('slow');      
                                    //Change the database entries  for display as hidden
                                    $.get('hide-snaps.php',{datadir : my_datadir });
                                    //
                                    break;

                                case 'hide-all':
                                    //Remove the entries from the DOM
                                    $snap_menu.find('.grayed').hide('slow'); 
                                    $run_menu.find('.grayed').hide('slow'); 
                                    //Change the database entries  for display as hidden
                                    $.get('hide-snaps.php',{datadir : my_datadir });
                                    $.get('hide-runs.php',{datadir : my_datadir });
                                    //
                                    break;

                                case 'show-success-snaps':
                                    //Change the database entries for display to show
                                    $.ajax({ type: 'PUT',
                                             async: false,
                                             url:  'show_success_snaps.php',
                                             data: datadir=my_datadir })
                                    //Remove all entries in the data areas
                                    $snap_menu.children().remove();
                                    $run_menu.children().remove();
                                    //Re-load all the data
                                    lastresultID = 0;
                                    lastresultTime = 0;
                                    resultsRefresh('False');
                                    //
                                    break; 

                                case 'show-all-snaps':
                                    //Change the database entries for display to show   
                                    $.ajax({ type: 'PUT',
                                             async: false,
                                             url:   'show-snaps.php',
                                             data:  datadir=my_datadir });
                                    //Remove all entries in the data areas
                                    $snap_menu.children().remove();
                                    $run_menu.children().remove();
                                    //Re-load all the data
                                    lastresultID = 0;
                                    resultsRefresh('False'); 
                                    //
                                    break;
     
                                case 'show-all':
                                    //Change the database entries for display to show
                                    $.ajax({ type: 'PUT',
                                             async: true, 
                                             url:   'show-runs.php',
                                             data:  datadir=my_datadir });
                                    $.ajax({ type: 'PUT',
                                             async: false,
                                             url:   'show-snaps.php',
                                             data:  datadir=my_datadir });
                                    //Remove all entries in the data areas
                                    $snap_menu.children().remove();
                                    $run_menu.children().remove();
                                    //Re-load all the data
                                    lastresultID = 0;
                                    resultsRefresh('False');
                                    //
                                    break;

                                case 'snap_settings':
                                    //new-style modal dialog
                                    $dialog_generic.load("snap_settings.php",
                                        {result_id:$(context).attr('id'),
                                         start_repr:$(context).text()},
                                        function(response, status, xhr) {
                                            $(this).dialog( "option", "title", 'Settings used for '+$(context).text());
                                            $(this).dialog("option", "buttons", {});
                                            $(this).dialog("option","width",400);
                                            $(this).dialog("option","height",350);
                                            $(this).dialog('open');
                                        }
                                    );
                                    //
                                    break;

                                case 'snap_header':
                                    //new-style modal dialog
                                    $dialog_generic.load("d_header.php",
                                        {result_id:$(context).attr('id'),
                                         start_repr:$(context).text()},
                                        function(response, status, xhr) {
                                            $(this).dialog( "option", "title", $(context).text());
                                            $(this).dialog("option", "buttons", {});
                                            $dialog_generic.dialog("option","width",500);
                                            $dialog_generic.dialog("option","height",650);
                                            $(this).dialog('open');
                                        }
                                    );
                                    //
                                    break;

                                case 'snap_download_image':
                                    if (cloud_download == '1')
                                    {   
                                        //Request the download be processed
                                        $.get('get_download.php',{ datadir : my_datadir,
                                                                   id : $(context).attr('id'),
                                                                   type : 'downimage',
                                                                   ip : my_ip });
                                        //Open the dialog and remove the title bar
                                        $download_dialog.dialog('open')
                                            .parents(".ui-dialog")
                                            .find(".ui-dialog-titlebar")
                                            .remove();
                                        $download_dialog.dialog( "option", "height", "auto");
                                        waiting_for_cloud = 'True';
                                        closeDownloadDialog();
                                        downloads_active += 1;
                                    } else {
                                        alert('Sorry - downloading not currently enabled');
                                    }
                                    //
                                    break;
 
                                case 'snap_download_package':
                                    if (cloud_download == '1')
                                    {
                                        $.get('get_download.php',{ datadir : my_datadir,
                                                                   id : $(context).attr('id'),
                                                                   type : 'downpackage',
                                                                   ip : my_ip });                                    
                                        $download_dialog.dialog('open')
                                            .parents(".ui-dialog")
                                            .find(".ui-dialog-titlebar")
                                            .remove();
                                        $download_dialog.dialog( "option", "height", 'auto');
                                        waiting_for_cloud = 'True';
                                        closeDownloadDialog();
                                        downloads_active += 1;
                                    } else {
                                        alert('Sorry - downloading not currently enabled');
                                    }
                                    //
                                    break;

                                case 'snap_reprocess':
                                    if (cloud_process == '1')
                                    {
                                        //popup a dialog with the reprocessing options
                                        //Set properties of the dialog
                                        $dialog_generic.dialog( "option", "title", 'Reprocess '+$(context).text());
                                        $dialog_generic.dialog( "option", "modal", true );
                                        $dialog_generic.dialog( "option", "width", 460 );
                                        $dialog_generic.dialog( "option", "height", 530 );
                                        $dialog_generic.load("snap_reprocess.php", {result_id:$(context).attr('id'),
                                                                                         start_repr:$(context).text(),
                                                                                         type:'reprocess',
                                                                                         ip:my_ip,
                                                                                         datadir:my_datadir});
                                        $dialog_generic.dialog("option", "buttons", { 
                                          'Reprocess': function() {
                                            //Assemble the variables to be passed on
                                            var request_type = $("#form_request_type").val();
                                            var original_result_id = $("#form_original_result_id").val();
                                            var original_type = $("#form_original_type").val();
                                            var original_id = $("#form_original_id").val();
                                            var data_root_dir = $("#form_data_root_dir").val();
                                            var ip_address = $("#form_ip_address").val();
                                            var multiprocessing = $("#form_multiprocessing").val();
                                            var work_dir_override = $("#form_work_dir_override").val();
                                            var work_directory = $("#form_work_directory").val();
                                            var susceptibility = $("#form_susceptibility").val();
                                            var crystal_size_x = $("#form_crystal_size_x").val();
                                            var crystal_size_y = $("#form_crystal_size_y").val();
                                            var crystal_size_z = $("#form_crystal_size_z").val();
                                            var a = $("#form_a").val();
                                            var b = $("#form_b").val();
                                            var c = $("#form_c").val();
                                            var alpha = $("#form_alpha").val();
                                            var beta = $("#form_beta").val();
                                            var gamma = $("#form_gamma").val();
                                            var index_hi_res = $("#form_index_hi_res").val();
                                            var aimed_res = $("#form_aimed_res").val();
                                            var min_exposure_per = $("#form_min_exposure_per").val();
                                            var spacegroup = $("#form_spacegroup").val();
                                            var sample_type = $("#form_sample_type").val();
                                            var solvent_content = $("#form_solvent_content").val();
                                            var beam_flip = $("#form_beam_flip").val();
                                            var x_beam = $("#form_x_beam").val();
                                            var y_beam = $("#form_y_beam").val();
                                            var strategy_type = $("#form_strategy_type").val();
                                            var best_complexity = $("#form_best_complexity").val();
                                            var mosflm_seg = $("#form_mosflm_seg").val();
                                            var mosflm_rot = $("#form_mosflm_rot").val();
                                            var aimed_res = $("#form_aimed_res").val();
                                            var beam_size_x = $("#form_beam_size_x").val();
                                            var beam_size_y = $("#form_beam_size_y").val();
                                            var integrate = $("#form_integrate").val();
                                            var additional_image = $("#form_additional_image").val();
                                            var reference_data = $("#form_reference_data").val();
                                            //Send it off
                                            $.ajax({
                                              type: "POST",
                                              url: "add_reprocess.php",
                                              data: {request_type:request_type,
                                                     original_result_id:original_result_id,
                                                     original_type:original_type, 
                                                     original_id:original_id,
                                                     data_root_dir:data_root_dir,
                                                     ip_address:ip_address,
                                                     multiprocessing:multiprocessing,
                                                     work_dir_override:work_dir_override,
                                                     work_directory:work_directory,
                                                     susceptibility:susceptibility,
                                                     crystal_size_x:crystal_size_x,
                                                     crystal_size_y:crystal_size_y,
                                                     crystal_size_z:crystal_size_z,
                                                     a:a,
                                                     b:b,
                                                     c:c,
                                                     alpha:alpha,
                                                     beta:beta,
                                                     gamma:gamma,
                                                     index_hi_res:index_hi_res, 
                                                     aimed_res:aimed_res,
                                                     min_exposure_per:min_exposure_per,
                                                     spacegroup:spacegroup,
                                                     sample_type:sample_type,
                                                     solvent_content:solvent_content,
                                                     beam_flip:beam_flip,
                                                     x_beam:x_beam,
                                                     y_beam:y_beam, 
                                                     strategy_type:strategy_type,
                                                     best_complexity:best_complexity,
                                                     mosflm_seg:mosflm_seg,
                                                     mosflm_rot:mosflm_rot,
                                                     aimed_res:aimed_res,
                                                     beam_size_x:beam_size_x,
                                                     beam_size_y:beam_size_y,
                                                     integrate:integrate,
                                                     additional_image:additional_image,
                                                     reference_data:reference_data
                                                    }
                                            }); 
                                            $(this).dialog('close'); 
                                          },
                                          'Cancel': function() {$(this).dialog('close');} 
                                        });
                                        $dialog_generic.dialog('open'); 
                                    } else {
                                        alert('Sorry - processing not currently enabled');
                                    }
                                    //
                                    break;
                                
                                case 'snap_kappa':
                                    if (cloud_process == '1')
                                    {   
                                        //new-style modal dialog
                                        $dialog_generic.load("snap_kappa.php",
                                            {result_id:$(context).attr('id'),
                                             start_repr:$(context).text(),
                                             type:'stac',
                                             ip:my_ip},
                                            function(response, status, xhr) {
                                                $(this).dialog( "option", "title", 'Minikappa Alignment for '+$(context).text());
                                                $dialog_generic.dialog("option","width",300);
                                                $dialog_generic.dialog("option","height",250);
                                                $(this).dialog("option", "buttons", {
                                                    'Run': function() {
                                                        //alert($('#form-snap-kappa').serialize());
                                                        $.ajax({
                                                            type:"POST",
                                                            url:"add_kappa.php",
                                                            data:$('#form-snap-kappa').serialize(),
                                                            success:function(){
                                                                $dialog_generic.dialog("close");
                                                                PopupSuccessDialog("Minikappa request submitted");
                                                            },
                                                            error:function(textStatus){
                                                                $dialog_generic.dialog("close");
                                                                PopupFailureDialog("Minikappa request unsuccessful with error: "+textStatus);
                                                            }
                                                        });
                                                        $(this).dialog('close');
                                                    },
                                                    'Cancel': function() {$(this).dialog('close');}
                                                });
                                                $(this).dialog('open');
                                            }
                                        );
                                    } else {
                                        alert('Sorry - processing not currently enabled');
                                    }
                                    //
                                    break;

                            }
                        } else {
                            alert("Reload the interface - you have a browser error!");
                        }
                    }
        });

        $('#run_menu > a').jeegoocontext('runmenu', {
                    livequery: true,
                    widthOverflowOffset: 0,
                    heightOverflowOffset: 1,
                    submenuLeftOffset: -4,
                    submenuTopOffset: -5,
                    onSelect: function(e, context){
                        if ($(context).attr('id'))
                        {
                            switch($(this).attr('id'))
                            {
                                case 'hide-this-run':
                                    //Hide immediately in the UI
                                    $run_menu.find('.'+$(context).attr('id')).hide('slow'); 
                                    //Change database entry for display as hidden
                                    $.get('hide-this-run.php',{res_id : $(context).attr('id') });
                                    //
                                    break;

                                case 'hide-all-runs':
                                    //Delete the entries from the DOM
                                    $run_menu.find('.grayed').hide('slow'); 
                                    //Change the database entries  for display as hidden
                                    $.get('hide-runs.php',{datadir:my_datadir});
                                    //
                                    break;

                                case 'hide-all':
                                    //Remove the entries from the DOM
                                    $snap_menu.find('.grayed').hide('slow'); 
                                    $run_menu.find('.grayed').hide('slow'); 
                                    //Change the database entries  for display as hidden
                                    $.get('hide-snaps.php',{datadir : my_datadir });
                                    $.get('hide-runs.php',{datadir : my_datadir });
                                    //
                                    break;

                                case 'show-success-runs':
                                    //Change the database entries for display to show
                                    $.ajax({ type: 'PUT',
                                             async: false,
                                             url:  'show-success-runs.php',
                                             data: datadir=my_datadir })
                                    //Remove all entries in the data areas
                                    $snap_menu.children().remove();
                                    $run_menu.children().remove();
                                    //Re-load all the data
                                    lastresultID = 0;
                                    resultsRefresh('False');
                                    //
                                    break;

                                case 'show-all-runs':
                                    //Change the database entries for display to show
                                    $.ajax({ type: 'PUT',
                                             async: false,
                                             url:   'show-runs.php',
                                             data:  datadir=my_datadir});
                                    //Remove all entries in the data areas
                                    $snap_menu.children().remove();
                                    $run_menu.children().remove();
                                    //Re-load all the data
                                    lastresultID = 0;
                                    resultsRefresh('False');
                                    //
                                    break;

                                case 'show-all':
                                    //Change the database entries for display to show
                                    $.ajax({ type: 'PUT',
                                             async: true, 
                                             url:   'show-runs.php',
                                             data:  datadir=my_datadir});
                                    $.ajax({ type: 'PUT',
                                             async: false,
                                             url:   'show-snaps.php',
                                             data:  datadir=my_datadir});
                                    //Remove all entries in the data areas
                                    $snap_menu.children().remove();
                                    $run_menu.children().remove();
                                    //Re-load all the data
                                    lastresultID = 0;
                                    resultsRefresh('False');
                                    //
                                    break;

                                case 'run_settings':
                                    tb_show("Setings for "+$(context).text(),"d_run_settings.php?height=300&width=550&result_id="+$(context).attr('id')+"&start_repr="+$(context).text()+"&type=reprocess&ip="+my_ip);
                                    break;

                                case 'run_header':
                                    tb_show("Header information for "+$(context).text(),"d_run_header.php?height=620&width=550&result_id="+$(context).attr('id')+"&start_repr="+$(context).text());
                                    break; 

                                //Make this the reference run for inclusive strategies
                                case 'make-run-reference':
                                    //Mark the run
                                    $(context).addClass("reference");
                                    //Accumulate all the result_ids into one array
                                    var id_array = "";
                                    $(context).parent().children(".reference").each(function(){id_array = id_array.concat($(this).attr('id'));
                                                                                               id_array = id_array.concat('::');});
                                    //Update reference_data
                                    $.ajax({type: "POST",
                                            url: 'd_update_reference_data.php',
                                            data: {res_id_array:id_array,
                                                   datadir:my_datadir,
                                                   beamline:my_beamline}}); 
                                    break; 

                                //Remove this run as a reference for inclusive strategies
                                case 'remove-run-reference':
                                    $(context).removeClass("reference");
                                    //Accumulate all the result_ids into one array
                                    var id_array = "";
                                    $(context).parent().children(".reference").each(function(){id_array = id_array.concat($(this).attr('id'));
                                                                                               id_array = id_array.concat('::');});
                                    //Update reference_data
                                    $.ajax({type: "POST",
                                            url: 'd_update_reference_data.php',
                                            data: {res_id_array:id_array,
                                                   datadir:my_datadir,
                                                   beamline:my_beamline}});
                                    break;

                                //Start the Xia2 pipeline
                                case 'run-xia2':
                                    //popup a dialog with the processing options
                                    $dialog_generic.dialog( "option", "title", 'Integrate and Scale '+$(context).text()+' Using Xia2');
                                    $dialog_generic.dialog( "option", "modal", true );
                                    $dialog_generic.dialog( "option", "width", 500 );
                                    $dialog_generic.dialog( "option", "height", 200 );
                                    $dialog_generic.load("run_integrate.php", {result_id:$(context).attr('id'),
                                                                                      start_repr:$(context).text(),
                                                                                      type:'start-xiaint',
                                                                                      ip:my_ip,
                                                                                      datadir:my_datadir});
                                    $dialog_generic.dialog("option", "buttons", {
                                        'Launch': function() {
                                            var my_data = $("#myForm_integrate").serialize();
                                            //alert(my_data);
                                            //Send it off
                                            $.ajax({
                                                type: "POST",
                                                url: "add_integrate.php",
                                                data: my_data
                                            });
                                            $(this).dialog('close');
                                        },
                                        'Cancel': function() {$(this).dialog('close');}
                                    });
                                    $dialog_generic.dialog('open');
                                    
                                    break;

                                //Start the RAPD pipeline
                                case 'run-integrate':
                                    //popup a dialog with the processing options
                                    $dialog_generic.dialog( "option", "title", 'Integrate and Scale '+$(context).text()+' Using RAPD Pipeline');
                                    $dialog_generic.dialog( "option", "modal", true );
                                    $dialog_generic.dialog( "option", "width", 500 );
                                    $dialog_generic.dialog( "option", "height", 200 );
                                    $dialog_generic.load("run_integrate.php", {result_id:$(context).attr('id'),
                                                                                      start_repr:$(context).text(),
                                                                                      type:'start-fastint',
                                                                                      ip:my_ip,
                                                                                      datadir:my_datadir});
                                    $dialog_generic.dialog("option", "buttons", {
                                        'Launch': function() {
                                            var my_data = $("#myForm_integrate").serialize();
                                            //alert(my_data);
                                            //Send it off
                                            $.ajax({
                                                type: "POST",
                                                url: "add_integrate.php",
                                                data: my_data,
                                            });
                                            $(this).dialog('close');
                                        },
                                        'Cancel': function() {$(this).dialog('close');}
                                    });
                                    $dialog_generic.dialog('open');
                                    break;
								
								// Merge the dataset with another wedge
                                case 'simple-merge':
                                  if (cloud_process == '1')
                                  {
								    //popup dialog with options
								    $dialog_generic.dialog("option", "title", "Merge "+$(context).text()+" with another run")
									$dialog_generic.dialog( "option", "modal", true );
	                                $dialog_generic.dialog( "option", "width", 500 );
	                                $dialog_generic.dialog( "option", "height", 200 );
									$dialog_generic.load("merge.php",{
										result_id:$(context).attr('id'),
										start_repr:$(context).text(),
										type:"smerge",
										ip:my_ip
									});
									$dialog_generic.dialog("option", "buttons", {
                                        'Launch': function() {
                                            var my_data = $("#myForm_merge").serialize();
                                            //alert(my_data);
                                            $.ajax({
                                                type: "POST",
                                                url: "add_smerge.php",
                                                data: my_data,
                                            });
                                            $(this).dialog('close');
                                        },
                                        'Cancel': function() {$(this).dialog('close');}
                                    });
                                    $dialog_generic.dialog('open');
                                  } else {
                                      alert('Sorry - processing not currently enabled');
                                  }
                                  break;

                                //Structure solution commands
                                case 'start-sad':
                                    //alert("SAD");
                                    //popup a dialog with the reprocessing options
                                    //Set properties of the dialog
                                    $dialog_generic.dialog( "option", "title", 'Initiate SAD Structure Solution on '+$(context).text());
                                    $dialog_generic.dialog( "option", "modal", true );
                                    $dialog_generic.dialog( "option", "width", 500 );
                                    $dialog_generic.dialog( "option", "height", 400 );
                                    $dialog_generic.load("run_sad.php", {result_id:$(context).attr('id'),
                                                                                start_repr:$(context).text(),
                                                                                type:'start-sad',
                                                                                ip:my_ip,
                                                                                datadir:my_datadir});
                                    $dialog_generic.dialog("option", "buttons", {
                                        'Launch': function() {
                                            //Send it off
                                            $.ajax({
                                                type: "POST",
                                                url: "add_sad.php",
                                                data: {request_type:'start-sad',
                                                       original_result_id:$(context).attr('id'),
                                                       original_type:'integrate',
                                                       original_id:$("#form_original_id").val(),
                                                       datadir:my_datadir,
                                                       input_sca:$("#form_input_sca").val(),
                                                       input_map:'None',
                                                       ha_type:$("#form_ha_type").val(),
                                                       ha_number:$("#form_ha_number").val(),
                                                       shelxd_try:$("#form_shelxd_try").val(),
                                                       sequence:$("#form_sequence").val(),
													   sad_res:$("#form_sad_res").val(),
                                                       ip:my_ip
                                                      }
                                            });
                                            $(this).dialog('close');
                                        },
                                        'Cancel': function() {$(this).dialog('close');}
                                   });
                                   $dialog_generic.dialog('open');
                                   break; 

                                case 'start-mr':
                                    //alert("MR");
                                    //Set properties of the dialog
                                    $dialog_generic.dialog( "option", "title", 'Initiate Molecular Replacement on '+$(context).text());
                                    $dialog_generic.dialog( "option", "modal", true );
                                    $dialog_generic.dialog( "option", "width", 500 );
                                    $dialog_generic.dialog( "option", "height", 300 );
                                    $dialog_generic.load("run_mr.php", {result_id:$(context).attr('id'),
                                                                               start_repr:$(context).text(),
                                                                               type:'start-mr',
                                                                               ip:my_ip,
                                                                               user:my_user,
                                                                               datadir:my_datadir});
                                    $dialog_generic.dialog("option", "buttons", {
                                        'Launch': function() {
                                            //handle the file upload
                                            $.ajaxFileUpload({
                                              url:'./doajaxfileupload.php',
                                              secureuri:false,
                                              fileElementId:"uploaded_file",
                                              dataType:"json",
                                              beforeSend:function(){$("#loading").show();},
                            			            complete:function(){$("#loading").hide();},				
                            			            success: function (data, status)
                            	              	{
                            				            if(typeof(data.error) != 'undefined')
                            				            {
                            			                if(data.error != '')
                            			                {
                            					              alert(data.error);
                                                    //No file to upload - check for prior pdb selection
                                                    if ($("#prior_pdb").val())
                                                    {
                                                      //alert("have prior");
                                                      var my_data = $("#myForm_mr").serialize();
                                                      //send it off
                                                      $.ajax({
                                                        type: "POST",
                                                        url: "add_mr.php",
                                                        data: my_data
                                                      });
                                                    }
                                                    else if ($("#pdb_id").val())
                                                    {
                                                      //alert("HAVE ID");
                                                      var my_data = $("#myForm_mr").serialize();
                                                      //send it off
                                                      $.ajax({
                                                        type: "POST",
                                                        url: "add_mr.php",
                                                        data: my_data
                                                      });
                                                    }
                            					            }
                                                  else
						                                      {
                                                    //File has uploaded
                                                    //data.msg should be the local name of the uploaded file
                                                    var my_data = $("#myForm_mr").serialize();
                                                    my_data = my_data + "&pdb_file="+data.msg;
                                                    //send it off
                                                    $.ajax({
                                                      type: "POST",
                                                      url: "add_mr.php",
                                                      data: my_data
                                                    });
						                                      }
                                                }
				                                      },
				                                      error: function (data, status, e)
				                                      {
					                                      alert(e);
				                                      }
			                                      });
                                            $(this).dialog('close');
                                            return false;
                                        },
                                        'Cancel': function() {$(this).dialog('close');}
                                   });
                                   $dialog_generic.dialog('open');
                                   break;



                                case 'run_download_process':
                                    if (cloud_download == '1')
                                    {
                                        $.get('get_download.php',{ datadir : my_datadir,
                                                                   id : $(context).attr('id'),
                                                                   type : 'downproc',
                                                                   ip : my_ip });                                    
                                        $download_dialog.dialog('open')
                                            .parents(".ui-dialog")
                                            .find(".ui-dialog-titlebar")
                                            .remove();
                                        $download_dialog.dialog( "option", "height", 'auto');
                                        waiting_for_cloud = 'True';
                                        closeDownloadDialog();
                                        downloads_active += 1;
                                    } else {
                                        alert('Sorry - downloading not currently enabled');
                                    }
                                    //
                                    break;

                                case 'run_download_image':
                                    if (cloud_download == '1')
                                    {
                                        $.get('get_download.php',{ datadir : my_datadir,
                                                                   id : $(context).attr('id'),
                                                                   type : 'downimage',
                                                                   ip : my_ip });
                                        $download_dialog.dialog('open')
                                            .parents(".ui-dialog")
                                            .find(".ui-dialog-titlebar")
                                            .remove();
                                        $download_dialog.dialog( "option", "height", 'auto');
                                        waiting_for_cloud = 'True';
                                        closeDownloadDialog();
                                        downloads_active += 1;
                                    } else {
                                        alert('Sorry - downloading not currently enabled');
                                    }
                                    //
                                    break;

                                case 'run_download_package':
                                    if (cloud_download == '1') 
                                    {
                                        $.get('get_download.php',{ datadir : my_datadir,
                                                                   id : $(context).attr('id'),
                                                                   type : 'downpackage',
                                                                   ip : my_ip });
                                        $download_dialog.dialog('open')
                                          .parents(".ui-dialog")
                                          .find(".ui-dialog-titlebar")
                                          .remove();
                                        $download_dialog.dialog( "option", "height", 'auto');
                                        waiting_for_cloud = 'True';
                                        closeDownloadDialog();
                                        downloads_active += 1;
                                    } else {
                                        alert('Sorry - downloading not currently enabled');
                                    }
                                    //
                                    break;

                            } //end of switch
                        } else {
                            alert($(this).attr('id')+'  '+$(context).attr('id'));
                            alert("Reload the interface - you have a browser error!");
                        }
                    }
        });

        $('#run_menu_in_process > div').jeegoocontext('inprocessmenu',{
                    livequery: true,
                    widthOverflowOffset: 0,
                    heightOverflowOffset: 1,
                    submenuLeftOffset: -4,
                    submenuTopOffset: -5,
                    onSelect: function(e, context){
                        if ($(context).attr('id'))
                        {
                            switch($(this).attr('id'))
                            {
                                case 'hide-this-process':
                                    //Hide immediately in the UI
                                    $('.'+$(context).attr('id')).hide('slow');
                                    //Change database entry for display as hidden
                                    $.get('hide-this-process.php',{div_id : $(context).attr('id') });
                                    //
                                    break;
                            }
                        }
                    }
        });

        $('#sad_menu > a.noautosol').jeegoocontext('sadmenu-working', {
                    livequery: true,
                    widthOverflowOffset: 0,
                    heightOverflowOffset: 1,
                    submenuLeftOffset: -4,
                    submenuTopOffset: -5,
                    onSelect: function(e, context){
                        if ($(context).attr('id'))
                        {
                            switch($(this).attr('id'))
                            {
                                case 'shelx_download':
                                    if (cloud_download == '1')
                                    {
                                        $.get('get_download.php',{ datadir : my_datadir,
                                                                   id : $(context).attr('id'),
                                                                   type : 'downshelx',
                                                                   ip : my_ip });
                                        $download_dialog.dialog('open')
                                          .parents(".ui-dialog")
                                          .find(".ui-dialog-titlebar")
                                          .remove();
                                        $download_dialog.dialog( "option", "height", 'auto');
                                        waiting_for_cloud = 'True';
                                        closeDownloadDialog();
                                        downloads_active += 1;
                                    } else {
                                        alert('Sorry - downloading not currently enabled');
                                    }
                                    //
                                    break;
                            }
                        }
                    }
        });
 

        $('#sad_menu > a.success').jeegoocontext('sadmenu-success', {
                    livequery: true,
                    widthOverflowOffset: 0,
                    heightOverflowOffset: 1,
                    submenuLeftOffset: -4,
                    submenuTopOffset: -5,
                    onSelect: function(e, context){
                        if ($(context).attr('id'))
                        {
                            switch($(this).attr('id'))
                            {
                                case 'shelx_download':
                                    if (cloud_download == '1')
                                    {
                                        $.get('get_download.php',{ datadir : my_datadir,
                                                                   id : $(context).attr('id'),
                                                                   type : 'downshelx',
                                                                   ip : my_ip });
                                        $download_dialog.dialog('open')
                                          .parents(".ui-dialog")
                                          .find(".ui-dialog-titlebar")
                                          .remove();
                                        $download_dialog.dialog( "option", "height", 'auto');
                                        waiting_for_cloud = 'True';
                                        closeDownloadDialog();
                                        downloads_active += 1;
                                    } else {
                                        alert('Sorry - downloading not currently enabled');
                                    }
                                    //
                                    break;

                                case 'sad_download':
                                    if (cloud_download == '1') 
                                    {
                                        $.get('get_download.php',{ datadir : my_datadir,
                                                                   id : $(context).attr('id'),
                                                                   type : 'downsad',
                                                                   ip : my_ip });
                                        $download_dialog.dialog('open')
                                          .parents(".ui-dialog")
                                          .find(".ui-dialog-titlebar")
                                          .remove();
                                        $download_dialog.dialog( "option", "height", 'auto');
                                        waiting_for_cloud = 'True';
                                        closeDownloadDialog();
                                        downloads_active += 1;
                                    } else {
                                        alert('Sorry - downloading not currently enabled');
                                    }
                                    //
                                    break;
									case 'hide-this-sad':
										HideThisSadResult(context);
									break;
									case 'hide-all-sad':
										HideAllSadFailures(context);
									break;
                            }
                        }
                    }
        });
    });  //end of document ready function

function DisplaySample(my_res_id) {
    $.ajax({
    	url: "get_sample_info.php",
    	data: "res_id="+my_res_id,
    	dataType: "json",
    	success: function(response) {
    		if (!response[1] ) {
    			$("#sample-summary1-0").empty();
    			$("#sample-summary1-1").empty();
    			$("#sample-summary1-2").empty();
    			$("#sample-summary1-3").empty();
    			$("#sample-summary1-4").empty();
    			$("#sample-summary1-5").empty();
    		} else {
    			$("#sample-summary1-0").html(response[2]);
    			$("#sample-summary1-1").html(response[2]);
    			$("#sample-summary1-2").html(response[2]);
    			$("#sample-summary1-3").html(response[2]);
    			$("#sample-summary1-4").html(response[2]);
    			$("#sample-summary1-5").html(response[2]);
    		}
    	}
    });
}

function LoadSamplesTable() {
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
				    /* Ligand */ null,
				    /* Comment */ null,
				    /* Freezing Condition */ null,
				    /* Crystal Condition */ null,
				    /* Metal */ null,
				    /* Project */ null,
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
	    $("#id_hideLigand").click( function() {
			samplesTable.fnSetColumnVis(6, this.checked);
		    });
	    $("#id_hideComment").click( function() {
		samplesTable.fnSetColumnVis(7, this.checked);
	    });
	    $("#id_hideFreezeCond").click( function() {
		samplesTable.fnSetColumnVis(8, this.checked);
	    });
	    $("#id_hideCrystalCond").click( function() {
		samplesTable.fnSetColumnVis(9, this.checked);
	    });
	    $("#id_hideMetal").click( function() {
		samplesTable.fnSetColumnVis(10, this.checked);
	    });
	    $("#id_hideProject").click( function() {
		samplesTable.fnSetColumnVis(11, this.checked);
	    });
	    $("#id_hidePerson").click( function() {
		samplesTable.fnSetColumnVis(12, this.checked);
	    });
}


function HideThisSadResult(context){
//Hide immediately in the UI
    $('#sad_menu').find('#'+$(context).attr('id')).hide('slow'); 
    //Change database entry for display as hidden
    $.get('hide-this-run.php',{res_id : $(context).attr('id') });
}

function HideAllSadFailures(context){
 //Hide immediately in the UI
 $('#sad_menu').find('.failed').hide('slow');
 
}
   
//grab the IP address, etc
function GetInfoAndStart(){
   // start monitoring the status
   var timeoutID = setTimeout(statusMonitor, 5000);
   // now refresh images for 1st time
   var timeoutID1 = setTimeout(resultsRefresh, 1000);
   // update the ReferenceSet
   var timeoutID2 = setTimeout(settingsMonitor,2000);
   // start monitoring the cloud
   var timeoutID3 = setTimeout(cloudMonitor, 10000);
   // start looking for processes going
   var timeoutID4 = setTimeout(processesRefresh,5000);
   // load the samples table
   var timeoutID5 = setTimeout(LoadSamplesTable,3000);

};


//refresh the snaps and runs on the left
function resultsRefresh(again) {
    //update the snaps and runs
    var prevlastresultTime = lastresultTime;
    $.getJSON("d_get_results.php?datadir="+my_datadir+"&id="+lastresultID+"&timestamp="+lastresultTime, function(json) {
        if(json.length)
        {
            for(i=0; i < json.length-1; i=i+7)
            {
                if (json[i] == "single")
                {
                    $snap_menu_in_process.children('.in_process_'+json[2]).hide('slow');

                    if (json[i+1] != 'hide')
                    {
                        $snap_menu.prepend(json[i+3]);
                        if (json[i+4] == "FAILED")
                        {
                            $snap_menu.children(":first").removeClass("image").addClass("grayed");
                        }
                        else if (json[i+4] == "REPROCESS")
                        {
                            $snap_menu.children(":first").removeClass("image").addClass("reprocess");
                        }
                        else if (json[i+4] == "STAC")
                        {
                            $snap_menu.children(":first").removeClass("image").addClass("stac");
                        }
                        else if (json[i+4] == "REF_STRAT")
                        {
                            $snap_menu.children(":first").removeClass("image").addClass("ref_strat");
                        }

                    }
                }
                else if (json[i] == "pair")
                {
                    $snap_menu_in_process.children('.in_process_'+json[2]).hide('slow');

                    if (json[i+1] != 'hide')
                    {
                        $snap_menu.prepend(json[i+3]);
                        if (json[i+4] == "FAILED")
                        {
                            $snap_menu.children(":first").removeClass("image").addClass("grayed");
                        }
                        else if (json[i+4] == "REPROCESS")
                        {
                            $snap_menu.children(":first").removeClass("image").addClass("reprocess");
                        }
                        else if (json[i+4] == "STAC")
                        {
                            $snap_menu.children(":first").removeClass("image").addClass("stac");
                        }
                        else if (json[i+4] == "REF_STRAT")
                        {
                            $snap_menu.children(":first").removeClass("image").addClass("ref_strat");
                        }
                    }
                }
                else if (json[i] in {run:1,merge:1})
                {
					//console.log(json.slice(i,i+7));
					
					// Reload the current displayed results if they are the results displayed
					if (currentresultID == json[i+6]) {
						loadRun(json[i+6],-1,false);
					}
					
                    //hide the process-display, if it is there
                    if ($run_menu_in_process.children('.in_process_'+json[2]).length)
                    {
                        $run_menu_in_process.children('.in_process_'+json[2]).hide('slow').remove();
                    }

                    //if we are not hiding this result, display
                    if (json[i+1] != 'hide')
                    {
						var selected = $("#"+json[i+6]).hasClass('clicked');
                        if (json[i+4] == 'WORKING')
                        {
                            if ($("#"+json[i+6]).length)
                            {
                                $run_menu.children("#"+json[i+6]).replaceWith(json[i+3]);
                            }
                            else
                            {
                                $run_menu.prepend(json[i+3]);
                            }
                        }
                        else if (json[i+4] == 'SUCCESS')
                        {
                            if ($("#"+json[i+6]).length)
                            {
                                $run_menu.children("#"+json[i+6]).replaceWith(json[i+3]);
                            }
                            else
                            {
                                $run_menu.prepend(json[i+3]);
                            }
                        }
                        else if (json[i+4] == 'FINISHED')
                        {
                            if ($("#"+json[i+6]).length)
                            {
                                $run_menu.children("#"+json[i+6]).replaceWith(json[i+3]);
                            }
                            else
                            {
                                $run_menu.prepend(json[i+3]);
                            }
                        }
                        else if (json[i+4] == "FAILED")
                        {
                            if ($run_menu.children("#"+json[i+6]).length)
                            {
                                $run_menu.children("#"+json[i+6]).replaceWith(json[i+3]);
                            }
                            else
                            {
                                $run_menu.prepend(json[i+3]);
                            }
                            $run_menu.children("#"+json[i+6]).removeClass("image").addClass("grayed");
                        }
                        else if (json[i+4] == "REFASTINT")
                        {
                            if ($run_menu.children("#"+json[i+6]).length)
                            {
                                $run_menu.children("#"+json[i+6]).replaceWith(json[i+3]);
                            }
                            else
                            {
                                $run_menu.prepend(json[i+3]);
                            }
                            $run_menu.children("#"+json[i+6]).removeClass("image").addClass("reprocess");
                        }
						else if (json[i+4] == "REXIA2")
                        {
                            if ($run_menu.children("#"+json[i+6]).length)
                            {
                                $run_menu.children("#"+json[i+6]).replaceWith(json[i+3]);
                            }
                            else
                            {
                                $run_menu.prepend(json[i+3]);
                            }
                            $run_menu.children("#"+json[i+6]).removeClass("image").addClass("rexia2");
                        }
						// Make sure the result is indicated as selected
						if (selected) {
							$("#"+json[i+6]).addClass('clicked');
						}

                        //Handle this being a result we are waiting for
                        if (json[i+2] == waiting_for_run)
                        {
                            waiting_for_run = 0;
                            //alert("Loading run "+json[i+6]);
                            $snap_menu.children().removeClass("clicked");
                            $run_menu.find('a').removeClass("clicked");
                            $("#"+json[i+6]).addClass("clicked");
                            //Load the data
							currentanalysisID = 0;
                            loadRun(json[i+6],-1,false);
                        }
                    }
                }
                else if (json[i] == "sad")
                {
                    //hide the process-display
                    if ($("#sad_menu_in_process").children('.in_process_'+json[2]).length)
                    {
                        $("#sad_menu_in_process").children('.in_process_'+json[2]).hide('slow');
                    }
                    //if we are not hiding this result, display
                    if (json[i+1] != 'hide')
                    {
                        if (json[i+4] == 'WORKING')
                        {
                            if ($("#"+json[i+6]).length)
                            {
                                //Replace the current displayed html with the new
                                $("#sad_menu").children("#"+json[i+6]).replaceWith(json[i+3]);
                            }
                            else
                            {
                                //Prepend the new html to the div
                                $('#sad_menu').prepend(json[i+3]);
                            }
                        }
                        if (json[i+4] == 'SUCCESS')
                        {
                            if ($("#"+json[i+6]).length)
                            {
                                //Replace the current displayed html with the new
                                $("#sad_menu").children("#"+json[i+6]).replaceWith(json[i+3]);
                            }
                            else
                            {
                                //Prepend the new html to the div
                                $('#sad_menu').prepend(json[i+3]);
                            }
                        }
                        if (json[i+4] == 'FINISHED')
                        {
                            if ($("#"+json[i+6]).length)
                            {
                                //Replace the current displayed html with the new
                                $("#sad_menu").children("#"+json[i+6]).replaceWith(json[i+3]);
                            }
                            else
                            {
                                //Prepend the new html to the div
                                $('#sad_menu').prepend(json[i+3]);
                            }
                        }
                        if (json[i+4] == "FAILED")
                        {
                            if ($('#sad_menu').children("#"+json[i+6]).length)
                            {
                                //Replace the current displayed html with the new
                                $("#sad_menu").children("#"+json[i+6]).replaceWith(json[i+3]);
                            }
                            else
                            {
                                //Prepend the new html to the div
                                $('#sad_menu').prepend(json[i+3]);
                            }
                            $('#sad_menu').children("#"+json[i+6]).removeClass("image").addClass("grayed");
                        }
                        else if (json[i+4] == "REPROCESS")
                        {
                            if ($('#sad_menu').children("#"+json[i+6]).length)
                            {
                                $("#sad_menu").children("#"+json[i+6]).replaceWith(json[i+3]);
                            }
                            else
                            {
                                $('#sad_menu').prepend(json[i+3]);
                            }
                            $('#sad_menu').children("#"+json[i+6]).removeClass("image").addClass("reprocess");
                        }
                        //Handle this being a result we are waiting for
                        if (json[i+2] == waiting_for_sad)
                        {
                            waiting_for_sad = 0;
                            //alert("Loading sad "+json[i+6]);
                            $("#sad_menu").children().removeClass("clicked");
                            $("#mr_menu").children().removeClass("clicked");
                            $("#"+json[i+6]).addClass("clicked");
                            //Load the data
                            loadSad(json[i+6],-1,false);
                        }
                    }
                }
                else if (json[i] == "mr")
                {
                    //hide the process-display
                    if ($("#mr_menu_in_process").children('.in_process_'+json[i+2]).length)
                    {
                        $("#mr_menu_in_process").children('.in_process_'+json[i+2]).hide('slow');
                    }
                    //if we are not hiding this result, display
                    if (json[i+1] != 'hide')
                    {
                        if (json[i+4] == 'WORKING')
                        {
                            if ($("#"+json[i+6]).length)
                            {
                                //Replace the current displayed html with the new
                                $("#mr_menu").children("#"+json[i+6]).replaceWith(json[i+3]);
                            }
                            else
                            {
                                //Prepend the new html to the div
                                $('#mr_menu').prepend(json[i+3]);
                            }
                        }
                        if (json[i+4] == 'SUCCESS')
                        {
                            if ($("#"+json[i+6]).length)
                            {
                                //Replace the current displayed html with the new
                                $("#mr_menu").children("#"+json[i+6]).replaceWith(json[i+3]);
                            }
                            else
                            {
                                //Prepend the new html to the div
                                $('#mr_menu').prepend(json[i+3]);
                            }
                        }
                        if (json[i+4] == 'COMPLETE' || json[i+4] == "FAILED")
                        {
                            if ($('#mr_menu').children("#"+json[i+6]).length)
                            {
                                //Replace the current displayed html with the new
                                $("#mr_menu").children("#"+json[i+6]).replaceWith(json[i+3]);
                            }
                            else
                            {
                                //Prepend the new html to the div
                                $('#mr_menu').prepend(json[i+3]);
                            }
                            $('#mr_menu').children("#"+json[i+6]).removeClass("image").addClass("grayed");
                        }
                    }
                }
            }
            //lastresultID = json[i];
            lastresultTime = json[i];
            // Call a single refresh of the rankings
            if ( prevlastresultTime < lastresultTime )
            {
                rankingRefresh();
            }
        }

        //Don't refresh if this is a one-off call
        if (again != 'False')
        {
            //Refresh again
            my_timeout_id = setTimeout(resultsRefresh, 5000);
        }
    });
};

// Fill the ranking table
function rankingRefresh() {
    //check the ranking results
    var my_snap_rank_id = lastsnaprankID;
    $.getJSON("d_get_rankings.php?datadir="+my_datadir+"&id="+lastsnaprankID, function(json) {
        if(json.length > 1) {
            for(i=0; i < json.length-1; i=i+12) {
                snapsSortTable.fnAddData([json.slice(i,i+12)],false);
                lastsnaprankID = json[i+11];
            }
            snapsSortTable.fnDraw();
        }
    });
    var my_run_rank_id = lastrunrankID;
    $.getJSON("d_get_run_rankings.php?datadir="+my_datadir+"&id="+lastrunrankID, function(json) {
        if(json.length > 1) {
            for(i=0; i < json.length-1; i=i+14) {
                //alert(json.slice(i,i+14));
                runsSortTable.fnAddData([json.slice(i,i+14)],false);
                lastrunrankID = json[i+14];
            }
            runsSortTable.fnDraw();
        }
     });
};

//refresh the display of currently active processes
function processesRefresh(again) {
    //update the in process display
    $.getJSON("d_get_processes.php?datadir="+my_datadir, function(json) {
        if(json.length)
        {
            for(i=0; i < json.length-1; i=i+5)
            {
                if (json[i] == "single")
                {
                    if (json[i+1] == 'show')
                    {
                        // If the process is not displayed, add it
                        if (! $snap_menu_in_process.find('#'+json[i+2]).length)
                        {
                            $snap_menu_in_process.prepend(json[i+4]);
                        }
                    } 
                }
                if (json[i] == "pair")
                {
                    if (json[i+1] == 'show')
                    {
                        // If the process is not displayed, add it
                        if (! $snap_menu_in_process.find('#'+json[i+2]).length)
                        {
                            $snap_menu_in_process.prepend(json[i+4]);
                        }
                    }
                }
                if (json[i] == "integrate")
                {
                    if (json[i+1] == 'show')
                    {
                        // If the process is not displayed, add it
                        if (! $run_menu_in_process.find('#'+json[i+2]).length)
                        {
                            $run_menu_in_process.prepend(json[i+4]);
                        }
                    }
                }
                if (json[i] == "sad")
                {
                    if (json[i+1] == 'show')
                    {
                        // If the process is not displayed, add it
                        if (! $('#sad_menu_in_process').find('#'+json[i+2]).length)
                        {
                            $('#sad_menu_in_process').prepend(json[i+4]);
                        }
                    }
                }

            }
        }

        //Don't refresh if this is a one-off call
        if (again != 'False')
        {
            //Refresh again
            my_timeout_id = setTimeout(processesRefresh, 5000);
        }
    });
};

//Update the status readout
function statusMonitor() {
    $.getJSON("get_instance_info.php?datadir="+my_datadir+"&ip="+my_ip, function(json) {
      
        instance_active = json[0];
        instance_local  = json[1];

        if (instance_active == 'True')
        //This is an active directory
        {
            $('#led_button').show();	
            $.getJSON("d_get_status.php?beamline="+my_beamline, function(json) {
                my_beamline    = json[0];
                dataserver_age = json[1];
                controller_age = json[2];
                cluster_age    = json[3];

                if ( dataserver_age < 30 )
                {
                    $('#dataserver').children().first().remove();
                    $('#dataserver').prepend("<img src='css/images/LEDs/green-on-16.png'");
                } 
                else if ( dataserver_age < 60 )
                {
                    $('#dataserver').children().first().remove();
                    $('#dataserver').prepend("<img src='css/images/LEDs/yellow-on-16.png'");
                }
                else
                {
                    $('#dataserver').children().first().remove();
                    $('#dataserver').prepend("<img src='css/images/LEDs/red-on-16.png'");
                }

                if ( controller_age < 30 )
                {
                    $('#controller').children().first().remove();
                    $('#controller').prepend("<img src='css/images/LEDs/green-on-16.png'");
                }
                else if ( controller_age < 60 )
                {
                    $('#controller').children().first().remove();
                    $('#controller').prepend("<img src='css/images/LEDs/yellow-on-16.png'");
                }
                else
                {
                    $('#controller').children().first().remove();
                    $('#controller').prepend("<img src='css/images/LEDs/red-on-16.png'");
                }

                if ( cluster_age < 30 )
                {
                    $('#cluster').children().first().remove();
                    $('#cluster').prepend("<img src='css/images/LEDs/green-on-16.png'");
                }
                else if ( cluster_age < 60 )
                {
                    $('#cluster').children().first().remove();
                    $('#cluster').prepend("<img src='css/images/LEDs/yellow-on-16.png'");
                }

                else
                {
                    $('#cluster').children().first().remove();
                    $('#cluster').prepend("<img src='css/images/LEDs/red-on-16.png'");
                }

                //trigger again
                timeoutID = setTimeout(statusMonitor,30000);
            });
        }
        else
        //This is not an active directory - so update less frequently
        {
            $('#led_button').hide();
            var timeoutID = setTimeout(statusMonitor,60000);
        }
    });
};

//Look for changes in settings made by other users or load when starting
function settingsMonitor() {
  //check the current settings
  $.getJSON("d_get_settings.php?datadir="+my_datadir+"&id="+lastsettingID, function(json) {
    if(json.length > 1)
    {
      if(json[0]>0)
      {
        $('#reference_data_active').show();
      } else {
        $('#reference_data_active').hide();
      }
      $run_menu.children('.reference').removeClass('reference');
      for(i=0; i < json.length-1; i=i+1)
      {
        if(json[i] > 0)
        {
          $('#'+json[i]).addClass('reference'); 
        }
      }
      lastsettingID = json[i];
      //alert(lastsettingID);
    }
  });
  var timeoutID = setTimeout(settingsMonitor,10000);
}

//Monitor the cloud table and act on changes
function cloudMonitor() {
    //check the cloud results
    $.getJSON("d_get_cloud.php?datadir="+my_datadir+"&user="+my_user+"&trip_id="+my_trip_id+"&ip_address="+my_ip+"&id="+lastcloudID, function(json) {
        if(json.length > 1)
        {
          for(i=0; i < json.length-1; i=i+3)
          {
              if (json[i] == "download")
              {
                  //Put the file in the download iframe - triggers save dialog in the browser
                  $('#download-iframe').attr("src",json[i+1]);
                  //Mark the cloud as displayed
                  $.ajax({ async: true,
                           type:'POST', 
                           url:'mark_cloud.php',
                           data:{id:json[i+3],mark:'shown'} })
                  //One less download processing
                  downloads_active -= 1;
                  //Get rid of the waiting for downloads indicator button - if we are not waiting any more
                  if (downloads_active <= 0)
                  {
                      $('#download_active').slideToggle("slow");
                      waiting_for_cloud = 'False';
                      downloads_active = 0;
                  }
              }
              //Not getting download - we are getting an update on the cloud availability
              else
              {
                  if (json[i+1] == '0')
                  {
                      $('#snap_download_top').css('color','red');
                      $('#snap_download_image').css('color','red');
                      $('#snap_download_package').css('color','red');
                      $('#run_download_top').css('color','red');
                      $('#run_download_image').css('color','red');
                      $('#run_download_process').css('color','red');
                      $('#run_download_package').css('color','red');
                      cloud_download = '0';
                  } else {
                      $('#snap_download_top').css('color','white');
                      $('#snap_download_image').css('color','white');
                      $('#snap_download_package').css('color','white');
                      $('#run_download_top').css('color','white');
                      $('#run_download_image').css('color','white');
                      $('#run_download_process').css('color','white');
                      $('#run_download_package').css('color','white');
                      cloud_download = '1';
                  }
                  if (json[i+2] == '0')
                  {
                     $('#snap_reprocess').css('color','red');
                     $('#run_reprocess').css('color','red');
                     $('#simple-merge').css('color','red');
                     cloud_process = '0';
                  } else {
                     $('#snap_reprocess').css('color','white');
                     $('#run_reprocess').css('color','white');
                     $('#simple-merge').css('color','white');
                     cloud_process = '1';
                  }
              }
          }
          lastcloudID = 0;
        }
        //fire again - if we are expecting something - 5sec, if not - 10 sec
        if ( waiting_for_cloud == 'True' )
        {
            var my_timeout_id = setTimeout(cloudMonitor, 5000);
        }
        else
        {
            var my_timeout_id = setTimeout(cloudMonitor, 10000);
        }
    });
};

//upon click, load up the data for the snap and fill the pages
function loadSnap(my_res_id) {

  //Set the globals
  currentresultID = my_res_id;
  currentresultType = 'SNAP';

  $.getJSON("d_get_result_data.php?res_id="+my_res_id+"&datadir="+my_datadir+"&trip_id="+my_trip_id, function(json) {
    if (json.length) {
      if (json[2] == 'None')
      {
        //Summary tab
        $("#tabs0-tab0-tabs1-tab0").css("display","list-item");
//        DisplaySample(my_res_id);
        $("#summary").load(json[1]);            
        //Make sure we have a tab selected before we hide the STAC tab
        if ($('#tabs0-tab0-tabs1').tabs('option', 'selected') == 1)
        {
          $('#tabs0-tab0-tabs1').tabs().tabs('select', 0 )
        }

        //Stac tab 
        $("#stac-summary").empty(); 
        $("#tabs0-tab0-tabs1-tab1").css("display","none"); 

        //Details tab          
        $("#tabs0-tab0-tabs1-tab2").css("display","list-item");
        $("#detail").empty();
        $("#detail").load(json[3]);

        //Images tab              
        $("#tabs0-tab0-tabs1-tab3").css("display","list-item");  
        image_mode    = json[4][0];
        if (image_mode == 'OLD')
        {
          image_string  = json[4][1];
          $("#mooviewer").hide();
          $("#old_images").empty();
          $("#old_images").append(image_string);
        }
        else if (image_mode == 'NEW')
        {
          number_images = json[4][1];
          image_repr    = json[4][2];
          image_string  = json[4][3];
          if ($('#tabs0-tab0-tabs1').tabs().tabs('option', 'selected') == 3)
          {
              $("#old_images").empty();
              $("#mooviewer").show();
              load_images(number_images,image_repr,image_string);
          } else {
              image_shown = 'False';
              $("#old_images").empty();
              $("#targetframe").empty();
          }
        }

        //Plots tab
        $("#tabs0-tab0-tabs1-tab4").css("display","list-item");
        $("#plots").load(json[5]);

		//Analysis tab
		$("#tabs0-tab0-tabs1-tab5").css("display","none");

        // Snap Ranking Tab
        //$("#tabs0-tab0-tabs1-tab6").css("display","list-item");

        // Samples Info
		if (!json[10] ) {
			$(".sample-summary").empty();
		} else {
			$(".sample-summary").html(json[11]);
		} 
      }
      else
      {
        //Load the info into the minikappa page
        $("#stac-summary").load(json[2]); 
        //Show the Minikappa page
        $("#tabs0-tab0-tabs1-tab1").css("display","list-item");
        //Make sure the STAC tab is selected
        $('#tabs0-tab0-tabs1').tabs().tabs('select', 1 );
        //Hide the Summary,Details,Images and Plots tabs
        $("#tabs0-tab0-tabs1-tab0").css("display","none");
        $("#tabs0-tab0-tabs1-tab2").css("display","none");
        $("#tabs0-tab0-tabs1-tab3").css("display","none");
        $("#tabs0-tab0-tabs1-tab4").css("display","none");  
      }
    }   
  });
};

//upon click, load up the data for the run and fill the pages
function loadRun(my_res_id,my_version,auto) {
    //alert('loadRun version:'+my_version+' auto:'+auto);
    if (auto==true) 
    {
        if (my_res_id != currentresultID)
        {
            //alert("Bailing on autorefresh");
            return; 
        }
    }
    currentresultID = my_res_id;
    currentresultType = 'RUN';
    $.getJSON("d_get_result_data.php?res_id="+my_res_id+"&datadir="+my_datadir+"&trip_id="+my_trip_id, function(json) {
        if (json.length) { 
            //alert(json);
            if (my_version < json[7])
            {
                my_version = json[7];
                //Update the repr
                $("#"+my_res_id).html(json[9]);
                // Summary tab 
                $("#tabs0-tab0-tabs1-tab0").css("display","list-item");
//                DisplaySample(my_res_id);
                $('#summary').empty().load(json[1], 
                    function (responseText, textStatus, req) {
                        if (textStatus == 'error') {
                            $(this).load(json[1]);
                        }
                    }
                );
                // If focus is on STAC tab, change focus since the tab will soon disappear 
                if ($('#tabs0-tab0-tabs1').tabs('option', 'selected') == 1)
                {
                    $('#tabs0-tab0-tabs1').tabs('select', 0 )
                }
                else if ($('#tabs0-tab0-tabs1').tabs('option', 'selected') == 3)
                {
                    $('#tabs0-tab0-tabs1').tabs('select', 0 )
                }
                // Make sure the STAC display is gone
                $("#stac-summary").empty();
                $("#tabs0-tab0-tabs1-tab1").css("display","none");
                // Details tab 
                $("#tabs0-tab0-tabs1-tab2").css("display","list-item");
                $("#detail").empty().load(json[3]);
                // Load the images - none right now 
                $("#tabs0-tab0-tabs1-tab3").css("display","none");
                // Load the plots
                $("#tabs0-tab0-tabs1-tab4").css("display","list-item");
                $("#plots").empty().load(json[5]);
                //Load sample info
        		if (!json[10] ) {
        			$(".sample-summary").empty();
        		} else {
        			$(".sample-summary").html(json[11]);
        		} 
                         
            }                                  
            //Handle the status
            if (json[6] == 'WORKING')
            {
				//Make sure the analysis tab is cleared out
				$("#content_cell_summary").empty();
				$("#content_xtriage").empty();
				$("#content_plots").empty();
				$("#content_molrep").empty();
				//Look for a run result again
                //var my_tmp = setTimeout("loadRun("+my_res_id+","+my_version+",true)",5000);
            }          
            else if (json[6] in {Success:1,SUCCESS:1})  //== 'Success')
            {
                //alert(my_res_id+' '+my_version);
				//alert('Complete');
				// hide the in progress gif
                $("#"+my_res_id+"-gif").hide();
				//Show the analysis tab
				$("#tabs0-tab0-tabs1-tab5").css("display","list-item");
				// try to load the dataset analysis
				if (currentanalysisID === 0) {
					$.getJSON("d_get_analysis_data.php?res_id="+my_res_id+"&datadir="+my_datadir+"&trip_id="+my_trip_id+"&username="+my_user, function(json) {
				        if (json.length) {
							currentanalysisID = my_res_id;
							$("#content_cell_summary").empty().load(json[1]);
							$("#content_xtriage").empty().load(json[2]);
							$("#content_plots").empty().load(json[3]);
							$("#content_molrep").empty().load(json[4], function(){$("#molrep_jpg").append("<object data='"+json[5]+"' align=center type='image/jpg'></object>");});
						}
					});
				}
				// keep looking for updated results
                //var my_tmp = setTimeout("loadRun("+my_res_id+","+my_version+",true)",5000);
            } 
            else if (json[6] == 'Failed')
            {
                $("#"+my_res_id+"-gif").hide();
                //alert('Abject failure');
				//Make sure the analysis tab is cleared out
				$("#content_cell_summary").empty();
				$("#content_xtriage").empty();
				$("#content_plots").empty();
				$("#content_molrep").empty();
            }
        }
        else if (auto == 'true')
        {
            //var my_tmp = setTimeout("loadRun("+my_res_id+","+my_version+",true)",5000);
        }
    });
};

//upon click, load up the data for the sad run and fill the pages
function loadSad(my_res_id,my_version,auto) {
    //alert('loadSad version:'+my_version+' auto:'+auto);
    if (auto==true)
    {
        if (my_res_id != currentstructureresultID)
        {
            //alert("Bailing on autorefresh");
            return;
        }
    }
    currentstructureresultID = my_res_id;
    currentstructureresultType = 'SAD';
    $.getJSON("d_get_result_data.php?res_id="+my_res_id+"&datadir="+my_datadir+"&trip_id="+my_trip_id, function(json) {
        if (json.length) {
            //alert(json);
            if (my_version < json[7])
            {
                my_version = json[7];
                //Update the repr
                $("#"+my_res_id).html(json[9]);
                //ShelX results tab
                $("#shelx-results").delay(1000).empty().load(json[1],
                    function (responseText, textStatus, req) {
                        if (textStatus == "error") {
                            $("#summary").load(json[1]);
                        }
                    }
                );
                //ShelX plots tab
                $("#shelx-plots").empty().load(json[5]);
                //Autosol results tab
                $("#autosol-results").empty().load(json[3]);
            }
            //Handle the status
            if (json[6] == 'Working')
            {
                var my_tmp = setTimeout("loadSad("+my_res_id+","+my_version+",true)",5000);
            }
            else if (json[6] == 'Success')
            {
                $("#"+my_res_id+"-gif").hide();
                var my_tmp = setTimeout("loadSad("+my_res_id+","+my_version+",true)",5000);
            }
            else if (json[6] == 'Failure')
            {
                $("#"+my_res_id+"-gif").hide();
                //alert('Abject failure');
            }
        }
        else if (auto == 'true')
        {
            var my_tmp = setTimeout("loadSad("+my_res_id+","+my_version+",true)",5000);
        }
    });
};

//upon click, load up the data for the sad run and fill the pages
function loadMr(my_res_id,my_version,auto) {
    //alert('loadMr version:'+my_version+' auto:'+auto);
    if (auto==true)
    {
        if (my_res_id != currentstructureresultID)
        {
            //alert("Bailing on autorefresh");
            return;
        }
    }
    currentstructureresultID = my_res_id;
    currentstructureresultType = 'MR';
    $.getJSON("d_get_result_data.php?res_id="+my_res_id+"&datadir="+my_datadir+"&trip_id="+my_trip_id, function(json) {
        if (json.length) {
            //alert(json);
            if (my_version < json[7])
            {
                my_version = json[7];
                //Update the repr
                $("#"+my_res_id).html(json[9]);
                //ShelX results tab
                $("#shelx-results").delay(1000).empty().load(json[1],
                    function (responseText, textStatus, req) {
                        if (textStatus == "error") {
                            $("#summary").load(json[1]);
                        }
                    }
                );
            }
            //Handle the status
            if (json[6] == 'Working')
            {
                var my_tmp = setTimeout("loadMr("+my_res_id+","+my_version+",true)",5000);
            }
            else if (json[6] == 'Success')
            {
                $("#"+my_res_id+"-gif").hide();
                var my_tmp = setTimeout("loadMr("+my_res_id+","+my_version+",true)",5000);
            }
            else if (json[6] == 'Failure')
            {
                $("#"+my_res_id+"-gif").hide();
                //alert('Abject failure');
            }
        }
        else if (auto == 'true')
        {
            var my_tmp = setTimeout("loadMr("+my_res_id+","+my_version+",true)",5000);
        }
    });
};

function include(filename)
{
	var head = document.getElementsByTagName('head')[0];
	
	script = document.createElement('script');
	script.src = filename;
	script.type = 'text/javascript';
	
	head.appendChild(script)
}

function PopupSuccessDialog(message)
{
    $("#dialog-transient-success > p").html('<b>'+message+'</b>');
    $("#dialog-transient-success").show();
    $("#dialog-transient-failure").hide();
    $("#dialog-transient").dialog("option","title","Success").dialog("open");
    setTimeout(CloseTransient,3000);
}

function PopupFailureDialog(message)
{
    $("#dialog-transient-failure > p").html(message);
    $("#dialog-transient-failure").show();
    $("#dialog-transient-success").hide();
    $("#dialog-transient").dialog("option","title","Failure").dialog("open");
    setTimeout(CloseTransient,3000); 
}

function CloseTransient()
{
    $("#dialog-transient").dialog("close");
}


