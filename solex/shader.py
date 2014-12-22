# =================
# Solex - shader.py
# =================

# Panda3d imports.
from panda3d.core import Shader, Material, Filename
from panda3d.core import LVector2f, LVector3f, LVector4f
from panda3d.core import PTA_LVecBase2f, PTA_LVecBase3f

# Local imports.
from etc.settings import _path, _env


class Shader_Manager:
    
    @classmethod
    def set_planet_shader(cls, planet):
        shader_types = ["VERT","FRAG","","TESC","TESE"]
        shaders = []
        inputs = []
        pd = planet.__dict__
        
        # Load and prepare necessary shaders.
        for shader_type in shader_types:
            if shader_type:
                shader_path = "{}/planet_{}.glsl".format(_path.SHADERS, shader_type)
                file_path = Filename(shader_path).toOsLongName()
                with open(file_path, "r") as shader_file:
                    lines = list(shader_file.readlines())
                shaders.append("".join(lines))
            else:
                shaders.append("")
        
        # Load final shader.
        shader = Shader.make(Shader.SL_GLSL, *shaders)
        planet.LOD_NP.setShader(shader)
        
        # Set shader inputs.
        planet.LOD_NP.setShaderInput("radius", float(planet.radius))
        planet.LOD_NP.setShaderInput("light_dir", LVector3f(1,0,0))
        
        # Terrain specs.
        min_radius = planet.radius - planet.height_min
        elev_range = planet.height_max - planet.height_min
        terrain_count = len(planet.terrains)

        terrain_specs = LVector4f(min_radius, elev_range, terrain_count, 0)
        planet.LOD_NP.setShaderInput("terrain_specs", terrain_specs)
        planet.LOD_NP.setShaderInput("ambient_val", _env.AMBIENT_FACTOR)
        
        # Geom tesselation specs.
        geom_lod_list = [LVector3f(x*0,0,0) for x in range(8)]
        for i, (dist, inner, outer) in enumerate(planet.near_lod):
            if dist <= 4: dist *= planet.radius
            geom_lod_list[i].set(dist, inner, outer)
        geom_lod = PTA_LVecBase3f(geom_lod_list)
        planet.LOD_NP.setShaderInput("geom_lod", geom_lod)
        
        # Texture LOD (tesselation).
        tex_lod_list = [LVector3f(x*0,0) for x in range(len(planet.tex_lod))]
        for i, (near, far, multi) in enumerate(planet.tex_lod):
            tex_lod_list[i].set(near, far, multi)
        tex_lod = PTA_LVecBase3f(tex_lod_list)
        planet.LOD_NP.setShaderInput("tex_lod", tex_lod)
        
        
    def __new__(self):
        return None


