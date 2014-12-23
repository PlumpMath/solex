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

    '''from math import log2, floor
    
    fart = (43000,28324,12032,6242,3023,1262,802,312,182,101)
    for i, f in enumerate(fart):
        print(floor(log2(f))-7)'''
