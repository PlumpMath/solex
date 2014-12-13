# Default system for planet_gen.

from etc.settings import _path

class Default_System:
    
    class Sol:
        type =        "star"
        cls =         "G2V"
        aphelion =    0
        sm_axis =     0
        inclination = 0
        rotation =    0
        
        class Earth:
            type =          "planet"
            path =          _path.PLANET_GEN+"/earth"
            aphelion =      152098232
            sm_axis =       149598261
            perhilion =     147098290
            inclination =   0
            rotation =      0.1

        
    
    
    


