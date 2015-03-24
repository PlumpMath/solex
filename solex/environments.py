# ================
# Solex - views.py
# ================

# System.

# Panda3d.
from panda3d.core import NodePath, Filename ##  DirectionalLight

# Local.
from etc.settings import _path, _sys, _env
from gui.gui import Lobby_Win, Pre_View_Win, Env_Win
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
        self.cam_list.reverse()
        cam = self.cam_list[0]
        old_cam = self.CAMERA
        cam.sys_pos = self.CAMERA.sys_pos
        cam.focus_pos = self.CAMERA.focus_pos
        self.CAMERA = cam
        self.client._display_region.setCamera(self.CAMERA.NP)
        self.CAMERA.switch_to(old_cam)
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
        self.star_sphere_np = NodePath("dummy")
        self.LIVE_OBJECTS = {}
        self.live_object_ids = set()
        self.cam_list = [Orbital_Camera(self), Surface_Camera(self)]
        self.CAMERA = self.cam_list[0]
        
        
        


    
    def _main_loop_(self, ue, dt):
        # User events.
        self._handle_user_events_(ue, dt)
        self.CAMERA._handle_user_events_(ue, dt)
        ## print(dt)
        # System State.
        light_vec = self.client.SYS.STARS[0].MODEL_NP.getPos()
        light_vec.normalize()
        cam = self.CAMERA
        for obj_id, obj in self.LIVE_OBJECTS.items():
            obj._update_(ue, dt, cam)
            obj.MODEL_NP.setShaderInput("light_vec", light_vec)
        # Gui.
        self.GUI._main_loop_(ue, dt)

    def _handle_user_events_(self, ue, dt):
        cmds = ue.get_cmds(self)
        if "change_cam" in cmds:
            self.change_camera()
        elif "exit_to_pre_view" in cmds:
            self.to_pre_view()

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
            
        bg_star_light = AmbientLight("bg_star_light")
        bg_star_light.setColor((0.4, 0.4, 0.4, 1))
        bg_star_light_np = render.attachNewNode(bg_star_light)
        star_sphere_np.setLight(bg_star_light_np)
        star_sphere_np.reparentTo(self.NP)
        return star_sphere_np



