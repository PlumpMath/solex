# ========================
# Solex - _build_planet.py
# ========================

# System imports.
import sys
from importlib import import_module

# Panda3d imports.
from panda3d.core import ConfigVariableString

# Local imports.
from etc.settings import _path
from planet_gen.model import Planet_Builder

if __name__ == "__main__":
    from sys import exit
    import direct.directbase.DirectStart
    base.disableMouse()
    
    planet_name = sys.argv[1].lower()
    planet_module = import_module("data.bodies.{}.{}".format(planet_name, planet_name))
    recipe = planet_module.__dict__[planet_name.title()]
    pb = Planet_Builder()
    pb.build_planet(recipe)


