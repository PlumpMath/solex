# ====================
# Solex - simulator.py
# ====================

# System imports.
from multiprocessing import Process, Value, Lock, cpu_count

# Panda3d.
from panda3d.core import Filename, ClockObject
from panda3d.core import LVector3d, LVector3f

# Local.
from etc.settings import _path, _sim, _phys
from etc.util import Throttle


class Simulator:
    
    # Public.
    def init_system(self, sys_recipe):
        self.sys_recipe = sys_recipe
        self.BODIES = self.__init_System(sys_recipe)
    def start(self, mode="python"):
        self.alive = Value("i", 1)
        if mode == "python":
            self.__sim_proc = Process(target=self._physics_, args=(self.alive, self.BODIES))
            self.__sim_proc.start()
    def stop(self):
        if self.alive.value == 1:
            self.alive.value = 0
            self.__sim_proc.join()
    def get_body_state(self, body_name):
        ba = self.BODIES[body_name]
        return {'POS':(ba[0].value, ba[1].value, ba[2].value),
                'VEC':(ba[3].value, ba[4].value, ba[5].value),
                'HPR':(ba[6].value, ba[7].value, ba[8].value),
                'ROT':(ba[9].value, ba[10].value, ba[11].value)}
        
    # Setup.
    def __init__(self, max_bodies):
        self.max_bodies = max_bodies
        self.alive = Value("i", 0)
        self.BODIES = None
        self.sys_recipe = None
        self.__sim_proc = None


    def _physics_(self, alive, sys):
        sim_throttle = Throttle(_sim.HZ)
        sys_root = self.__init_Py_Bodies(self.sys_recipe)
        dir_vec = LVector3d(0,0,0)
        clock = ClockObject.getGlobalClock()
        G = _phys.G
        
        def apply_physics(body, parent, dt):
            if parent:
                # Find distance and direction from body to its parent.
                dir_vec.set(*body['POS']-parent['POS'])
                dist = dir_vec.length()
                dir_vec.normalize()
                
                # Apply parent's gravity.
                F = (G*(parent['mass']+body['mass'])) / (dist**2)
                body['delta_vec'] = -dir_vec * F * dt
                body['VEC'] += body['delta_vec'] + parent['delta_vec']
                body['POS'] += body['VEC'] * dt
                
                # Update self.BODIES.
                ba = self.BODIES[body['name']]
                pos, vec, hpr, rot = body['POS'], body['VEC'], body['HPR'], body['ROT']
                ba[0].value, ba[1].value, ba[2].value = pos.x, pos.y, pos.z
                ba[3].value, ba[4].value, ba[5].value = vec.x, vec.y, vec.z
                ba[6].value, ba[7].value, ba[8].value = hpr.x, hpr.y, hpr.z
                ba[9].value, ba[10].value, ba[11].value = rot.x, rot.y, rot.z
                
            for sat in body['bodies']:
                apply_physics(sat, body, dt)

        p_time = 0
        while alive.value:
            with sim_throttle:
                c_time = clock.getRealTime()
                dt = c_time - p_time
                apply_physics(sys_root, None, dt)
                p_time = c_time
                    
    def __init_System(self, sys_recipe):
        sys = {}
        
        def add_body(body, parent_str="", x=0):
            x += body['aphelion']
            sys[body['name']] = [Value("d", x),    # x
                                 Value("d", 0.0),  # y
                                 Value("d", 0.0),  # z
                                 Value("f", 0.0),  # vx
                                 Value("f", 0.0),  # vy
                                 Value("f", 0.0),  # vz
                                 Value("f", 0.0),  # h
                                 Value("f", 0.0),  # p
                                 Value("f", 0.0),  # r
                                 Value("f", 0.0),  # rh
                                 Value("f", 0.0),  # rp
                                 Value("f", 0.0)]  # rr
                              
            for sat in body['sats']:
                add_body(sat, body['name'], x)
            x -= body['aphelion']
            
        add_body(sys_recipe)
        return sys

    def __init_Py_Bodies(self, sys_recipe):
        
        def add_body(body, x=0):
            x += body['aphelion']
            bodies = []
            for sat in body['sats']:
                bodies.append(add_body(sat, x))
            
            body_dict = {'name':body['name'],
                         'mass':body['mass'],
                         'radius':body['radius'],
                         'POS':LVector3d(x,0,0),
                         'HPR':LVector3f(0,0,0),
                         'VEC':LVector3d(0,0,0),
                         'ROT':LVector3f(0,0,0),
                         'delta_vec':LVector3d(0,0,0),
                         'bodies':bodies}
                              
            x -= body['aphelion']
            return body_dict
            
        sys_root = add_body(sys_recipe)
        return sys_root



