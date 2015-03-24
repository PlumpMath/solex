# ========================
# Solex - _build_planet.py
# ========================

# System imports.
import sys
from os import listdir

# Panda3d imports.
from panda3d.core import ConfigVariableString, Filename

# Local imports.
from etc.settings import _path
from etc.util import TimeIt
from planet_gen.model import Planet_Builder

if __name__ == "__main__":
    args = sys.argv
    if args[-1] == "all":
        args = listdir(Filename(_path.BODIES).toOsLongName())
    else:
        args = args[1:]
    pb = Planet_Builder()
    for planet_name in args:
        if planet_name.startswith("."): continue
        with TimeIt(planet_name):
            pb.build_models(planet_name)


