# ===================
# Solex - settings.py
# ===================

from os import path

# Computer.
class _sys:
    SCREEN_W = 1920
    SCREEN_H = 1080

# File system.
class _path:
    solex_dir = path.dirname(path.dirname(path.abspath(__file__)))
    SOLEX = solex_dir.replace("E:", "/e").replace("\\", "/")
    BODIES = "{}/data/bodies".format(SOLEX)
    MODELS = "{}/data/models".format(SOLEX)
    SYSTEMS = "{}/data/systems".format(SOLEX)
    SHADERS = "{}/gpu/shaders".format(SOLEX)
    PLANET_GEN = "{}/planet_gen/saved".format(SOLEX)

# Physical constants.
class _phys:
    OBJ_SCALE = 0.001                   # 1 km = 1 m.
    TIME_SCALE = 1/60                   # 1 hour = 1 minute.
    G = (6.67384*10**-11)*OBJ_SCALE*TIME_SCALE # Scaled gravitaional constant.

# Environment.
class _env:
    STAR_COUNT = 15000
    STAR_RADIUS = 890000
    ATMOS_RADIUS = 800000
    AMBIENT = 0.02

# Simulator.
class _sim:
    MAX_LOCAL_BODIES = 1000
    HZ = 600

# Camera.
class _cam:
    FAR = 1000000
    
# Net.
class _net:
    BROADCAST_HZ = 6


