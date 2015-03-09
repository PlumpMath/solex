# ================
# Solex - views.py
# ================

# System.

# Panda3d.
from panda3d.core import NodePath, Filename

# Local.
from etc.settings import _path
from gui.gui import Lobby_Win, Pre_View_Win
from solex.cameras import *


class Lobby:
    
    cmd_map = {'exit':"escape"}
    
    # Public.
    def launch_pre_view(self, sys_name=""):
        if sys_name: self.client.init_system(sys_name)
        self.client.switch_display(self.client.PRE_VIEW)
    def refresh_servers(self):
        self.__refresh_Servers()
    def on_switch(self):
        print("lobby")
    
    # Setup.
    def __init__(self, client):
        self.client = client
        self.NP = NodePath("lobby")
        self.NP.reparentTo(render)
        self.GUI = Lobby_Win(ctrl=self)
        self.GUI.render()
        
        self.CAMERA = Dummy_Camera(self, "lobby")
        


    def _main_loop_(self, ue, dt):
        self.GUI._main_loop_(ue, dt)
        self._handle_user_events_(ue, dt)

    def _handle_user_events_(self, ue, dt):
        cmds = ue.get_cmds(self)
        if "exit" in cmds:
            print("exit")
            self.client._alive = False

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
        

class Pre_View:
    
    cmd_map = {'exit_to_lobby':"escape"}
    
    def on_sys_init(self):
        self.GUI.update(self.client.SYS)
    def on_switch(self):
        print("pre_view")
    
    def __init__(self, client):
        self.client = client
        self.NP = NodePath("pre_view")
        self.NP.reparentTo(render)
        self.SYS_NP = None
        self.cam_pos_np = self.NP.attachNewNode("pre_view_cam_pos_np")
       
        self.GUI = Pre_View_Win(ctrl=self)
        self.GUI.render()
        self.GUI.NP.hide()
        self.CAMERA = Preview_Camera(self, "pre_view")  # <-


    def _main_loop_(self, ue, dt):
        self.GUI._main_loop_(ue, dt)
        self._handle_user_events_(ue, dt)

    def _handle_user_events_(self, ue, dt):
        cmds = ue.get_cmds(self)
        if "exit_to_lobby" in cmds:
            print("exit_to_lobby")
            self.client.switch_display(self.client.LOBBY)


class Sys_View:
    
    def on_switch(self):
        pass


