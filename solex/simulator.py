# ====================
# Solex - simulator.py
# ====================

# System imports.
from multiprocessing import Process, Value 
from math import sqrt

# Panda3d.
from panda3d.core import Filename, ClockObject
from panda3d.core import LVector3d, LVector3f

# Local.
from etc.settings import _path, _sim, _phys
from etc.util import Throttle, TimeIt


class Simulator:
    
    # Public.
    def init_system(self, sys_recipe):
        self.stop()
        self.sys_recipe = sys_recipe
        self.BODIES = self.__init_Bodies(sys_recipe)
    def start(self, mode="python"):
        self.alive = Value("i", 1)
        if mode == "python":
            self.__sim_proc = Process(target=self._physics_, args=(self.alive, self.BODIES))
            self.__sim_proc.start()
    def stop(self):
        if self.alive.value == 1:
            self.alive.value = 0
            self.__sim_proc.join()
    def get_state(self, sys_pos):
        return self.__get_State(sys_pos)
    def get_object_state(self, obj_id, fields=[]):
        return self.__get_Object_State(obj_id, fields)
        
    # Setup.
    def __init__(self, max_bodies):
        self.max_bodies = max_bodies
        self.alive = Value("i", 0)
        self.BODIES = None
        self.sys_recipe = None
        self.__sim_proc = None


    def _physics_(self, alive, sys):
        sim_throttle = Throttle(_sim.HZ)
        sys_root = self.__init_Sim_System(self.sys_recipe)
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
                b = self.BODIES[body['name']]
                pos, vec, hpr, rot = body['POS'], body['VEC'], body['HPR'], body['ROT']
                b['x'].value, b['y'].value, b['z'].value = pos.x, pos.y, pos.z
                b['vx'].value, b['vy'].value, b['vz'].value = vec.x, vec.y, vec.z
                b['h'].value, b['p'].value, b['r'].value = hpr.x, hpr.y, hpr.z
                b['rh'].value, b['rp'].value, b['rr'].value = rot.x, rot.y, rot.z
                
            for sat in body['bodies']:
                apply_physics(sat, body, dt)

        p_time = 0
        dt = 0
        while alive.value:
            with sim_throttle:
                ## with TimeIt() as tt:
                c_time = clock.getRealTime()
                dt = c_time - p_time
                apply_physics(sys_root, None, dt)
                p_time = c_time
                ## print(tt.dur/dt)
                    
    def __init_Bodies(self, sys_recipe):
        sys = {}
        
        def add_body(body, p_mass=0, pv=0, x=0):
            x += body['aphelion']
            v = 0
            if x:
                v = sqrt((_phys.G*(p_mass+body['mass']))*(2/body['aphelion']-1/body['sm_axis']))
                ## print(body['name'])
                ## print(v);print()
                
            sys[body['name']] = {
                '_prox':body['radius']*body['far_horizon'],
                'x':Value("d", x),
                'y':Value("d", 0.0),
                'z':Value("d", 0.0),
                'vx':Value("f", 0.0),
                'vy':Value("f", v+pv),
                'vz':Value("f", 0.0),
                'h':Value("f", 0.0),
                'p':Value("f", 0.0),
                'r':Value("f", 0.0),
                'rh':Value("f", 0.0),
                'rp':Value("f", 0.0),
                'rr':Value("f", 0.0)}
                              
            for sat in body['sats']:
                add_body(sat, body['mass'], v, x)
            x -= body['aphelion']
            
        add_body(sys_recipe)
        return sys

    def __init_Sim_System(self, sys_recipe):
        
        def add_body(body, p_mass=0, pv=0, x=0):
            x += body['aphelion']
            v = 0
            if x:
                v = sqrt((_phys.G*(p_mass+body['mass']))*(2/body['aphelion']-1/body['sm_axis']))
            bodies = []
            for sat in body['sats']:
                bodies.append(add_body(sat, body['mass'], v, x))
            
            body_dict = {'name':body['name'],
                         'mass':body['mass'],
                         'radius':body['radius'],
                         'POS':LVector3d(x,0,0),
                         'VEC':LVector3d(0,v+pv,0),
                         'HPR':LVector3f(0,0,0),
                         'ROT':LVector3f(0,0,0),
                         'delta_vec':LVector3d(0,0,0),
                         'bodies':bodies}
                              
            x -= body['aphelion']
            return body_dict
            
        sys_root = add_body(sys_recipe)
        return sys_root

    def __get_State(self, sys_pos, obj_vec=LVector3d(0,0,0)):
        state = {}
        for obj_id, o in self.BODIES.items():
            obj_vec.set(o['x'].value, o['y'].value, o['z'].value)
            dist = (sys_pos-obj_vec).length()
            if dist < o['_prox']:
                state[obj_id] = {'sys_pos':(o['x'].value, o['y'].value, o['z'].value),
                                 'sys_vec':(o['vx'].value, o['vy'].value, o['vz'].value),
                                 'sys_hpr':(o['h'].value, o['p'].value, o['r'].value),
                                 'sys_rot':(o['rh'].value, o['rp'].value, o['rr'].value)}
        return state

    def __get_Object_State(self, obj_id, fields=[]):
        if not fields:
            fields = ["sys_pos", "sys_vec", "sys_hpr", "sys_rot"]
        o = self.BODIES[obj_id]
        obj_state = {}
        if "sys_pos" in fields:
            obj_state['sys_pos'] = (o['x'].value, o['y'].value, o['z'].value)
        if "sys_vec" in fields:
            obj_state['sys_vec'] = (o['vx'].value, o['vy'].value, o['vz'].value)
        if "sys_hpr" in fields:
            obj_state['sys_hpr'] = (o['h'].value, o['p'].value, o['r'].value)
        if "sys_rot" in fields:
            obj_state['sys_rot'] = (o['rh'].value, o['rp'].value, o['rr'].value)
        
        return obj_state



