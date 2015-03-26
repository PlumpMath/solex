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
        self.far_radius = _env.ATMOS_RADIUS - self.radius
        self.near_radius = 0
        self._mode = "far"
        ## self._lod = "low"
        self._loaded = False
    
    def _update_(self, ue, dt, cam):
        if not self._loaded: return
        body_pos = self.sys_pos - cam.sys_pos
        dist_from_cam = body_pos.length()
        
        # Switch Far/Near modes when necessary.
        if dist_from_cam >= self.far_radius:
            # Far mode - planet recedes no further but shrinks to mimic
            # recession, otherwise it would move beyond cam.FAR and be culled.
            scale = self.far_radius / dist_from_cam
            scale *= ((self.far_radius+((1-scale)*self.radius))/self.far_radius)
            body_pos *= scale
            self.MODEL_NP.setScale(scale)
            if self._mode == "near":
                self._mode = "far"
        elif self._mode == "far" and dist_from_cam < self.far_radius:
            # Near mode - planet moves normally.
            self.MODEL_NP.setScale(1.0)
            self._mode = "near"
                
        # Update body state.
        self.MODEL_NP.setPos(*body_pos)
        self.sys_pos += (self.sys_vec*dt)
        self.render_pos = body_pos
        
        self._post_update_(dist_from_cam)
        
    def _post_update_(self, dist_from_cam):
        pass

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
        
        
    def _post_update_(self, dist_from_cam, body_pos=LVector3f(0,0,0)):
        # Switch model LOD.
        for near, far in self.__lod_list:
            if dist_from_cam >= near and dist_from_cam < far:
                if near != self.__c_near:
                    self.show_model(near)
                break

        # Shader updates.
        if dist_from_cam < self.near_radius:
            cull_dist = dist_from_cam**2 - self.radius**2
            self.MODEL_NP.setShaderInput("cull_dist", cull_dist)
            
        if "atmos_ceiling" in self.__dict__:
            # The outer 'env.atmos_sphere_np' completes its fade in at the halfway height
            # between the planet's 'sea_level' and 'atmos_ceiling' values; while the
            # inner 'atmos_np' of this planet completes its fade out at the same point.
            cam_height = dist_from_cam - self.radius
            half_ceiling = self.atmos_ceiling / 2
            atmos_np = self.current_model_np.find("atmos")
            if cam_height < half_ceiling:
                atmos_np.hide()
            else:
                atmos_np.show()
                fade_multi = 1
                if cam_height < self.atmos_ceiling:
                    fade_multi = min((cam_height-half_ceiling)/half_ceiling, 1)
                
                # Better to determine body and atmos angles here and pass them to shader,
                # rather than having them recalculated for every pixel. See 'planet_atmos_FRAG'
                # for their use.
                body_angle = abs(degrees(asin(self.radius/dist_from_cam)))
                atmos_angle = abs(degrees(asin(min((self.radius+self.atmos_ceiling)/dist_from_cam,1))))
                atmos_vals = LVector4f(dist_from_cam, fade_multi, body_angle, atmos_angle)
                self.MODEL_NP.setShaderInput("atmos_vals", atmos_vals)
                # 'body_dir' allows the 
                body_pos.set(*self.render_pos)
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
            atmos_np = model_np.find("atmos")
            if atmos_np:
                atmos_np.setBin("fixed", 20)
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
        
        self.near_radius = self.__lod_list[-1][1]

    def __Reset(self):
        self.current_model_np = None
        self.__models = {}
        self.__lod_list = []
        self.__c_near = None




