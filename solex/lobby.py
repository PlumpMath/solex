# ================
# Solex - lobby.py
# ================

# System.
from glob import glob
from os import path as os_path

# Panda3d.
from panda3d.core import NodePath, Filename

# Local.
from etc.settings import _path
from etc.shiva import Shiva_Compiler as SC
from gui.gui import Lobby_Win


class Lobby:
    
    cmd_map = {'exit':"escape"}
    
    # Public.
    def launch_system_local(self, sys_name):
        sys_recipe = self.sys_recipes[sys_name]
        self.client.launch_system_local(sys_recipe)
    def refresh_servers(self):
        self.__refresh_Servers()
    
    # Setup.
    def __init__(self, client):
        self.client = client
        self.NP = NodePath("lobby")
        self.NP.reparentTo(render)
        self.GUI = Lobby_Win(ctrl=self)
        self.GUI.render()
        
        self.sys_recipes = self.__load_Sys_Recipes()
        ## self.CAMERA = _Camera_(self)  # Dummy Camera (renders nothing)
    
    

    
    def _main_loop_(self, ue, dt):
        self.GUI._main_loop_(ue, dt)
        ## self._handle_user_events_(ue)

    def _handle_user_events_(self, ue):
        pass

    def __refresh_Servers(self):
        server_array = []
        for host in SERVER_LIST:
            server_addr = (host, SERVER_PING_PORT)
            with TCP_Ping(server_addr) as tcp:
                tcp.ping()
            if tcp.val < 0: sys_name, ping = "-", "-"
            else: sys_name, ping = tcp.msg, tcp.val
            server_array.append([host, "-", sys_name, str(ping)])
        return server_array
        
    def __load_Sys_Recipes(self):
        sys_dir_path = Filename("{}/*.shv".format(_path.SYSTEMS))
        sys_files = glob(sys_dir_path.toOsLongName())
        sys_recipes = {}
        for sys_file in sys_files:
            base_name = os_path.basename(sys_file)
            sys_name = os_path.splitext(base_name)[0]
            sys_recipes[sys_name] = SC.compile_sys_recipe(sys_file)
        return sys_recipes


