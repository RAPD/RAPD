import os, re, sys, urllib.request, urllib.error, urllib.parse

# Available DISTL servers (scyld)
_HOSTS = ['164.54.208.135']
# Available ports for DISTL
_PORTS = [8125]
# Base URL for DISTL server command
#_BASEURL = "http://%s:%d/spotfinder/distl.signal_strength?distl.image=%s&distl.bins.verbose=False&distl.res.outer=%s&distl.res.inner=%s"
_BASEURL = "http://%s:%d/spotfinder/distl.signal_strength?distl.image=%s"
# Data to parse out of results
_LOOKUPS = [('file',re.compile("\s*File \:\s*([\w\d\.\_]*)\s*", re.MULTILINE),lambda x: str(x)),
			('total_spots',re.compile("\s*Spot Total \:\s*(\d*)\s*", re.MULTILINE), lambda x: int(x)),
			('remove_ice_spots',re.compile("\s*Remove Ice \:\s*(\d*)\s*", re.MULTILINE), lambda x: int(x)),
			('in_res_spots',re.compile("\s*In-Resolution Total \:\s*(\d*)\s*", re.MULTILINE), lambda x: int(x)),
			('good_b_spots',re.compile("\s*Good Bragg Candidates \:\s*(\d*)\s*", re.MULTILINE), lambda x: int(x)),
			('ice_rings',re.compile("\s*Ice Rings \:\s*([\d\.]*)\s*", re.MULTILINE), lambda x: float(x)),
			('resolution_1',re.compile("\s*Method 1 Resolution \:\s*([\d\.]*)\s*", re.MULTILINE), lambda x: float(x)),
			('resolution_2',re.compile("\s*Method 2 Resolution \:\s*([\d\.]*)\s*", re.MULTILINE), lambda x: float(x)),
			('max_cell',re.compile("\s*Maximum unit cell \:\s*([\d\.]*)\s*", re.MULTILINE), lambda x: float(x)),
			('eccentricity',re.compile("\s*<Spot model eccentricity> \:\s*([\d\.]*)\s*", re.MULTILINE), lambda x: float(x)),
			('saturation_50',re.compile("\s*\%Saturation\, Top 50 Peaks \:\s*([\d\.]*)\s*", re.MULTILINE), lambda x: float(x)),
			('overloads',re.compile("\s*In-Resolution Ovrld Spots \:\s*(\d*)\s*", re.MULTILINE), lambda x: int(x)),
			('total_signal',re.compile("\s*Total integrated signal, pixel-ADC units above local background \(just the good Bragg candidates\)\s*([\d\.]*)\s*", re.MULTILINE), lambda x: float(x)),
			('signal_min',re.compile("\s*Signals range from ([\d\.]*)\s*", re.MULTILINE), lambda x: float(x)),
			('signal_max',re.compile("\s*Signals range from [\d\.]* to ([\d\.]*)\s*", re.MULTILINE), lambda x: float(x)),
			('signal_mean',re.compile("\s*Signals range from [\d\.]* to [\d\.]* with mean integrated signal ([\d\.]*)\s*", re.MULTILINE), lambda x: float(x)),
			('saturation_min',re.compile("\s*Saturations range from ([\d\.]*)\%\s*", re.MULTILINE), lambda x: float(x)),
			('saturation_max',re.compile("\s*Saturations range from [\d\.]*\% to ([\d\.]*)\%\s*", re.MULTILINE), lambda x: float(x)),
			('saturation_mean',re.compile("\s*Saturations range from [\d\.]*% to [\d\.]*% with mean saturation ([\d\.]*)%\s*", re.MULTILINE), lambda x: float(x))]
			

def run_distl(image):
  command = _BASEURL%(_HOSTS[0],_PORTS[0],image)
  Response = urllib.request.urlopen(command)
  raw = Response.read()
  Response.close()
  print(raw)

def main():
  import argparse
  #Parse the command line for commands.
  parser = argparse.ArgumentParser(description='Get Distl results')
  parser.add_argument('inp' ,nargs='*', type=str, help='image_path')
  args = vars(parser.parse_args())
  if len(args['inp']) == 0:
    image = input('image path?: ')
  else:
    image = args['inp'][0]
  run_distl(image)
  
if __name__ == '__main__':
  main()
