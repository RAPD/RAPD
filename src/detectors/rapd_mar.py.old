<<<<<<< HEAD
import os,re,time
import logging, logging.handlers
import iotbx.detectors.mar as Mar
=======
from __future__ import division
import re,struct
from iotbx.detectors.detectorbase import DetectorImageBase

class MARImage(DetectorImageBase):
  def __init__(self,filename):
    DetectorImageBase.__init__(self,filename)
    self.vendortype = "MARCCD"

    byte_order = str(open(self.filename,"rb").read(2))
    if byte_order == 'II':
      self.endian = 0
    else:
      self.endian = 1

    assert not self.isCompressed()

  def isCompressed(self):
    if self.getEndian(): format = '>'
    else: format = '<'

    f = open(self.filename,"rb")
    try:
      f.seek(4)
      rawdata = f.read(4)
      ifd = struct.unpack(format+'i',rawdata)[0]

      # if ifd is 0 then there are no more Image File Directories
      while ifd:
        f.seek(ifd)

        rawdata = f.read(2)
        # get the number of directory entries in the IFD
        numentries = struct.unpack(format+'h',rawdata)[0]

        # search for compression tag
        for x in range(numentries):
          f.seek(ifd+x*12+2)
          rawdata = f.read(2)
          tag = struct.unpack(format+'h',rawdata)[0]
          if tag == 259: # value of compression tag
            f.seek(ifd+x*12+2+8) # seek to value offset
            # value is left justified in 4 byte field
            # read two bytes so can unpack as short
            rawdata = f.read(2)
            value = struct.unpack(format+'h',rawdata)[0]
            #print value
            if value == 1: # no compression
              return 0
            else:
              return 1

        f.seek(ifd+numentries*12+2)
        rawdata = f.read(4)
        ifd = struct.unpack(format+'i',rawdata)[0]

    finally:
      f.close()

    # control should never reach this point
    assert 1==0

  # returns 0 for little endian 'II'
  # returns 1 for big endian 'MM'
  def getEndian(self):
    return self.endian

  def readHeader(self,offset=1024):
    if not self.parameters:
      if self.getEndian(): format = '>'
      else: format = '<'

      f = open(self.filename,"rb")

      try:
        f.seek(2464) # seek to file_comments
        file_comments = f.read(512) # read file_comments

        parameters={}
        for item in [('Detector Serial Number','DETECTOR_SN')]: #expected integers
          pattern = re.compile(item[0]+' = '+r'(.*)')
          matches = pattern.findall(file_comments)
          if len(matches) > 0:
            parameters[item[1]] = int(matches[-1])
          else:
            parameters[item[1]] = 0

        f.seek(offset+28)
        rawdata = f.read(8)
        header_byte_order,data_byte_order = struct.unpack(format+'ii',rawdata)

        f.seek(offset+80)
        rawdata = f.read(8)
        parameters['SIZE1'],parameters['SIZE2'] = struct.unpack(format+'ii',rawdata)
        assert parameters['SIZE1'] == parameters['SIZE2']
        f.seek(offset+88)
        rawdata = f.read(4)
        self.depth = struct.unpack(format+'i',rawdata)[0]

        f.seek(offset+104)
        rawdata = f.read(4)
        parameters['CCD_IMAGE_SATURATION'] = struct.unpack(format+'i',rawdata)[0]

        f.seek(offset+116)
        rawdata = f.read(12)
        origin,orientation,view_direction = struct.unpack(format+'iii',rawdata)

        f.seek(offset+696)
        rawdata = f.read(4)
        start_xtal_to_detector = struct.unpack(format+'i',rawdata)[0]/1000.
        f.seek(offset+728)
        rawdata = f.read(4)
        end_xtal_to_detector = struct.unpack(format+'i',rawdata)[0]/1000.
        #assert start_xtal_to_detector == end_xtal_to_detector
        #that assertion would've been nice but ESRF BM14 frames fail; instead:
        #assert the distance is greater than zero in _read_header_asserts
        parameters['DISTANCE'] = start_xtal_to_detector

        f.seek(offset+772)
        rawdata = f.read(8)
        pixelsize_x,pixelsize_y = struct.unpack(format+'ii',rawdata)
        assert pixelsize_x == pixelsize_y
        parameters['PIXEL_SIZE'] = pixelsize_x*1.0e-6 # convert from nano to milli


        f.seek(offset+644)
        rawdata = f.read(8)
        beam_center_x,beam_center_y = struct.unpack(format+'ii',rawdata)
        parameters['BEAM_CENTER_X'] = beam_center_x/1000.*parameters['PIXEL_SIZE']
        parameters['BEAM_CENTER_Y'] = beam_center_y/1000.*parameters['PIXEL_SIZE']

        # ----- phi analysis
        f.seek(offset+684)
        rawdata = f.read(4)
        parameters['OSC_START'] = struct.unpack(format+'i',rawdata)[0]/1000.

        f.seek(offset+716)
        rawdata = f.read(4)
        end_phi = struct.unpack(format+'i',rawdata)[0]/1000.

        #parameters['OSC_RANGE'] = end_phi - parameters['OSC_START']
        #would have thought this would work; but turns out unreliable because
        # software doesn't always fill in the end_phi

        # ----- rotation analysis
        f.seek(offset+736)
        rawdata = f.read(4)
        rotation_range = struct.unpack(format+'i',rawdata)[0]/1000.
        parameters['OSC_RANGE'] = rotation_range

        f.seek(offset+732)
        rawdata = f.read(4)
        rotation_axis = struct.unpack(format+'i',rawdata)[0]
        #assert rotation_axis == 4 # if it isn't phi; go back and recode to cover all cases

        # ----- omega analysis
        f.seek(offset+672)
        rawdata = f.read(4)
        parameters['OMEGA_START'] = struct.unpack(format+'i',rawdata)[0]/1000.

        f.seek(offset+704)
        rawdata = f.read(4)
        parameters['OMEGA_END'] = struct.unpack(format+'i',rawdata)[0]/1000.

        if rotation_axis == 4: # rotation axis is phi
          pass
        elif rotation_axis == 1: # rotation about omega
          parameters['OSC_START'] = parameters['OMEGA_START']

        f.seek(offset+668)
        rawdata = f.read(4)
        start_twotheta = struct.unpack(format+'i',rawdata)[0]/1000.
        f.seek(offset+700)
        rawdata = f.read(4)
        end_twotheta = struct.unpack(format+'i',rawdata)[0]/1000.
        self._assert_matching_twothetas = start_twotheta == end_twotheta
        parameters['TWOTHETA'] = start_twotheta

        f.seek(offset+908)
        rawdata = f.read(4)
        parameters['WAVELENGTH'] = struct.unpack(format+'i',rawdata)[0]*1.0e-5 # convert from femto to angstrom
        
        f.seek(offset+656)
        rawdata = f.read(4)
        parameters['TIME'] = struct.unpack(format+'i',rawdata)[0]/1000.
        
        #Put date stamp together
        f.seek(2368)
        rawdata = f.read(32)
        mo = rawdata[:2]
        d = rawdata[2:4]
        h = rawdata[4:6]
        mi = rawdata[6:8]
        y = rawdata[8:12]
        s = rawdata[13:15]
        time = ':'.join((h,mi,s))
        date =  '-'.join((y,mo,d))
        parameters['DATE'] = 'T'.join((date,time))
        
      finally:
        f.close()

      self.parameters=parameters

      self._read_header_asserts()

  def _read_header_asserts(self):
    ''' move a couple asserts here that aren't always desireable for un-initialized data '''
    assert self.parameters['DISTANCE'] > 0
    assert self._assert_matching_twothetas

  def dataoffset(self):
    return 4096

  def integerdepth(self):
    return self.depth

import os,re,time
import logging, logging.handlers
>>>>>>> a87ce4a942c3b7eac52a2ce1570f7ed3cd661333

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

<<<<<<< HEAD
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
=======
  m = MARImage(image)
  m.read()
  header = m.parameters

  header_items = { 'detector_sn'  : str(m.serial_number),
                   'date'         : str(header['DATE']),
                   'pixel_size'   : float(m.pixel_size),
                   'time'         : float(header['TIME']),
>>>>>>> a87ce4a942c3b7eac52a2ce1570f7ed3cd661333
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
<<<<<<< HEAD
                   
                   
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
  
=======
                   }
  #try:
  #tease out the info from the file name
  #base = os.path.basename(image).rstrip(".cbf")
  base = os.path.basename(image)

  parameters = {'fullname'     : image,
                'detector'     : 'MARCCD',
                'directory'    : os.path.dirname(image),
                'image_prefix' : "_".join(base.split("_")[0:-2]),
                'run_number'   : str(base.split("_")[-2]),
                #'image_number' : int(base.split("_")[-1]),
                'image_number' : int(base.split(".")[-1]),
                'axis'         : 'omega',
                'collect_mode' : mode,
                'run_id'       : run_id,
                'place_in_run' : place_in_run,
                }
  """
  for label,pat in header_items.iteritems():
    # print label
    pattern = re.compile(pat[0], re.MULTILINE)
    matches = pattern.findall(header)
    if len(matches) > 0:
      parameters[label] = pat[1](matches[-1])
    else:
      parameters[label] = None
  """
  parameters.update(header_items)
  return(parameters)
  """
  except:
    if logger:
      logger.exception('Error reading the header for image %s' % image)
  """
>>>>>>> a87ce4a942c3b7eac52a2ce1570f7ed3cd661333
if __name__ == "__main__":
    """
    #testing
    #Test PilatusMonitor
    def notify(input):
        print input
    P = PilatusMonitor(beamline='C',notify=notify,reconnect=None,logger=None)
    """
    #Test the header reading
<<<<<<< HEAD
    test_image = "/gpfs6/users/necat/Jon/Programs/CCTBX_x64/modules/dials_regression/image_examples/APS_22ID/mar300.0001"
=======
    test_image = "/gpfs6/users/necat/Jon/Programs/CCTBX_x64/modules/dials_regression/image_examples/APS_22ID/junk_r1_1.0001"
>>>>>>> a87ce4a942c3b7eac52a2ce1570f7ed3cd661333
    header = MarReadHeader(test_image)
    import pprint
    P = pprint.PrettyPrinter()
    P.pprint(header)
