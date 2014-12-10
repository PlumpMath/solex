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
        
        # Terrain textures.
        for terrain in planet.terrains:
            tex_array = Texture()
            tex_array.setup2dTextureArray(2)
            for i, tex_name in enumerate(terrain['textures']):
                tex_img = PNMImage()
                tex_img.read(Filename("{}/textures/{}".format(planet.path, tex_name)))
                tex_array.load(tex_img, i, 0)
            planet.LOD_NP.setShaderInput("tex_array", tex_array)  ## temp for mono terrain
    
    def __new__(self):
        return None

