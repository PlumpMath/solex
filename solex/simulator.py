# ====================
# Solex - simulator.py
# ====================

# System imports.
from multiprocessing import Process, Value, Lock, cpu_count

# Panda3d.
from panda3d.core import Filename

# Local.
from etc.settings import _path, _sim
from etc.util import Throttle


class Simulator:
    
    # Public.
    def init_system(self, sys_recipe):
        self.SYS = self.__init_System(sys_recipe)
    def start(self):
        self.alive = Value("i", 1)
        self.__sim_proc = Process(target=self._physics_, args=(self.alive, self.SYS))
        self.__sim_proc.start()
    def stop(self):
        if self.alive.value == 1:
            self.alive.value = 0
            self.__sim_proc.join()
        
    # Setup.
    def __init__(self, max_bodies):
        self.max_bodies = max_bodies
        self.alive = None
        self.SYS = None
        self.__sim_proc = None


    def _physics_(self, alive, sys):
        sim_throttle = Throttle(_sim.LOCAL_THROTTLE)
        c = 0
        while alive.value:
            with sim_throttle:
                print(c)
            
            c += 1

    def __init_System(self, sys_recipe):
        sys = {}
        
        def add_body(body, x=0):
            x += body['aphelion']
            sys[body['name']] = [Value("d", x),    # x
                                 Value("d", 0.0),  # y
                                 Value("d", 0.0),  # z
                                 Value("f", 0.0),  # h
                                 Value("f", 0.0),  # p
                                 Value("f", 0.0),  # r
                                 Value("f", 0.0),  # vel
                                 Value("f", 0.0)]  # rot
                              
            for sat in body['sats']:
                x = add_body(sat, x)
            x -= body['aphelion']
            return x
            
        add_body(sys_recipe)
        return sys



