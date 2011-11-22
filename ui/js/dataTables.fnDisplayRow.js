$.fn.dataTableExt.oApi.fnDisplayRow = function ( oSettings, nRow )
{
	var iPos = -1;
	for( var i=0, iLen=oSettings.aiDisplay.length ; i<iLen ; i++ )
	{
		if( oSettings.aoData[ oSettings.aiDisplay[i] ].nTr == nRow )
		{
			iPos = i;
			break;
		}
	}
	
	if( iPos >= 0 )
	{
		oSettings._iDisplayStart = ( Math.floor(i / oSettings._iDisplayLength) ) * oSettings._iDisplayLength;
		this.oApi._fnCalculateEnd( oSettings );
	}
	
	this.oApi._fnDraw( oSettings );
}

