# =================
# Solex - shader.py
# =================

# Panda3d imports.
from panda3d.core import Shader, Material, Filename
from panda3d.core import PNMImage, Texture, RenderModeAttrib ## 
from panda3d.core import LVector2f, LVector3f, LVector4f, LVector3i
from panda3d.core import PTA_LVecBase2f, PTA_LVecBase3f, PTA_LVecBase3i

# Local imports.
from etc.settings import _path, _env


class Shader_Manager:
    
    _glsl_ver = 440
    shaders = {}
    
    @classmethod
    def set_planet_shaders(cls, planet, model_np, model_type):
        # Basic shaders.
        for shader_type in ("terrain", "sea", "atmos"):
            sub_np = model_np.find(shader_type)
            if sub_np:
                if shader_type == "atmos":
                    key = "planet_{}".format(shader_type)
                else:
                    key = "planet_{}_{}".format(shader_type, model_type)
                if key not in cls.shaders:
                    cls.shaders[key] = cls.__load_Shader(cls, key, model_type)
                sub_np.setShader(cls.shaders[key])
        
        # Shader constants.
        cls.__set_Planet_Constants(cls, planet, model_np, model_type)

    def __new__(self):
        return None

    def __load_Shader(cls, key, model_type):
        shader_stages = ["VERT", "FRAG"]
        if model_type == "high":
            shader_stages.extend(["", "TESC", "TESE"])
        
        shaders = []
        for shader_stage in shader_stages:
            if shader_stage:
                path_str = "{}/{}_{}.glsl"
                path = path_str.format(_path.SHADERS, key, shader_stage)
                shaders.append(Filename(path))
            else:
                shaders.append("")
                
        shader = Shader.load(2, *shaders)
        return shader

    def __set_Planet_Constants(cls, planet, model_np, model_type):
        # Env constants.
        model_np.setShaderInput("radius", float(planet.radius))
        model_np.setShaderInput("ambient_val", _env.AMBIENT)
        
        # Env vars.
        model_np.setShaderInput("light_vec", LVector3f(-1,0,0))
        if "atmos_colour" in planet.__dict__:
            model_np.setShaderInput("atmos_colour", LVector4f(*planet.atmos_colour))
            model_np.setShaderInput("atmos_ceiling", planet.atmos_ceiling)
            model_np.setShaderInput("atmos_radius", planet.radius+planet.atmos_ceiling)
            ## model_np.setShaderInput("atmos_vals", LVector4f(0,0,0,0))
        
        # Mid model.
        if model_type == "mid" and "colour_map" in planet.__dict__:
            col_path = "{}/maps/{}".format(planet.path, planet.colour_map.replace(".","_low."))
            model_np.setShaderInput("colour_map", loader.loadTexture(Filename(col_path)))
        
        # High Model.
        elif model_type == "high":
            # Mapping textures.
            hm_path = "{}/maps/{}".format(planet.path, planet.height_map)
            nm_path = "{}/maps/{}".format(planet.path, planet.normal_map)
            col_path = "{}/maps/{}".format(planet.path, planet.colour_map)
            ter_path = "{}/maps/{}".format(planet.path, planet.terrain_map)
            model_np.setShaderInput("height_map", loader.loadTexture(Filename(hm_path)))
            model_np.setShaderInput("normal_map", loader.loadTexture(Filename(nm_path)))
            model_np.setShaderInput("colour_map", loader.loadTexture(Filename(col_path)))
            model_np.setShaderInput("terrain_map", loader.loadTexture(Filename(ter_path)))
            
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
            
            model_np.setShaderInput("near_tex", near_tex_array)
            model_np.setShaderInput("far_tex", far_tex_array)
            
            # Env vars.
            planet.MODEL_NP.setShaderInput("cull_dist", 999999999999999999)
            ## model_np.setAttrib(RenderModeAttrib.make(2))
             
            # Terrain specs.
            min_radius = planet.radius - planet.height_min
            elev_range = planet.height_max - planet.height_min
            terrain_count = len(planet.terrains)
        
            terrain_specs = LVector4f(min_radius, elev_range, terrain_count, 0)
            model_np.setShaderInput("terrain_specs", terrain_specs)
            
            # Geom tesselation specs.
            geom_lod_list = [LVector3i(x*0,0,0) for x in range(8)]  ## lod ranges need to be un const.
            for i, (dist, inner, outer) in enumerate(planet.near_lod):
                if dist <= 4: dist *= planet.radius
                geom_lod_list[i].set(int(dist), inner, outer)
            geom_lod = PTA_LVecBase3i(geom_lod_list)
            model_np.setShaderInput("geom_lod", geom_lod)
            
            # Texture LOD.
            tex_lod_list = [LVector3f(x*0,0) for x in range(len(planet.tex_lod))]
            for i, (near, far, multi) in enumerate(planet.tex_lod):
                tex_lod_list[i].set(near, far, multi)
            tex_lod = PTA_LVecBase3f(tex_lod_list)
            model_np.setShaderInput("tex_lod", tex_lod)
            
            # Tesselation LOD.
            tess_lod_list = [LVector2f(x*0,0) for x in range(len(planet.tess_lod))]
            for i, (var_thresh, tess_max) in enumerate(planet.tess_lod):
                tess_lod_list[i].set(var_thresh, tess_max)
            tess_lod = PTA_LVecBase2f(tess_lod_list)
            model_np.setShaderInput("tess_lod", tess_lod)



