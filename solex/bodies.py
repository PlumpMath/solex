# =================
# Solex - bodies.py
# =================

# System.
from random import random
from math import sin, cos, acos

# Panda3d.
from panda3d.core import NodePath, Filename
from panda3d.core import LVector3f, LVector3d, LPoint3f

# Local.
from etc.settings import _path, _env
from etc.util import TimeIt
from planet_gen.model import Model




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
        model_path = "{}/sphere_5t.bam".format(_path.MODELS)
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
        model_file = Filename("{}/{}_pre.bam".format(self.path, self.name))
        self.pre_model_np = loader.loadModel(model_file).getChildren()[0]
        return self.pre_model_np
    def load(self):
        self.__load_Models()
    def show_model(self, index):
        if not self.current_model_np.isStashed():
            self.current_model_np.stash()
        self.current_model_np = self.__models[index]
        self.current_model_np.unstash()
        self.__lod_index = index
    def unload(self):
        self.MODEL_NP.removeNode()
        self.MODEL_NP = NodePath("model")
    
    # Callbacks.
    def _on_load_model(self, model_np, index):
        model_np.stashTo(self.MODEL_NP)
        self.__models[index] = model_np
        self.current_model_np = model_np
        if len(self.__models) == len(self.__lod_list):
            self.current_model_np.unstash()
            self._loaded = True
            self.__lod_count = len(self.__models)
            self.__lod_index = self.__lod_count-1
    
    # Setup.    
    def __init__(self, recipe):
        _Body_.__init__(self, recipe)
        self.path = "{}/{}".format(_path.BODIES, self.name)
        self.MODEL_NP = NodePath("model")
        self.current_model_np = None
        self.__models = {}
        self.__lod_index = -1
        self.__lod_list = []
        self.__lod_count = 0
        

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
        c_near, c_far = self.__lod_list[self.__lod_index]
        if dist_from_cam < c_near:
            i = self.__lod_index - 1
            while i >= 0:
                near, far = self.__lod_list[i]
                if dist_from_cam >= near and dist_from_cam < far:
                    self.show_model(i)
                    break
                i -= 1
        elif dist_from_cam > c_far:
            i = self.__lod_index + 1
            while i < self.__lod_count:
                near, far = self.__lod_list[i]
                if dist_from_cam >= near and dist_from_cam < far:
                    self.show_model(i)
                    break
                i += 1
        
        self.MODEL_NP.setPos(*body_pos)
        self.sys_pos += (self.sys_vec*dt)
        
        
        
        '''if dist_from_cam < far_radius:
            cull_dist = dist_from_cam**2 - self.radius**2
            self.LOD_NP.setShaderInput("cull_dist", cull_dist)'''
        
        
    def __load_Models(self):
        # High model.
        near = 0
        i = 0
        high_model_file = Filename("{}/{}.bam".format(self.path, self.name))
        if high_model_file.exists():
            loader.loadModel(high_model_file, callback=self._on_load_model, extraArgs=[i])
            self.__lod_count += 1
            self.__lod_list.append((0,self.near_horizon*self.radius))
            near = self.near_horizon
            i = 1
            
        # Low models.
        for rec, far in self.far_lod:
            model_file = Filename("{}/{}_{}.bam".format(self.path, self.name, rec))
            loader.loadModel(model_file, callback=self._on_load_model, extraArgs=[i])
            self.__lod_list.append((near*self.radius,far*self.radius))
            near = far
            i += 1




