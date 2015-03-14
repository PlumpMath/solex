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
    args = sys.argv[1:]
    qual = None
    if args[0] in ("preview", "low", "high"):
        qual = args.pop(0)
    if args[-1] == "all":
        args = listdir(Filename(_path.BODIES).toOsLongName())

    pb = Planet_Builder()
    if qual == "preview": build = pb.build_preview_model
    elif qual == "low": build = pb.build_low_model
    elif qual == "high": build = pb.build_high_model
    else: build = pb.build_all
    
    for planet_name in args:
        if planet_name.startswith("."): continue
        with TimeIt(planet_name):
            planet = build(planet_name)
            planet.save()


