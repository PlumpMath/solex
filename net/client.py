# =================
# Solex - client.py
# =================

# System.
from sys import exit

# Panda3d.
from direct.showbase.ShowBase import ShowBase
from panda3d.core import ClockObject

# Local.
from etc.settings import _path, _maps, _sim
from gui.ueh import Default_UEH
from solex.lobby import Lobby
from solex.simulator import Simulator


class Client(ShowBase):
    
    # Public.
    def launch_system_local(self, sys_recipe):
        self.SIM.init_system(sys_recipe)
        self.SIM.start()
    def exit(self):
        self.SIM.stop()
        exit()
    
    # Setup.
    def __init__(self):
        ShowBase.__init__(self)
        self.Clock = ClockObject.getGlobalClock()
        self.cmd_map = _maps.client
        self._alive = True
        self._connected = False
        self._prev_t = 0
    
        # Init main menu and environment.
        self.LOBBY = Lobby(self)  # <-
        '''self.ENV = Environment(self)  # <-
        self.ENV.NP.hide()
        self.PRE_ENV = Preview_Env(self)  # <-
        self.PRE_ENV.NP.hide()'''
        self.DISPLAY = self.LOBBY
        self.SIM = Simulator(_sim.MAX_LOCAL_BODIES)
        
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
        self._handle_user_events_(ue)  # <-
        
        # Main loops.
        self.DISPLAY._main_loop_(ue, dt)  # <-
        self._prev_t = new_t
        
        if self._alive: return task.cont
        else: self.exit()

    def _handle_user_events_(self, ue):
        cmds = ue.get_cmds(self)
        if "exit" in cmds:
            print("exit")
            self._alive = False



