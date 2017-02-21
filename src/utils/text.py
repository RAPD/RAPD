import sys

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
