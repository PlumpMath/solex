# ==================
# Solex - texture.py
# ==================

# Panda3d imports.
from panda3d.core import Texture, TextureStage
from panda3d.core import Filename, PNMImage

# Local imports.
from etc.settings import _path


class Texture_Manager:
    
    @classmethod
    def set_textures(cls, planet):
        # Terrain map texture.
        map_img = PNMImage()
        map_img.read(Filename("{}/maps/{}".format(planet.path, planet.height_map)))
        map_tex = Texture()
        map_tex.load(map_img)
        planet.LOD_NP.setShaderInput("map_tex", map_tex)
        
        # Colour map texture.
        col_img = PNMImage()
        col_img.read(Filename("{}/maps/{}".format(planet.path, planet.colour_map)))
        col_tex = Texture()
        col_tex.load(col_img)
        planet.LOD_NP.setShaderInput("col_tex", col_tex)
        
        # Normal map texture.
        norm_img = PNMImage()
        norm_img.read(Filename("{}/maps/{}".format(planet.path, planet.normal_map)))
        norm_tex = Texture()
        norm_tex.load(norm_img)
        planet.LOD_NP.setShaderInput("norm_tex", norm_tex)
        
        # Apply terrain textures.
        for i, terrain in enumerate(planet.terrains):
            tex_img = PNMImage()
            for tex_type in ("tex_near", "tex_far"):
                tex_name = terrain[tex_type]
                tex_img.read(Filename("{}/textures/{}".format(planet.path, tex_name)))
                tex = Texture()
                tex.load(tex_img)
                ## tex.setMinfilter(Texture.FTLinear)
                ## tex.setMagfilter(Texture.FTLinear)
                ## tex.setAnisotropicDegree(2)
                ts = TextureStage(str(i))
                ts.setSort(i)
                planet.LOD_NP.setTexture(ts, tex, i*10)

    def __new__(self):
        return None
