# ==================
# Solex - cameras.py
# ==================

# Panda3d imports.
from panda3d.core import NodePath, Camera
from panda3d.core import LVector3f, LVector3d, LPoint3f

# Local imports.
from etc.settings import _cam, _sys


class _Camera_:
        
    key_map = {}
    mouse_map = {}
    
    # Public.
    def set_focus(self, obj):
        if self.FOCUS and obj is self.FOCUS: return
        self.FOCUS = obj
        self.focus_radius = obj.radius
        self.radius = self.focus_radius * 5
        self.focus_pos.set(0, self.radius-obj.radius, 0)
        obj_state = self.env.client.SIM.get_object_state(obj.name, ["sys_pos"])
        obj.sys_pos = LVector3d(*obj_state['sys_pos'])
        self.sys_pos = obj.sys_pos - self.focus_pos
        print(obj.name, obj.sys_pos)
    
    # Setup.
    def __init__(self, env):
        self.env = env
        self.cam_node = Camera(self.__class__.__name__.lower())
        self.cam_node.setScene(env.NP)
        self.NP = NodePath(self.cam_node)
        self.LENS = self.cam_node.getLens()
        self.LENS.setFar(_cam.FAR)
        self.LENS.setFov(base.camLens.getFov())
        self.FOCUS = None
        
        self.focus_pos = LVector3d(0,0,0)
        self.sys_pos = LVector3d(0,0,0)
        self.radius = 1
        self.focus_radius = 1
    


class Orbital_Camera(_Camera_):
               
    cmd_map = {'y_move':"_mouse3",
               'x_move':"_mouse1",
               'z_move':"_mouse1"}
               
    zoom_factor = .2
    move_factor = .1

    
    def switch_to(self):
        self.LENS.setViewHpr(0,0,0)

    def _handle_user_events_(self, ue, dt, delta=LVector3f()):
        if not self.FOCUS: return
        delta.set(0,0,0)
        cmds = ue.get_cmds(self)
        dist = self.focus_pos.length() - self.FOCUS.radius
        
        # Move.
        if "y_move" in cmds:
            delta.setY(-ue.y_diff*dist*self.zoom_factor)
        if "x_move" in cmds:
            delta.setX(ue.x_diff*dist*self.move_factor)
        if "z_move" in cmds:
            delta.setZ(-ue.y_diff*dist*self.move_factor)
        
        # Apply delta.
        mat = self.NP.getTransform(render).getMat()
        delta = LVector3d(*mat.xformVec(delta)) * dt
        self.focus_pos += delta
        self.sys_pos = self.FOCUS.sys_pos - self.focus_pos
        self.NP.lookAt(LPoint3f(*self.focus_pos))
        

class Surface_Camera(_Camera_):
    
    cmd_map = {'move_up':"_e",
               'move_down':"_q",
               'move_left':"_a",
               'move_right':"_d",
               'move_y':"_mouse3",
               'rotate_heading':"_mouse3",
               'rotate_pitch':"_shift-_mouse1"}
    
    _y_val = 0
    _x_val = 16
    _z_val = 16
    _h_val = 0
    _p_val = 0
    
    _y_zone = 20  # Width of move y-axis only zone.
    _rot_factor = .001
    _prev_pos = LVector3f(0,0,0)
    
    def switch_to(self):
        self._prev_pos = LVector3f(*self.focus_pos)
        self._prev_pos.normalize()
        self.NP.setP(self.NP, 90)

    def _handle_user_events_(self, ue, dt, delta=LVector3f()):
        delta.set(0,0,0)
        cmds = ue.get_cmds(self)
        
        # Y-axis movement.
        if "move_y" in cmds:
            self._y_val += ue.y_diff
            delta.setY(self._y_val)
        else:
            self._y_val = 0
        
        # X-axis movement.
        if "move_left" in cmds:
            delta.setX(self._x_val)
        if "move_right" in cmds:
            delta.setX(-self._x_val)
        
        # Z-axiz movement.
        if "move_up" in cmds:
            delta.setZ(-self._z_val)
        if "move_down" in cmds:
            delta.setZ(self._z_val)
        
        # Heading rotation.
        if "rotate_heading" in cmds:
            self._h_val += ue.x_diff * self._rot_factor
            # Only change heading if mouse moves out of "y_zone".
            _y_zone = self._y_zone * self._rot_factor
            if self._h_val > _y_zone or self._h_val < -_y_zone:
                self.NP.setH(self.NP, -(self._h_val-_y_zone))
        else:
            self._h_val = 0
            
        # Pitch rotation.
        if "rotate_pitch" in cmds:
            self._p_val += ue.y_diff * self._rot_factor * 20
        self.LENS.setViewHpr(0,-self._p_val,0)
        
        # Translate and apply delta.
        mat = self.NP.getTransform(render).getMat()
        trans_delta = LVector3d(*mat.xformVec(delta)) * dt
        self.focus_pos += trans_delta
        self.sys_pos = self.FOCUS.sys_pos - self.focus_pos
        
        # Correct tilt of camera to stay level with surface.
        delta.normalize()
        _pos = LVector3f(*self.focus_pos)
        _pos.normalize()
        deg = self._prev_pos.angleDeg(_pos)
        y_deg = deg * delta.y
        x_deg = deg * delta.x
        self.NP.setP(self.NP, y_deg)
        self.NP.setR(self.NP, -x_deg)
        self._prev_pos = _pos


        

        
class Preview_Camera(_Camera_):
    
    cmd_map = {'y_move':"_mouse3",
               'x_move':"_mouse1",
               'z_move':"_mouse1"}
    
    zoom_factor = .005
    move_factor = 1/float(_sys.SCREEN_W)
    

    def _handle_user_events_(self, ue, dt, delta=LVector3f()):
        delta.set(0,0,0)
        cmds = ue.get_cmds(self)
        dist = -self.NP.getY()
        
        # Handle mouse based movement.
        if "y_move" in cmds:
            new_y = ue.y_diff*dist*self.zoom_factor
            delta.setY(new_y)
        if "x_move" in cmds:
            delta.setX(-ue.x_diff*dist*self.move_factor)
        if "z_move" in cmds:
            delta.setZ(ue.y_diff*dist*self.move_factor)
        
        pos = self.NP.getPos() + delta
        self.NP.setPos(pos)


class Dummy_Camera(_Camera_):
    pass


