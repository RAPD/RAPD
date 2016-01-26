import os,re,time
import logging, logging.handlers
import iotbx.detectors.mar as Mar

def MarReadHeader(image,
                  mode=None,
                  run_id=None,
                  place_in_run=None,
                  logger=False):

  """
  Given a full file name for a Piltus image (as a string), read the header and
  return a dict with all the header info
  """
  # print "determine_flux %s" % image
  if logger:
    logger.debug('MarReadHeader ' % image)

  def mmorm(x):
    d = float(x)
    if (d < 2):
      return(d*1000)
    else:
      return(d)

  m = Mar.MARImage(image)
  m.read()
  print dir(m)
  print m.__dict__
  print m.parameters
  
  #m.readHeader()
  header = m.parameters
  
  
  header_items = { 'detector_sn'  : str(m.serial_number),
                   #'date'         : ("^# ([\d\-]+T[\d\.\:]+)\s*", lambda x: str(x)),
                   'pixel_size'   : float(m.pixel_size),
                   #'time'         : ("^# Exposure_time\s*([\d\.]+) s", lambda x: float(x)),
                   #'period'       : ("^# Exposure_period\s*([\d\.]+) s", lambda x: float(x)),
                   'count_cutoff' : int(m.saturation),
                   'wavelength'   : float(m.wavelength),
                   'distance'     : float(m.distance),
                   #'transmission' : ("^# Filter_transmission\s*([\d\.]+)", lambda x: float(x)),
                   'osc_start'    : float(m.osc_start),
                   'osc_range'    : float(header['OSC_RANGE']),
                   'twotheta'     : float(header['TWOTHETA']),
                   'size1'        : int(header['SIZE1']),
                   'size2'        : int(header['SIZE2']),
                   'omega_end'    : float(header['OMEGA_END']),
                   'omega_start'  : float(header['OMEGA_START']),
                   'beam_center_x': float(header['BEAM_CENTER_X']),
                   'beam_center_y': float(header['BEAM_CENTER_Y']),
                   'vendortype'   : m.vendortype,
                   
                   
                   }
                   
  print header_items
  
  try:
    #tease out the info from the file name
    #base = os.path.basename(image).rstrip(".cbf")

    parameters = {'fullname'     : image,
                  'detector'     : 'MARCCD',
                  'directory'    : os.path.dirname(image),
                  'image_prefix' : "_".join(base.split("_")[0:-2]),
                  'run_number'   : int(base.split("_")[-2]),
                  'image_number' : int(base.split("_")[-1]),
                  'axis'         : 'omega',
                  'collect_mode' : mode,
                  'run_id'       : run_id,
                  'place_in_run' : place_in_run,
                  'size1'        : 2463,
                  'size2'        : 2527}

    for label,pat in header_items.iteritems():
      # print label
      pattern = re.compile(pat[0], re.MULTILINE)
      matches = pattern.findall(header)
      if len(matches) > 0:
        parameters[label] = pat[1](matches[-1])
      else:
        parameters[label] = None

    return(parameters)

  except:
    if logger:
      logger.exception('Error reading the header for image %s' % image)
  
if __name__ == "__main__":
    """
    #testing
    #Test PilatusMonitor
    def notify(input):
        print input
    P = PilatusMonitor(beamline='C',notify=notify,reconnect=None,logger=None)
    """
    #Test the header reading
    test_image = "/gpfs6/users/necat/Jon/Programs/CCTBX_x64/modules/dials_regression/image_examples/APS_22ID/mar300.0001"
    header = MarReadHeader(test_image)
    import pprint
    P = pprint.PrettyPrinter()
    P.pprint(header)
