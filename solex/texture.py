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
    def set_planet_textures(cls, planet):
        # Terrain map texture.
        map_img = PNMImage()
        map_img.read(Filename("{}/maps/{}".format(planet.path, planet.height_map)))
        map_tex = Texture()
        map_tex.load(map_img)
        planet.LOD_NP.setShaderInput("height_map", map_tex)
        
        # Colour map texture.
        col_img = PNMImage()
        col_img.read(Filename("{}/maps/{}".format(planet.path, planet.colour_map)))
        col_tex = Texture()
        col_tex.load(col_img)
        planet.LOD_NP.setShaderInput("col_map", col_tex)
        
        # Normal map texture.
        norm_img = PNMImage()
        norm_img.read(Filename("{}/maps/{}".format(planet.path, planet.normal_map)))
        norm_tex = Texture()
        norm_tex.load(norm_img)
        planet.LOD_NP.setShaderInput("normal_map", norm_tex)
        
        # Terrain map texture.
        ter_img = PNMImage()
        ter_img.read(Filename("{}/maps/{}".format(planet.path, planet.terrain_map)))
        ter_tex = Texture()
        ter_tex.load(ter_img)
        planet.LOD_NP.setShaderInput("terrain_map", ter_tex)
        
        # Terrain textures.
        tex_count = len(planet.terrains)
        near_tex_array = Texture()
        far_tex_array = Texture()
        near_tex_array.setup2dTextureArray(tex_count)
        far_tex_array.setup2dTextureArray(tex_count)
        for i, terrain in enumerate(planet.terrains):
            near_tex_img, far_tex_img = PNMImage(), PNMImage()
            near_tex_name, far_tex_name = terrain['textures']
            near_tex_img.read(Filename("{}/textures/{}".format(planet.path, near_tex_name)))
            far_tex_img.read(Filename("{}/textures/{}".format(planet.path, far_tex_name)))
            near_tex_array.load(near_tex_img, i, 0)
            far_tex_array.load(far_tex_img, i, 0)
        
        planet.LOD_NP.setShaderInput("near_tex", near_tex_array)
        planet.LOD_NP.setShaderInput("far_tex", far_tex_array)
    
    def __new__(self):
        return None
