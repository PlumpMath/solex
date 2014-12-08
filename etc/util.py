# ===============
# Solex - util.py
# ===============

# Panda3d imports.
from panda3d.core import NodePath, ClockObject, Filename, Texture
from panda3d.core import Shader, ShaderAttrib, PNMImage, InternalName
# Geom imports.
from panda3d.core import GeomVertexWriter, GeomVertexReader
from panda3d.core import GeomVertexData, GeomVertexFormat, GeomVertexArrayFormat
from panda3d.core import Geom, GeomNode, GeomTriangles, GeomPatches

# Local imports.
from etc.settings import _path


class TimeIt:
    
    def __init__(self, msg):
        self.msg = msg
        self.clock = ClockObject()
    def __enter__(self):
        self.start_dt = self.clock.getRealTime()
        return self
    def __exit__(self, *e_info):
        dur = self.clock.getRealTime()-self.start_dt
        print("{}:  {}".format(self.msg, round(dur, 3)))
        for attr in self.__dict__:
            if attr in ("msg", "clock", "start_dt"): continue
            print("  {}:  {}".format(attr, self.__dict__[attr]))

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




