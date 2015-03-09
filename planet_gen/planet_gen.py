# =====================
# Solex - planet_gen.py
# =====================

# System imports.
from sys import exit

# Panda3d imports.
from panda3d.core import ClockObject, RenderModeAttrib
from panda3d.core import LVector3f, LVector3d, LPoint3f

# Local imports.
from etc.settings import _path
from etc.shiva import Shiva_Compiler as SI
from gui.ueh import Default_UEH
from solex.environment import Environment


class Planet_Gen:
    
    cmd_map = {'exit':"escape"}
    
    def launch(self, focus_name):
        self._alive = True
        self.UEH = Default_UEH()
        self.ENV = Environment()
        sys_recipe = SI.compile_sys_recipe("{}/_default.shv".format(_path.SYSTEMS))
        self.ENV.load_system(sys_recipe, focus_name)
        taskMgr.add(self._main_loop_, "main_loop", appendTask=True, sort=0)
        
    
    def __init__(self):
        self.Clock = ClockObject.getGlobalClock()
        self.UEH = None
        self.ENV = None
        self._alive = False
        self._prev_t = 0
        
        
    def _main_loop_(self, task):
        # Get 'dt' - time lapsed since last frame.
        new_t = self.Clock.getRealTime()
        dt = new_t - self._prev_t
        # User events.
        ue = self.UEH._get_events_()  # <-
        self._handle_user_events_(ue)  # <-
        # GUI.
        ## self.GUI._main_loop_(ue)  ## <-
        # Env.
        self.ENV._main_loop_(ue, dt)
        
        
        # Continue or exit loop based on status of
        # "_alive" (set in _handle_user_events_).
        self._prev_t = new_t
        if self._alive: return task.cont
        else: exit()

    def _handle_user_events_(self, ue):
        cmds = ue.get_cmds(self)
        if "exit" in cmds:
            print("exit")
            ## self._alive = False

