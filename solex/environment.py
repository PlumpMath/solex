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


class Environment:
    
    cmd_map = {'change_cam':"c"}
    
    def load_system(self, sys_recipe, focus_name):
        self.SYS = self.__load_System(sys_recipe, focus_name)
    def unload_system(self):
        self.SYS.NP.removeNode()
        self.SYS = None
    def change_camera(self, cam_type=""):
        self.current_cam_type = self.__change_Camera(cam_type)
    
    def __init__(self, bg_stars=[]):
        self.NP = NodePath("env")
        self.NP.reparentTo(render)
        self.SYS = None
        ## self.GUI = Env_Win(ctrl=self)
        ## self.GUI.render()
        ## self.Lock = threading.Lock()
        self.CAMERA = Orbital_Camera(self)
        self.current_cam_type = "orbital"
        self.cam_list = ["orbital", "surface"]
        
        # Star sphere.
        base.setBackgroundColor(0.0, 0.0, 0.0)
        self.star_sphere_np = self.__build_Star_Sphere(bg_stars)
        self.star_sphere_np.reparentTo(self.NP)
        
        ## self._loaded = False    # If a sys is loaded.
        ## self._live = False      # If env is live and receiving server updates.
        ## self._mode = "update"

    
    def _main_loop_(self, ue, dt):
        # User events.
        self._handle_user_events_(ue)
        # Camera
        self.CAMERA._handle_user_events_(ue, dt)
        # Physics.
        self.SYS._physics_(dt)


    def _handle_user_events_(self, ue):
        cmds = ue.get_cmds(self)
        if "change_cam" in cmds:
            self.change_camera()

    def __load_System(self, sys_recipe, focus_name):
        # Remove currently loaded system first.
        if self.SYS: 
            self.unload_system()
        # Init system object.
        system = System(self, sys_recipe)
        system.NP.reparentTo(self.NP)
        
        # Set focus to body named 'focus_name'.
        focus = system.B_DICT[focus_name]
        focus.sys_pos = LVector3d(focus.aphelion,0,0)
        self.CAMERA.set_focus(focus)
        
        return system

    def __change_Camera(self, cam_type=""):
        # No 'cam_type' means just get next cam in 'self.cam_list'.
        if not cam_type:
            cci = self.cam_list.index(self.current_cam_type)    # cci -> current cam index.
            if cci == len(self.cam_list)-1:
                cam_type = self.cam_list[0]
            else:
                cam_type = self.cam_list[cci+1]
        
        # Set cam to 'cam_type'.
        Cam_Cls = eval("{}_Camera".format(cam_type.title()))
        self.CAMERA.__class__ = Cam_Cls
        self.CAMERA.switch_to()
        return cam_type

    def __build_Star_Sphere(self, bg_stars):
        from panda3d.core import GeomVertexWriter, GeomVertexFormat, GeomVertexData
        from panda3d.core import Geom, GeomNode, GeomPoints, AmbientLight
        
        # If no bg stars are given then generate them randomly.
        if not bg_stars:
            from math import cos, sin, acos
            from random import random
            radial = _env.STAR_RADIUS
            for i in range(_env.STAR_COUNT):
                u, v = random(), random()
                azm = 2*3.141598*u
                pol = acos(2*v-1)
                x = radial*cos(azm)*sin(pol)
                y = radial*sin(azm)*sin(pol)
                z = radial*cos(pol)
                bg_stars.append([x,y,z])
        
        # Fill GeomVertexData.
        vformat = GeomVertexFormat.getV3c4()
        vdata = GeomVertexData("Data", vformat, Geom.UHStatic) 
        vertices = GeomVertexWriter(vdata, "vertex")
        colours = GeomVertexWriter(vdata, "color")
        for coords in bg_stars:
            x, y, z = coords
            vertices.addData3f(x, y, z)
            colours.addData4f(1, 1, 1, 1)
            
        # Render bg stars.
        bg_stars = GeomPoints(Geom.UHStatic)
        bg_stars.addNextVertices(_env.STAR_COUNT)
        bg_stars_geom = Geom(vdata)
        bg_stars_geom.addPrimitive(bg_stars)
        star_sphere = GeomNode("star_sphere")
        star_sphere.addGeom(bg_stars_geom)
        star_sphere_np = NodePath(star_sphere)
            
        bg_star_light = AmbientLight("bg_star_light")
        bg_star_light.setColor((0.4, 0.4, 0.4, 1))
        bg_star_light_np = render.attachNewNode(bg_star_light)
        star_sphere_np.setLight(bg_star_light_np)
        return star_sphere_np


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
            
            if body.type == "planet":
                body.LOD_NP.setShaderInput("light_dir", light_dir_vec)
            
            '''# GUI.
            if body is cam.FOCUS:
                self.GUI.Dist_Banner.set_text(str(int(dist_from_cam)))'''

    def __load_System(self, sys_recipe):
        """Load the system given in recipe, return a dict mapping body
        names to body objects."""
        ClassType = type(self.__class__)
        def load_body(body_sys_recipe, parent, b_dict={}):
            """Load and init each body and its satellites."""
            Body = globals()[body_sys_recipe.type.title()]
            body_name = body_sys_recipe.__name__.lower()
            body = Body(body_name, body_sys_recipe)
            b_dict[body_name] = body
            body.NP.reparentTo(self.NP)
            parent.SATS.append(body)
                
            # Call load_body on any satellites of this body.
            for attr in list(body_sys_recipe.__dict__.values()):
                if type(attr) == ClassType:
                    b_dict = load_body(attr, body, b_dict)
            return b_dict
        
        # Step through recipe and recursively load system.
        b_dict = {}
        for attr in list(sys_recipe.__dict__.values()):
            if type(attr) == ClassType:
                b_dict = load_body(attr, self, b_dict)

        return b_dict


STAR_TYPE_DICT = {
    'G2V':{'radius':696342,'mass':1.9891*10**30,'colour':(1,.961,.925,1)}
}

class Star:
    
    def __init__(self, name, star_sys_recipe):
        self.name = name
        self.__dict__.update(star_sys_recipe.__dict__)
        self.__dict__.update(STAR_TYPE_DICT[self.cls])
        self.model_path = "{}/star.bam".format(_path.MODELS)
        
        # Nodepaths.
        self.NP = NodePath(name)
        self.MODEL_NP = loader.loadModel(Filename(self.model_path)).getChildren()[0]
        self.MODEL = Model(self.MODEL_NP)
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
        self.__dict__.update(body_sys_recipe.__dict__)
        
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
        TM.set_textures(self)
        
        # Render wireframe for crude models.
        ## if "max_elevation" not in self.__dict__:
        ## self.LOD_NP.setAttrib(RenderModeAttrib.make(2))


