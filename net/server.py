# =================
# Solex - server.py
# =================

# System.
from sys import exit

# Panda3d.
from direct.showbase.ShowBase import ShowBase

# Local.
from etc.settings import _path
from etc.shiva import Shiva_Compiler as SC
from solex.simulator import Simulator

# Config.
MAX_BODIES = 1000


class Server(ShowBase):
    
    # Public.
    def init_system(self, sys_recipe):
        self.SIM.init_system(sys_recipe)
        self.SIM.start()
    def exit(self):
        print("server.exit")
        self.SIM.stop()
        exit()
        
    # Setup.
    def __init__(self):
        ShowBase.__init__(self)
        self.SIM = Simulator(MAX_BODIES)
                
        # Temp.
        self.accept("escape", self.exit)
        self.setBackgroundColor(0,0,0)




