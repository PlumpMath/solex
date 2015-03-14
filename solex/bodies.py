# =================
# Solex - bodies.py
# =================

# System.
from random import random
from math import sin, cos, acos

# Panda3d.
from panda3d.core import NodePath, Filename
from panda3d.core import LVector3f, LVector3d

# Local.
from etc.settings import _path, _env
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
        self._is_far = True
    
    def _update_(self, ue, dt, body, body_pos, far_radius=_env.ATMOS_RADIUS):
        dist_from_cam = body_pos.length()
        
        # Switch modes when necessary.
        if dist_from_cam >= far_radius:
            # Far mode - planet recedes no further but shrinks to mimic
            # recession, otherwise it moves beyond cam.FAR and is culled.
            scale = far_radius / dist_from_cam
            body_pos *= scale
            body.MODEL_NP.setScale(scale)
            # Put body into "far" mode.
            if not body._is_far:
                '''if body.lod_node:
                    body.lod_node.setCenter(LPoint3f(*body_pos))'''
                body._is_far = True
        elif body._is_far and dist_from_cam < far_radius:
            # Near mode - planet moves normally.
            body.MODEL_NP.setScale(1.0)
            # Put body in "near" mode.
            '''if body.lod_node:
                body.lod_node.setCenter(LPoint3f(0,0,0))'''
            body._is_far = False
            
        self.MODEL_NP.setPos(*body_pos)
        
        
        '''if dist_from_cam < far_radius:
            cull_dist = dist_from_cam**2 - body.radius**2
            body.LOD_NP.setShaderInput("cull_dist", cull_dist)'''
        
        
    def _gen_Sphere_Model(self):
        model_path = "{}/sphere_5t.bam".format(_path.MODELS)
        model_np = loader.loadModel(model_path).getChild(0)
        model_np.setName("{}_pre_model".format(self.name))
        model = Model(model_np)
        
        # Inflate sphere model to planet radius.
        pts = model.read("vertex")
        pts = list(map(lambda pt: pt*self.radius, pts))
        model.modify("vertex", pts)
        
        # Default colour.
        r, g, b, a = self.colour
        cols = [(x*0+r,g,b,a) for x in range(len(pts))]
        model.modify("color", cols)
        
        return model_np



class Star(_Body_):
    
    def load_preview_model(self):
        self.preview_model = self._gen_Sphere_Model()
        return self.preview_model
    def load_low_model(self):
        self.MODEL_NP = self._gen_Sphere_Model()
        
    def __init__(self, recipe):
        _Body_.__init__(self, recipe)
        self.__dict__.update(recipe)
        self.SATS = []
        self.preview_model = None
        


class Planet(_Body_):
    
    # Public.
    def load_preview_model(self):
        if not self.pre_model_np:
            if self._pre_file.exists():
                self.pre_model_np = loader.loadModel(self._pre_file).getChildren()[0]
            else:
                self.pre_model_np = self._gen_Sphere_Model()
        return self.pre_model_np
    def load_low_model(self):
        if self._low_file.exists():
            loader.loadModel(self._low_file, callback=self._on_load_model)
        else:
            low_model = self._gen_Sphere_Model()
        low_model.reparentTo(self.MODEL_NP)

            
    def load_high_model(self):
        if self._high_file.exists():
            loader.loadModel(self._high_file, callback=self._on_load_model)
        else:
            self.load_low_model()
    
    # Callbacks.
    def _on_load_model(self, model_list):
        model_list[0].reparentTo(self.MODEL_NP)
                
    # Setup.    
    def __init__(self, recipe):
        _Body_.__init__(self, recipe)
        self.path = "{}/{}".format(_path.BODIES, recipe['name'])
        
        # Models.
        self._pre_file = Filename("{}/{}_pre.bam".format(self.path, recipe['name']))
        self._low_file = Filename("{}/{}_low.bam".format(self.path, recipe['name']))
        self._high_file = Filename("{}/{}_high.bam".format(self.path, recipe['name']))
        self.pre_model_np = None
        self.MODEL_NP = NodePath("model")
        



