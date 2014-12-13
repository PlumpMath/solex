# =====================
# Solex - planet_gen.py
# =====================

# Local imports.
from planet_gen.planet_gen import Planet_Gen

if __name__ == "__main__":
    import direct.directbase.DirectStart
    base.disableMouse()
    ## base.oobe()
    planet_gen = Planet_Gen()
    planet_gen.launch("earth")
    run()

