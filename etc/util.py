# ===============
# Solex - util.py
# ===============

# System.
from multiprocessing import Process, Queue
from datetime import datetime
from time import sleep

# Panda3d.
from panda3d.core import NodePath, ClockObject, Filename, Texture, Loader
from panda3d.core import Shader, ShaderAttrib, PNMImage, InternalName
# Geom.
from panda3d.core import GeomVertexWriter, GeomVertexReader
from panda3d.core import GeomVertexData, GeomVertexFormat, GeomVertexArrayFormat
from panda3d.core import Geom, GeomNode, GeomTriangles, GeomPatches

# Local.
from etc.settings import _path


class TimeIt:
    
    def __init__(self, msg="", rnd=3):
        self._msg = msg
        self._rnd = rnd
        self._clock = ClockObject()
    def __enter__(self):
        self._start_dt = self._clock.getRealTime()
        return self
    def __exit__(self, *e_info):
        self._dur = self._clock.getRealTime()-self._start_dt
        if self._msg:
            print("{}:  {}".format(self._msg, round(self._dur, self._rnd)))
            for attr in self.__dict__:
                if attr.startswith("_"): continue
                print("  {}:  {}".format(attr, self.__dict__[attr]))

# Loop throttle.
class Throttle:
    
    def __init__(self, hz):
        if hz < 1: hz = 1.0
        self.clock = ClockObject()
        self.max_dur = 1.0/float(hz)
    
    def __enter__(self):
        self.start_dt = self.clock.getRealTime()
        return self

    def __exit__(self, *e_info):
        e_dt = self.clock.getRealTime()
        dur = e_dt-self.start_dt
        pause = self.max_dur-dur
        while pause > 0.0:
            sleep(pause)
            dt = self.clock.getRealTime()
            pause -= dt-e_dt
            e_dt = dt
            
class Geom_Builder:
    
    field_types = {
        'vertex':"point",
        'normal':"vector",
        'color':"color",
        'texcoord':"texcoord",
    }
    
    _data_types = {
        'point':(3, Geom.NTFloat32, Geom.CPoint, GeomVertexWriter.addData3f),
        'vector':(3, Geom.NTFloat32, Geom.CVector, GeomVertexWriter.addData3f),
        'color':(4, Geom.NTFloat32, Geom.CColor, GeomVertexWriter.addData4f),
        'texcoord':(2, Geom.NTFloat32, Geom.CTexcoord, GeomVertexWriter.addData2f),
        'vec2f':(2, Geom.NTFloat32, Geom.COther, GeomVertexWriter.addData2f),
        'vec3f':(3, Geom.NTFloat32, Geom.COther, GeomVertexWriter.addData3f),
        'vec4f':(4, Geom.NTFloat32, Geom.COther, GeomVertexWriter.addData4f),
        'vec2i':(2, Geom.NTUint32, Geom.COther, GeomVertexWriter.addData2i),
        'vec3i':(3, Geom.NTUint32, Geom.COther, GeomVertexWriter.addData3i),
        'vec4i':(4, Geom.NTUint32, Geom.COther, GeomVertexWriter.addData4i),
    }
        
    
    def build(self, data_dict, tris):
        return self.__build_Geom(data_dict, tris)
        
    
    def __init__(self, fields, field_types={}):
        self.fields = fields
        self.field_types.update(field_types)
        self.__vdata,\
        self.__writers = self.__build_Writers()
        
    
    def __build_Writers(self):
        # Build Vdata.
        array = GeomVertexArrayFormat()
        for field_name, field_spec_name in list(self.field_types.items()):
            field_specs = self._data_types[field_spec_name][:-1]
            array.addColumn(InternalName.make(field_name), *field_specs)
        vformat = GeomVertexFormat()
        vformat.addArray(array)
        vformat = GeomVertexFormat.registerFormat(vformat)
        vdata = GeomVertexData("data", vformat, Geom.UHStatic)
        
        # Build GeomVertexWriters.
        writers = {}
        for field_name in list(self.field_types.keys()):
            writers[field_name] = GeomVertexWriter(vdata, field_name)
        return vdata, writers
    def __build_Geom(self, data_dict, tris, prim_type=GeomTriangles):
        data_list = list(data_dict.items())
        _num_rows = 0
        for field, data in data_list:
            if not _num_rows: _num_rows = len(data)
            writer = self.__writers[field]
            writer.reserveNumRows(_num_rows)
            set_data = self._data_types[self.field_types[field]][-1]
            for datum in data:
                set_data(writer, *datum)
        
        # Tris
        prim = prim_type(Geom.UHStatic)
        prim.reserveNumVertices(len(tris))
        for tri in tris:
            prim.addVertices(*tri)
        prim.closePrimitive()
        
        # Geom.
        geom = Geom(self.__vdata)
        geom.addPrimitive(prim)
        geom_node = GeomNode("geom")
        geom_node.addGeom(geom)
        geom_np = NodePath(geom_node)
        return geom_np


class Model_Loader:
    
    # Public.
    def load_model(self, file_name, call_back, args=[], priority=1):
        self.__call_backs['file_name'] = (call_back, args)
        print("IN:", file_name)
        self.in_Q.put(file_name)
    def close(self):
        self.in_Q.put("close")
    def flush(self):
        while not self.out_Q.empty():
            file_name, geom = self.out_Q.get()
            cb, args = self.__call_backs.pop(file_name)
            cb(model, *args)
        
    # Callbacks.
    def _on_close(self, model):
        self.__in_Q.join_thread()
        self.__out_Q.join_thread()
        self.__load_proc.join()
    
    # Setup.
    def __init__(self):
        self.in_Q = Queue()
        self.out_Q = Queue()
        ## self.fart_node = NodePath("fart")
        self.__call_backs = {'close':self._on_close}
        self.__load_proc = Process(target=self._loader_, args=(self.in_Q, self.out_Q))
        self.__load_proc.start()

    # Main loop.
    def _loader_(self, in_Q, out_Q):
        _alive = True
        # print("FART", self.fart_node)
        loader = Loader()
        while _alive:
            file_name = in_Q.get()
            if file_name == "close":
                model = None
                _alive = False
            else:
                model = loader.loadSync(file_name)
                geom = NodePath(model.getChildren()[0])
                geom = geom.__reduce_persist__(geom)
                ## mp = pickler.dumps(model)
                print("OUT:", model)
            out_Q.put((file_name, geom))



