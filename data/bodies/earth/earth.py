# -----
# Earth 
# -----

from data.bodies.templates import Terrestrial


class Earth(Terrestrial):
    radius =           6371
    height_map =       "earth_near.jpg"
    colour_map =       "earth_colour.jpg"
    normal_map =       "earth_norm.jpg"
    max_elevation =    36
    min_elevation =    -36
    terrains = (
    
        {'name':            "land",
         'textures':        ("land_near.jpg", "land_far.jpg", "land_far.jpg", "land_far.jpg"),
         'alt_range':       (0,100)},
         
    )

