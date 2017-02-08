# Creating a new detector
RAPD needs to have a definition for your detector to properly process data. While generic detectors are available, RAPD will function best with a description of your specific detector.

The easiest case is when your detector is very similar to a detector already in RAPD. In this case, you should be able to copy the file, and modify it to suit your needs.

If you are adding a detector that is new to RAPD, you can generate a scaffold and then edit it.

### Generating a new detector
1. Use the built in scaffold generator for starting `rapd.generate_detector site_manufacturer_detectormodel.py` (ex. necat_dectris_pilatus6mf)  
2. If you have an XDS.INP file that you would like to use as a basis for XDS processing, you can use the xds_to_dict tool to make a RAPD-compatible python dict `rapd.xds_to_dict YOU_INPU_FILE`. You can copy the output of this tool into your new detector file - there is a place for it. 
