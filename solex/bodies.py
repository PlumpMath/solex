# =================
# Solex - bodies.py
# =================

# System.
from random import random
from math import sin, cos, asin, acos, degrees

# Panda3d.
from panda3d.core import NodePath, Filename, TransparencyAttrib ## 
from panda3d.core import LVector3f, LVector3d, LPoint3f, LVector4f

# Local.
from etc.settings import _path, _env
from etc.util import TimeIt
from planet_gen.model import Model
from solex.shader import Shader_Manager as SM




class System:
    
    def __init__(self, sys_recipe):
        self.name = sys_recipe['name']
        self.BODIES = []
        self.STARS = []
        self.OBJECT_DICT = {}
        self.root = None
        self.bg_stars = self.__generate_Bg_Stars()
    
    def __generate_Bg_Stars(self):
        bg_stars = []
        radial = _env.STAR_RADIUS
        for i in range(_env.STAR_COUNT):
            u, v = random(), random()
            azm = 2*3.141598*u
            pol = acos(2*v-1)
            x = radial*cos(azm)*sin(pol)
            y = radial*sin(azm)*sin(pol)
            z = radial*cos(pol)
            bg_stars.append([x,y,z])
            
        return bg_stars


class Body:
    
    def __new__(self, recipe):
        if recipe['type'] == "star":
            return Star(recipe)
        elif recipe['type'] == "planet":
            return Planet(recipe)

class _Body_:
    
    def __init__(self, recipe):
        self.__dict__.update(recipe)
        self.SATS = []
        self.sys_vec = LVector3d(0,0,0)
        self.sys_pos = LVector3d(0,0,0)
        self.sys_hpr = LVector3f(0,0,0)
        self.sys_rot = LVector3f(0,0,0)
        self.POS = LVector3f(0,0,0)
        self._mode = "far"
        self._lod = "low"
        self._loaded = False
    
    def _gen_Sphere_Model(self, colour=[]):
        model_path = "{}/sphere_low_5.bam".format(_path.MODELS)
        model_np = loader.loadModel(model_path).getChild(0)
        model_np.setName("{}_pre_model".format(self.name))
        model = Model(model_np)
        
        # Inflate sphere model to planet radius.
        pts = model.read("vertex")
        pts = list(map(lambda pt: pt*self.radius, pts))
        model.modify("vertex", pts)
        
        # Default colour.
        if not colour: colour = self.colour
        r, g, b, a = colour
        cols = [(x*0+r,g,b,a) for x in range(len(pts))]
        model.modify("color", cols)
        
        return model_np


class Star(_Body_):
    
    def load_preview_model(self):
        self.preview_model = self._gen_Sphere_Model()
        return self.preview_model
    def load(self):
        self.MODEL_NP = self._gen_Sphere_Model()
        
    def __init__(self, recipe):
        _Body_.__init__(self, recipe)
        self.__dict__.update(recipe)
        self.SATS = []
        self.preview_model = None
        self._has_high = False
        self._loaded = True
        

    def _update_(self, ue, dt, cam, far_radius=_env.ATMOS_RADIUS):
        if not self._loaded: return
        body_pos = self.sys_pos - cam.sys_pos
        dist_from_cam = body_pos.length()
        
        # Switch Far/Near modes when necessary.
        if dist_from_cam >= far_radius:
            # Far mode - planet recedes no further but shrinks to mimic
            # recession, otherwise it would move beyond cam.FAR and be culled.
            scale = far_radius / dist_from_cam
            body_pos *= scale
            self.MODEL_NP.setScale(scale)
            if self._mode == "near":
                self._mode = "far"
        elif self._mode == "far" and dist_from_cam < far_radius:
            # Near mode - planet moves normally.
            self.MODEL_NP.setScale(1.0)
            self._mode = "near"
                
        # Update body state.
        self.MODEL_NP.setPos(*body_pos)
        self.sys_pos += (self.sys_vec*dt)
        

        
        

class Planet(_Body_):
    
    # Public.
    def load_preview_model(self):
        p_str = "{}/{}_{}_{}.bam".format(self.path, self.name, self.preview_type, self.preview_rec)
        model_file = Filename(p_str)
        self.pre_model_np = loader.loadModel(model_file).getChildren()[0]
        SM.set_planet_shaders(self, self.pre_model_np, self.preview_type)
        self.pre_model_np.setShaderInput("light_vec", LVector3f(-1,0,0))
        self.pre_model_np.setShaderInput("atmos_vals", LVector4f(0,0,0,0))
        self.pre_model_np.setShaderInput("body_dir", LVector3f(0,1,0)) ### 
        return self.pre_model_np
    def load(self):
        self.__load_Models()
    def show_model(self, near):
        if self.current_model_np:
            self.current_model_np.stash()
        self.current_model_np = self.__models[near]
        self.current_model_np.unstash()
        self.__c_near = near
    def unload(self):
        for model_np in list(self.__models.values()):
            model_np.removeNode()
        self.__Reset()  

    # Setup.
    def __init__(self, recipe):
        _Body_.__init__(self, recipe)
        self.path = "{}/{}".format(_path.BODIES, self.name)
        self.MODEL_NP = NodePath("model")
        self.MODEL_NP.setShaderInput("atmos_vals", LVector4f(0,0,0,0))
        self.__Reset()
        
        
    def _update_(self, ue, dt, cam, far_radius=_env.ATMOS_RADIUS):
        if not self._loaded: return
        body_pos = self.sys_pos - cam.sys_pos
        dist_from_cam = body_pos.length()
        
        # Switch Far/Near modes when necessary.
        if dist_from_cam >= far_radius:
            # Far mode - planet recedes no further but shrinks to mimic
            # recession, otherwise it would move beyond cam.FAR and be culled.
            scale = far_radius / dist_from_cam
            body_pos *= scale
            self.MODEL_NP.setScale(scale)
            if self._mode == "near":
                self._mode = "far"
        elif self._mode == "far" and dist_from_cam < far_radius:
            # Near mode - planet moves normally.
            self.MODEL_NP.setScale(1.0)
            self._mode = "near"
            
        # Switch model LOD.
        for near, far in self.__lod_list:
            if dist_from_cam >= near and dist_from_cam < far:
                if near != self.__c_near:
                    self.show_model(near)
                break

        # State.
        self.MODEL_NP.setPos(*body_pos)
        self.sys_pos += (self.sys_vec*dt)
        
        # Shader updates.
        if dist_from_cam < far_radius:
            cull_dist = dist_from_cam**2 - self.radius**2
            self.MODEL_NP.setShaderInput("cull_dist", cull_dist)
        if "atmos_ceiling" in self.__dict__:
            atmos_vals = LVector4f(dist_from_cam, dist_from_cam-self.radius,
                                   abs(degrees(asin(self.radius/dist_from_cam))),
                                   abs(degrees(asin(min((self.radius+self.atmos_ceiling)/dist_from_cam,1)))))
            self.MODEL_NP.setShaderInput("atmos_vals", atmos_vals)
            body_pos.normalize()
            self.MODEL_NP.setShaderInput("body_dir", LVector3f(*body_pos))
        

    def __load_Models(self):
        
        # Async callback.
        def _on_load_model(model_np, near, model_type):
            model_np = model_np.getChildren()[0]
            ## model_np.setAttrib(TransparencyAttrib.make(TransparencyAttrib.MAlpha))  ## 
            model_np.stashTo(self.MODEL_NP)
            self.__models[near] = model_np
            SM.set_planet_shaders(self, model_np, model_type)
            if len(self.__models) == len(self.lod):
                self.show_model(near)
                self._loaded = True
        
        # Async load each model given by 'lod_models'.
        far = self.far_horizon * self.radius
        for mod_type, (near, rec) in reversed(list(zip(self.lod_models, self.lod))):
            near *= self.radius
            model_file = Filename("{}/{}_{}_{}.bam".format(self.path, self.name, mod_type, rec))
            loader.loadModel(model_file, callback=_on_load_model, extraArgs=[near, mod_type])
            self.__lod_list.append((near,far))
            far = near

    def __Reset(self):
        self.current_model_np = None
        self.__models = {}
        self.__lod_list = []
        self.__c_near = None




