from bson import json_util
from bson.objectid import ObjectId
import json as system_json
import sys
from collections import OrderedDict

black = "\033[30m"
red = "\033[31m"
green = "\033[32m"
yellow = "\033[33m"
blue = "\033[34m"
magenta = "\033[35m"
cyan = "\033[36m"
light_gray = "\033[37m"
default = "\033[39m"
dark_gray = "\033[90m"
light_red = "\033[91m"
light_green = "\033[92m"
light_yellow = "\033[93m"
light_blue = "\033[94m"
light_magenta = "\033[95m"
light_cyan = "\033[96m"
white = "\033[97m"

info = blue
error = red
stop = "\033[0m"

main_module = sys.modules[__name__]

def color(requested_color="default"):
    return getattr(main_module, requested_color)


aring = chr(197).encode('utf-8')
deg = chr(176).encode('utf-8')

class json(object):
    """Provide methods like the systme json, but wrapped for rapd"""

    @staticmethod
    def dumps(input):
        """Just like json.dumps"""
        return system_json.dumps(input, default=json_util.default)

    @staticmethod
    def loads(input):
        """Just like json.loads"""
        # return system_json.loads(input, object_hook=json_util.object_hook, object_pairs_hook=OrderedDict)
        return system_json.loads(input, object_hook=json_util.object_hook)

if __name__ == "__main__":

    input_obj = {1:ObjectId('111111111111111111111111'),2:OrderedDict({1:'one'})}

    print("input object:", input_obj)

    d_res = json.dumps(input_obj)
    print("\ndumped string:", d_res)

    l_res = json.loads(d_res)
    print("\nloaded object:", l_res)
