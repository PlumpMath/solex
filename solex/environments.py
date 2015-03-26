# ================
# Solex - views.py
# ================

# System.

# Panda3d.
from panda3d.core import NodePath, Filename, Shader, LVector4f
from panda3d.core import CullFaceAttrib, TransparencyAttrib
# Local.
from etc.settings import _path, _sys, _env
from gui.gui import Lobby_Win, Pre_View_Win, Env_Win
from solex.bodies import Model
from solex.cameras import *


class Lobby:
    
    cmd_map = {'exit':"escape"}
    
    # Public.
    def to_pre_view(self, sys_name=""):
        if sys_name: self.client.init_system(sys_name)
        self.client.switch_display(self.client.PRE_VIEW)
    
    # Setup.
    def __init__(self, client):
        self.client = client
        self.NP = NodePath("lobby")
        self.NP.reparentTo(render)
        self.GUI = Lobby_Win(ctrl=self)
        self.GUI.render()
        
        self.CAMERA = Dummy_Camera(self)
        

    def _main_loop_(self, ue, dt):
        self.GUI._main_loop_(ue, dt)
        self._handle_user_events_(ue, dt)

    def _handle_user_events_(self, ue, dt):
        cmds = ue.get_cmds(self)
        if "exit" in cmds:
            print("exit")
            self.client._alive = False


class Sys_View:
    
    def on_switch(self):
        pass

class Pre_View:
    
    cmd_map = {'exit_to_lobby':"escape"}
    
    # Public.
    def on_sys_init(self, sys):
        self.GUI.update(sys)
        self.GUI.clear_labels()
        for model_np in self.__models:
            model_np.removeNode()
        self.__init_Sys(sys)
    def to_lobby(self):
        self.client.switch_display(self.client.LOBBY)
    def to_env(self, focus_id):
        self.client.switch_display(self.client.ENV)
        self.client.ENV.set_focus(focus_id)
        self.NP.stash()
    
    # Setup.
    def __init__(self, client):
        self.client = client
        self.NP = NodePath("pre_view")
        self.NP.reparentTo(render)
        self.NP.hide()
        self.SYS_NP = self.NP.attachNewNode("sys_np")
        self.BODY_NP = self.SYS_NP.attachNewNode("body_np")
        self.cam_pos_np = self.NP.attachNewNode("pre_view_cam_pos_np")
        self.__models = []
       
        self.GUI = Pre_View_Win(ctrl=self)
        self.GUI.render()
        self.GUI.NP.hide()
        self.CAMERA = Preview_Camera(self)  # <-
        
        '''light = DirectionalLight("pre_view")
        light.setColor((1, 1, 1, 1))
        dlnp = self.BODY_NP.attachNewNode(light)
        dlnp.setHpr(-90, 0, 0)
        self.BODY_NP.setLight(dlnp)'''


    def _main_loop_(self, ue, dt):
        self.GUI._main_loop_(ue, dt)
        self.CAMERA._handle_user_events_(ue, dt)
        self._handle_user_events_(ue, dt)

    def _handle_user_events_(self, ue, dt):
        cmds = ue.get_cmds(self)
        if "exit_to_lobby" in cmds:
            self.to_lobby()

    def __init_Sys(self, sys):
        w, h = (_sys.SCREEN_W, _sys.SCREEN_H)
        _tot_x = 0
        
        def place_model(body, mode, pos, p_radius, gap=1000):
            nonlocal _tot_x
            scaled_radius = body.radius * .01
            preview_model = body.load_preview_model()
            
            if body.__class__.__name__ == "Star":
                preview_model.reparentTo(self.SYS_NP)
                preview_model.setScale(.01,.001,.01)
                self.GUI.add_star_label(body)
            else:
                preview_model.reparentTo(self.BODY_NP)
                preview_model.setScale(.01)
                self.GUI.add_planet_label(body, mode)
            self.__models.append(preview_model)
                
            # Position body based on layout formula.
            x, y = ox, oy = pos
            if p_radius == 0:
                x = -scaled_radius
            else:
                if body.radius < 50: gap /= 4
                if mode == "horizontal":
                    x += p_radius + scaled_radius + gap
                    _tot_x += scaled_radius*2 + gap
                    mode = "vertical"
                else:
                    y += p_radius + scaled_radius + gap
                    mode = "horizontal"
            pos = x, y
            preview_model.setPos(x,0,-y)
            
            # Place satellites.
            _prev_radius = scaled_radius
            for _c, sat in enumerate(body.SATS):
                pos = place_model(sat, mode, pos, _prev_radius, gap/8)
                _prev_radius = sat.radius * .01
            
            # Undo progression in direction of children.
            if mode == "horizontal":
                pos = (ox, pos[1])
            else:
                pos = (pos[0], oy)
            return pos
        
        place_model(sys.root, "horizontal", [0,0], 0)
        self.CAMERA.NP.setPos(_tot_x/2,-_tot_x*1.24,0)  ## y val hacky
       

class Environment:
    
    cmd_map = {'change_cam':"c",
               'exit_to_pre_view':"escape"}
               
    # Public.
    def on_sys_init(self, sys):
        self.LIVE_OBJECTS = {}
        self.live_object_ids = set()
        self.star_sphere_np = self.__build_Star_Sphere(sys.bg_stars)
    def to_pre_view(self):
        self.client.switch_display(self.client.PRE_VIEW)
    def set_focus(self, focus_id):
        obj = self.client.SYS.OBJECT_DICT[focus_id]
        self.GUI.set_widget_text("env_win.focus_banner", obj.name.title())
        if focus_id not in self.live_object_ids:
            self.add_object(focus_id, obj)
        for cam in self.cam_list:
            cam.set_focus(obj)
    def change_camera(self):
        self.__change_Camera()
    def add_object(self, obj_id, obj):
        obj.load()
        self.live_object_ids.add(obj_id)
        self.LIVE_OBJECTS[obj_id] = obj
        obj.MODEL_NP.reparentTo(self.NP)
    def remove_object(self, obj_id, obj):
        self.live_object_ids.remove(obj_id)
        self.LIVE_OBJECTS.pop(obj_id)
        obj.unload()
    
    # Setup.
    def __init__(self ,client):
        self.client = client
        self.NP = NodePath("env")
        self.NP.reparentTo(render)
        self.NP.hide()
        self.GUI = Env_Win(ctrl=self)
        self.GUI.render()
        self.GUI.NP.hide()
        # Background.
        self.star_sphere_np = NodePath("dummy")
        self.atmos_sphere_np = self.__build_Atmos_Sphere()
        # Objects.
        self.LIVE_OBJECTS = {}
        self.live_object_ids = set()
        # Cameras.
        self.cam_list = [Orbital_Camera(self), Surface_Camera(self)]
        self.CAMERA = self.cam_list[0]
        
        
        


    
    def _main_loop_(self, ue, dt, atmos_col=LVector4f(0,0,0,0), body_dir=LVector3f(0,0,0)):
        # User events.
        self._handle_user_events_(ue, dt)
        self.CAMERA._handle_user_events_(ue, dt)
        
        # System State.
        light_vec = self.client.SYS.STARS[0].MODEL_NP.getPos()
        light_vec.normalize()
        cam = self.CAMERA
        for obj_id, obj in self.LIVE_OBJECTS.items():
            obj._update_(ue, dt, cam)
            obj.MODEL_NP.setShaderInput("light_vec", light_vec)
            
            # Atmosphere effects for bg atmos sphere.
            if obj is self.CAMERA.FOCUS and "atmos_ceiling" in obj.__dict__:
                cam_height = self.CAMERA.focus_pos.length() - obj.radius
                if cam_height < obj.atmos_ceiling:
                    # Full oppacity at 1/2 ceiling.
                    half_ceiling = obj.atmos_ceiling / 2
                    atmos_col.set(*obj.atmos_colour)
                    atmos_col *= max(min((1-(cam_height-half_ceiling)/half_ceiling),1),0)
                    # Day/night fades in/out along a band that extends
                    # around the planet along the terminator.
                    body_dir.set(*obj.render_pos)
                    body_dir.normalize()
                    night_factor = max(min(((1-(body_dir.dot(light_vec)*.5+.5))-.45)*10,1),0)
                    atmos_col *= night_factor
                else:
                    atmos_col.set(0,0,0,0)
                self.atmos_sphere_np.setShaderInput("atmos_colour", atmos_col)
                
        # Gui.
        self.GUI._main_loop_(ue, dt)

    def _handle_user_events_(self, ue, dt):
        cmds = ue.get_cmds(self)
        if "change_cam" in cmds:
            self.change_camera()
        elif "exit_to_pre_view" in cmds:
            self.to_pre_view()

    def __change_Camera(self):
        self.cam_list.reverse()
        cam = self.cam_list[0]
        old_cam = self.CAMERA
        cam.sys_pos = self.CAMERA.sys_pos
        cam.focus_pos = self.CAMERA.focus_pos
        self.CAMERA = cam
        self.client._display_region.setCamera(self.CAMERA.NP)
        self.CAMERA.switch_to(old_cam)

    def __build_Star_Sphere(self, bg_stars):
        from panda3d.core import GeomVertexWriter, GeomVertexFormat, GeomVertexData
        from panda3d.core import Geom, GeomNode, GeomPoints, AmbientLight
        self.star_sphere_np.removeNode()
        
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

        star_sphere_np.reparentTo(self.NP)
        return star_sphere_np

    def __build_Atmos_Sphere(self):
        sphere_path = "{}/sphere_simp_6.bam".format(_path.MODELS)
        atmos_model_np = loader.loadModel(sphere_path).getChild(0)
        atmos_model_np.setName("atmos")
        atmos_model = Model(atmos_model_np)
        
        pts = atmos_model.read("vertex")
        pts = list(map(lambda pt: pt*_env.ATMOS_RADIUS, pts))
        atmos_model.modify("vertex", pts)
        atmos_model.NP.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
        atmos_model.NP.setAttrib(TransparencyAttrib.make(TransparencyAttrib.MAlpha))
        
        atmos_vert_path = "{}/env_atmos_VERT.glsl".format(_path.SHADERS)
        atmos_frag_path = "{}/env_atmos_FRAG.glsl".format(_path.SHADERS)
        atmos_shader = Shader.load(Shader.SL_GLSL, atmos_vert_path, atmos_frag_path)
        atmos_model.NP.setShader(atmos_shader)
        atmos_model.NP.setShaderInput("atmos_colour", LVector4f(0,0,0,0))
        atmos_model.NP.setBin("fixed", 10)
        atmos_model.NP.reparentTo(self.NP)
        return atmos_model.NP



