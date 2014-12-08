# ================
# Solex - model.py
# ================

# Panda3d imports.
from panda3d.core import GeomVertexWriter, GeomVertexReader
from panda3d.core import LVector2f, LVector3f, LVector4f, LPoint3f
from panda3d.core import Texture, TextureStage


class Modify_Model:
    
    def read(self, field):
        return self.__read_Model(field)
    def modify(self, field, data=None):
        self.__modify_Model(field, data)
    def apply_textures(self, recipe, tex_dict):
        self.__apply_Textures(recipe, tex_dict)
    
    def __init__(self, model_np):
        self.model_np = model_np
            
    def __read_Model(self, field):
        get_dict = {
            'vertex':(GeomVertexReader.getData3f, LPoint3f),
            'normal':(GeomVertexReader.getData3f, LVector3f),
            'color':(GeomVertexReader.getData4f, LVector4f),
            'texcoord':(GeomVertexReader.getData2f, LVector2f),
            'info':(GeomVertexReader.getData4f, list),
            'ref':(GeomVertexReader.getData3f, LPoint3f),
            'nbr':(GeomVertexReader.getData4f, list)}
            
        data = []
        vdata = self.NP.node().getGeom(0).getVertexData()
        reader = GeomVertexReader(vdata, field)
        get_data, v_type = get_dict[field]
        while not reader.isAtEnd():
            datum = v_type(get_data(reader))
            data.append(datum)
            
        return data

    def __modify_Model(self, field, data):
        set_dict = {
            'vertex':GeomVertexWriter.setData3f,
            'normal':GeomVertexWriter.setData3f,
            'color':GeomVertexWriter.setData4f,
            'texcoord':GeomVertexWriter.setData2f,
            'info':GeomVertexWriter.setData4f,
            'ref':GeomVertexWriter.setData3f,
            'nbr':GeomVertexWriter.setData4i}
            
        geom = self.NP.node().modifyGeom(0)
        vdata = geom.modifyVertexData()
        vwriter = GeomVertexWriter(vdata, field)
        vwriter.reserveNumRows(len(data))
        set_data = set_dict[field]
        for datum in data:
            set_data(vwriter, *datum)
        geom.setVertexData(vdata)

    def __apply_Textures(self, recipe, tex_dict):
        for i, ter_dict in enumerate(recipe['terrains']):
            tex_img = PNMImage()
            tex_img.read(Filename("{}/tex/{}".format(recipe['planet_path'], ter_dict['texture'])))
            tex = Texture()
            tex.load(tex_img)
            tex.setMinfilter(Texture.FTLinear)
            ts = TextureStage(str(i))
            ts.setSort(i)
            self.NP.setTexture(ts, tex, i*10)
            


