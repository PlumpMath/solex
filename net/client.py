# =================
# Solex - client.py
# =================

# System.
from sys import exit
from glob import glob
from os import path as os_path

# Panda3d.
from direct.showbase.ShowBase import ShowBase
from panda3d.core import ClockObject, Filename

# Local.
from etc.settings import _path, _sim
from etc.shiva import Shiva_Compiler as SC
from gui.ueh import Default_UEH
from solex.views import *
from solex.bodies import *
from solex.simulator import Simulator


class Client(ShowBase):
    
    # Public.
    def init_system(self, sys_name):
        sys_recipe = self.sys_recipes[sys_name]
        self.SYS = self.__init_Sys(sys_recipe)
        self.SIM.init_system(sys_recipe)
        self.PRE_VIEW.on_sys_init()
        ## self.SIM.start()
    def exit(self):
        self.SIM.stop()
        exit()
    def switch_display(self, display):
        display.on_switch()
        self.__switch_Display(display)
    def refresh_sys_recipes(self):
        self.sys_recipes = self.__refresh_Sys_Recipes()
    
    # Setup.
    def __init__(self):
        ShowBase.__init__(self)
        self.Clock = ClockObject.getGlobalClock()
        self._alive = True
        self._connected = False
        self._prev_t = 0
        self._display_region = self.cam.getNode(0).getDisplayRegion(0)
    
        # Init main menu and environment.
        self.LOBBY = Lobby(self)  # <-
        '''self.ENV = Environment(self)  # <-
        self.ENV.NP.hide()'''
        self.PRE_VIEW = Pre_View(self)  # <-
        self.PRE_VIEW.NP.hide()
        self.DISPLAY = self.LOBBY
        self.SIM = Simulator(_sim.MAX_LOCAL_BODIES)
        self.sys_recipes = self.__refresh_Sys_Recipes()
        
        # Init Player and main objects.
        ## self.PLAYER = Player()  # <-
        self.UEH = Default_UEH()  # <-
        
        self.setBackgroundColor(0,0,0)
        self.disableMouse()
        
        # Network data.
        '''self.host = socket.gethostbyname(socket.gethostname())
        self.tcp_addr = (self.host, CLIENT_TCP_PORT)
        self.udp_addr = (self.host, CLIENT_UDP_PORT)
        ## self.tcp_req_addr = (self.host, CLIENT_REQUEST_PORT)
        self.proxy_tcp_addr = None   ## self.client_proxy_tcp_addr
        ## self.LOBBY.refresh_servers()  # <-'''
        
        # Main loop.
        taskMgr.add(self._main_loop_, "main_loop", appendTask=True, sort=0)  # <-
        
    
    def _main_loop_(self, task):
        # Get 'dt' - time lapsed since last frame.
        new_t = self.Clock.getRealTime()
        dt = new_t - self._prev_t
        
        # User events.
        ue = self.UEH._get_events_()  # <-
        self._handle_user_events_(ue, dt)  # <-
        
        # Main loops.
        self.DISPLAY._main_loop_(ue, dt)  # <-
        self._prev_t = new_t
        
        if self._alive: return task.cont
        else: self.exit()

    def _handle_user_events_(self, ue, dt):
        pass
    def __refresh_Sys_Recipes(self):
        sys_dir_path = Filename("{}/*.shv".format(_path.SYSTEMS))
        sys_files = glob(sys_dir_path.toOsLongName())
        sys_recipes = {}
        for sys_file in sys_files:
            base_name = os_path.basename(sys_file)
            sys_name = os_path.splitext(base_name)[0]
            sys_recipes[sys_name] = SC.compile_sys_recipe(sys_file)
        return sys_recipes

    def __init_Sys(self, sys_recipe):
        
        class Sys:
            name = sys_recipe['name']
            BODIES = []
            B_DICT = {}
        sys = Sys()
        
        def add_body(body_recipe):
            body = Body(body_recipe)
            sys.BODIES.append(body)
            sys.B_DICT[body_recipe['name']] = body
            for sat in body_recipe['sats']:
                add_body(sat)
            
        add_body(sys_recipe)
        return sys

    def __switch_Display(self, display):
        self.DISPLAY.NP.hide()
        self.DISPLAY.GUI.NP.hide()
        self.DISPLAY.CAMERA.cam_node.setActive(False)
        display.NP.show()
        display.GUI.NP.show()
        display.CAMERA.cam_node.setActive(True)
        self._display_region.setCamera(display.CAMERA.NP)
        self.DISPLAY = display



