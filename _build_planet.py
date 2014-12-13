# ========================
# Solex - _build_planet.py
# ========================

# System imports.
import sys
from importlib import import_module

# Panda3d imports.
from panda3d.core import ConfigVariableString, Filename

# Local imports.
from etc.settings import _path
from planet_gen.model import Planet_Builder

if __name__ == "__main__":
    from sys import exit
    import direct.directbase.DirectStart
    base.disableMouse()
    
    planet_name = sys.argv[1].lower()
    shv_path = Filename("{}/{}/{}.shv".format(_path.PLANET_GEN, planet_name, planet_name))
    with open(shv_path.toOsLongName()) as shv_file:
        lines = shv_file.readlines()
    shiva_str = "".join(lines)
    
    pb = Planet_Builder()
    planet_np = pb.init(shiva_str)
    pb.build(planet_np)
    pb.save(planet_np, planet_name)


