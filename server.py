# =================
# Solex - server.py
# =================

# Prevent Panda3d window from opening.
## from panda3d.core import loadPrcFileData
## loadPrcFileData("", "window-type offscreen" ) # Spawn an offscreen buffer

# Local.
from net.server import Server

SYS_NAME = "sol"

if __name__ == "__main__":
    server = Server()
    sys_path = "{}/{}.shv".format(_path.SYSTEMS, SYS_NAME)
    sys_recipe = SC.compile_sys_recipe(sys_path)
    server.init_system("sol")
    server.run()
