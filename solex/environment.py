# ======================
# Solex - environment.py
# ======================

# System imports.
import threading
from ast import literal_eval

# Panda3d imports.
from panda3d.core import NodePath, Filename, RenderModeAttrib, PNMImage
from panda3d.core import LVector3f, LVector3d, LPoint3f
from panda3d.core import LVector4f

# Local imports.
from etc.settings import _path, _env
from planet_gen.model import Model
from .cameras import Orbital_Camera, Surface_Camera
from .shader import Shader_Manager as SM
from .texture import Texture_Manager as TM


class System:
    
    def __init__(self, env, sys_recipe):
        self.env = env
        self.name = sys_recipe.__class__.__name__
        self.recipe = sys_recipe
        self.NP = NodePath("{}_system".format(self.name))
        
        # Bodies.
        self.SATS = []  # root body objects.
        self.B_DICT = self.__load_System(self.recipe)
        self.BODIES = list(self.B_DICT.values())
        self.STARS = list(filter(lambda b: b.__class__.__name__ == "Star", self.BODIES))
       
    
    def _physics_(self, dt=None):
        cam = self.env.CAMERA
        far_radius = _env.ATMOS_RADIUS
        # Shader inputs.
        light_dir_vec = self.STARS[0].NP.getPos(render) / 2
        light_dir_vec.normalize()
        
        # Update pos of each body in system.
        for body in self.BODIES:
            body_pos = body.sys_pos - cam.sys_pos
            dist_from_cam = body_pos.length()
            
            # Distance and scaling.
            body.dist_from_cam = dist_from_cam
            # Switch modes when necessary.
            if dist_from_cam >= far_radius:
                # Far mode - planet recedes no further but shrinks to mimic
                # recession, otherwise it moves beyond cam.FAR and is culled.
                scale = far_radius / dist_from_cam
                body_pos *= scale
                body.MODEL_NP.setScale(scale)
                # Put body into "far" mode.
                if not body._is_far:
                    if body.lod_node:
                        body.lod_node.setCenter(LPoint3f(*body_pos))
                    body._is_far = True
            elif body._is_far and dist_from_cam < far_radius:
                # Near mode - planet moves normally.
                body.MODEL_NP.setScale(1.0)
                # Put body in "near" mode.
                if body.lod_node:
                    body.lod_node.setCenter(LPoint3f(0,0,0))
                body._is_far = False
                
            body.NP.setPos(*body_pos)
            if dist_from_cam < far_radius:
                cull_dist = dist_from_cam**2 - body.radius**2
                body.LOD_NP.setShaderInput("cull_dist", cull_dist)
            
            if body.body_type == "planet":
                body.LOD_NP.setShaderInput("light_dir", light_dir_vec)
            
            '''# GUI.
            if body is cam.FOCUS:
                self.GUI.Dist_Banner.set_text(str(int(dist_from_cam)))'''


class Star:
    
    def __init__(self, name, star_sys_recipe):
        self.name = name
        self.__dict__.update(star_sys_recipe)
        self.model_path = "{}/sphere_6.bam".format(_path.MODELS)
        
        # Nodepaths.
        self.NP = NodePath(name)
        self.MODEL_NP = loader.loadModel(Filename(self.model_path)).getChildren()[0]
        sphere = Model(self.MODEL_NP)
        pts = sphere.read("vertex")
        pts = list(map(lambda pt: pt*self.radius, pts))
        sphere.modify("vertex", pts)
        
        self.lod_node = None
        '''mod_star = Modify_Model(self.MODEL_NP)
        pts = mod_star.read("vertex")
        pts = map(lambda pt: pt*self.radius, pts)
        cols = map(lambda pt: self.colour, pts)
        mod_star.modify("vertex", pts)
        mod_star.modify("color", cols)'''

        ## self.MODEL_NP.setShader(Shader.load("shaders/star.c"))
        ## self.MODEL_NP.setShaderInput("ambient", 0.2)
        
        self.sys_pos = LVector3d(0,0,0)
        self.POS = LVector3f(0,0,0)
        self.HPR = LVector3f(0,0,0)
        self.SATS = []
        self._is_far = False
        
        

class Planet:
    
    def __init__(self, name, body_sys_recipe):
        self.name = name
        self.path = "{}/{}".format(_path.BODIES, name.lower())
        self.model_path = "{}/{}.bam".format(self.path, name.lower())
        
        # Nodepaths and LODs.
        self.NP = NodePath(name)
        self.MODEL_NP = loader.loadModel(Filename(self.model_path)).getChildren()[0]
        self.MODEL_NP.reparentTo(self.NP)
        self.LOD_NP = lod_np = self.MODEL_NP.find("far_lod")
        self.lod_node = self.LOD_NP.node()
        
        # Planet specs.
        recipe = literal_eval(self.MODEL_NP.getChild(1).getName())
        self.__dict__.update(recipe)
        self.__dict__.update(body_sys_recipe)
        
        # State.
        self.sys_pos = LVector3d(0,0,0)
        self.POS = LVector3f(0,0,0)
        self.HPR = LVector3f(0,0,0)
        self.SATS = []
        self._is_far = False
        self._has_sea = "sea_level" in self.__dict__
        self.dist_from_cam = 999999999

        # Shaders and textures.
        SM.set_planet_shader(self)
        TM.set_planet_textures(self)
        
        # Render wireframe for crude models.
        ## self.LOD_NP.setAttrib(RenderModeAttrib.make(2))


