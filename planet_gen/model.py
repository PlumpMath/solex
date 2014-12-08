# ================
# Solex - model.py
# ================

# System imports.
from math import sqrt, degrees, asin

# Panda3d imports.
from panda3d.core import GeomVertexWriter, GeomVertexReader
from panda3d.core import GeomVertexData, GeomVertexFormat, GeomVertexArrayFormat
from panda3d.core import Geom, GeomNode, GeomTriangles, GeomPatches
from panda3d.core import NodePath, LODNode, Texture, TextureStage, InternalName
from panda3d.core import LVector2f, LVector3f, LVector4f, LPoint3f
from panda3d.core import PNMImage, Filename

# Local imports.
from etc.settings import _path
from etc.util import TimeIt
from gpu.panda3d_gpu import GPU_Image


class Hexasphere:
    
    # Pts.
    s = sqrt(3) / 2
    t = .5
    pts = (LVector3f(0, 0, 1),
        
           LVector3f(1, 0, t),
           LVector3f(.5, s, t),
           LVector3f(-.5, s, t),
           LVector3f(-1, 0, t),
           LVector3f(-.5, -s, t),
           LVector3f(.5, -s, t),

           LVector3f(s, .5, -t),
           LVector3f(0, 1, -t),
           LVector3f(-s, .5, -t),
           LVector3f(-s, -.5, -t),
           LVector3f(0, -1, -t),
           LVector3f(s, -.5, -t),
            
           LVector3f(0, 0, -1))
    
    # Tris.
    tris = ((0, 1, 2),
            (0, 2, 3),
            (0, 3, 4),
            (0, 4, 5),
            (0, 5, 6),
            (0, 6, 1),
             
            (1, 7, 2),
            (2, 7, 8),
            (2, 8, 3),
            (3, 8, 9),
            (3, 9, 4),
            (4, 9, 10),
             
            (4, 10, 5),
            (5, 10, 11),
            (5, 11, 6),
            (6, 11, 12),
            (6, 12, 1),
            (1, 12, 7),
             
            (13, 8, 7),
            (13, 9, 8),
            (13, 10, 9),
            (13, 11, 10),
            (13, 12, 11),
            (13, 7, 12))
            
    # Neighbors.
    nbrs = []
    for i, pt in enumerate(pts):
        pt.normalize()
        ni_list = []
        for tri in tris:
            if i in tri:
                ni_list.append(i)
                if len(ni_list) == 4:
                    break
        nbrs.append(ni_list)
    
    # Texture coords.
    uvs = (LVector2f(0,0),

           LVector2f(0,1),
           LVector2f(1,0),
           LVector2f(0,1),
           LVector2f(1,0),
           LVector2f(0,1),
           LVector2f(1,0),
           
           LVector2f(1,1),
           LVector2f(0,0),
           LVector2f(1,1),
           LVector2f(0,0),
           LVector2f(1,1),
           LVector2f(0,0),
            
           LVector2f(1,0))

class Sphere_Builder:
    
    def build_spheres(self):
        self.__build_Spheres()
    
    def __init__(self, recs):
        self.RECS = recs
        self.vformat = self.__generate_Vformat()
        
    
    def __build_Spheres(self):
        sphere = Hexasphere()
        
        def build_sphere(sphere, name):
            """Build and save actual model."""
            sphere_np = self.__build_Geom(sphere)
            sphere_np.setName(name)
            sphere_path = "{}/{}.bam".format(_path.MODELS, name)
            sphere_np.writeBamFile(sphere_path)
        
        # Build lower recursion full sphere models.
        for rec in range(self.RECS+1):
            if rec > 0:
                with TimeIt("Recursion {}".format(rec)):
                    sphere = self.__recurse_Sphere(sphere)
            
            # Tessellating spheres with patches.
            name = "sphere_{}".format(rec)
            with TimeIt("Build {}".format(name)):
                build_sphere(sphere, name)
                    
            print(" pts:  {}".format(len(sphere.pts)))
            print(" tris: {}".format(len(sphere.tris)))
            print()

    def __recurse_Sphere(self, sphere):
        
        def mid_point(pa, pb):
            # Find the mid pt between two pts.
            pax, pay, paz = pa
            pbx, pby, pbz = pb
            px, py, pz = (pax+pbx)/2, (pay+pby)/2, (paz+pbz)/2
            p = LVector3f(px, py, pz)
            p.normalize()
            return p
        
        pt_dict = {}
        pts, tris, uvs = sphere.pts, sphere.tris, sphere.uvs
        new_pts, new_tris, new_uvs = [], [], []
        i = 0
        for tri in sphere.tris:
            # New pts.
            a, b, c = tri
            pA, pB, pC = pts[a], pts[b], pts[c]
            pD = mid_point(pB, pC)
            pE = mid_point(pA, pC)
            pF = mid_point(pA, pB)
            uvA, uvB, uvC = uvs[a]*2, uvs[b]*2, uvs[c]*2
            uvD = (uvB+uvC) / 2
            uvE = (uvA+uvC) / 2
            uvF = (uvA+uvB) / 2
            p_list = (pA,pB,pC,pD,pE,pF)
            t_list = (uvA,uvB,uvC,uvD,uvE,uvF)
            pi_list = []
            for p, t in zip(p_list, t_list):
                if p not in pt_dict:
                    new_pts.append(p)
                    new_uvs.append(t)
                    pi_list.append(i)
                    pt_dict[p] = i
                    i += 1
                else:
                    pi_list.append(pt_dict[p])
            # New tris.
            a, b, c, d, e, f = pi_list
            tA = (a, f, e)
            tB = (f, b, d)
            tC = (e, d, c)
            tD = (d, e, f)
            new_tris.extend([tA,tB,tC,tD])

        new_sphere = Hexasphere()
        new_sphere.pts = new_pts
        new_sphere.tris = new_tris
        new_sphere.uvs = new_uvs
        
        return new_sphere

    def __build_Geom(self, sphere):
        vdata = GeomVertexData("Data", self.vformat, Geom.UHStatic)
        vertices = GeomVertexWriter(vdata, "vertex")
        mapcoords = GeomVertexWriter(vdata, "mapcoord")
        texcoords = GeomVertexWriter(vdata, "texcoord")
        
        _num_rows = len(sphere.pts)
        vertices.reserveNumRows(_num_rows)
        mapcoords.reserveNumRows(_num_rows)
        texcoords.reserveNumRows(_num_rows)

        # Pts.
        for pt, uv in zip(sphere.pts, sphere.uvs):
            vertices.addData3f(*pt)
            muv = self.__get_Map_UV(pt)
            mapcoords.addData2f(*muv)
            texcoords.addData2f(*uv) ## *.99+.01)
        
        # Tris
        prim = GeomPatches(3, Geom.UHStatic)
        prim.reserveNumVertices(len(sphere.tris))
        for tri in sphere.tris:
            prim.addVertices(*tri)
        prim.closePrimitive()
        
        # Geom.
        geom = Geom(vdata)
        geom.addPrimitive(prim)
        geom_node = GeomNode("geom")
        geom_node.addGeom(geom)
        geom_np = NodePath(geom_node)
        return geom_np

    def __get_Map_UV(self, pt, z_norm=LVector3f(), ref_vec=LVector3f(0,-1,0)):
        x, y, z = pt
        z_norm.set(*pt)
        z_norm.normalize()
        z = z_norm[-1]
        u_vec = LVector3f(x,y,0)
        u_vec.normalize()
        u_deg = u_vec.angleDeg(ref_vec)
        if x < 0: u_deg = 180 + (180-u_deg)
        u = u_deg/360
        v_deg = degrees(asin(z))
        v = (v_deg+90) / 180
        return (u, v)

    def __generate_Vformat(self):
        # Vformat.
        array = GeomVertexArrayFormat()
        array.addColumn(InternalName.make("vertex"), 3, Geom.NTFloat32, Geom.CPoint)
        ## array.addColumn(InternalName.make("normal"), 3, Geom.NTFloat32, Geom.CVector)
        ## array.addColumn(InternalName.make("color"), 4, Geom.NTFloat32, Geom.CColor)
        array.addColumn(InternalName.make("mapcoord"), 2, Geom.NTFloat32, Geom.CTexcoord)
        array.addColumn(InternalName.make("texcoord"), 2, Geom.NTFloat32, Geom.CTexcoord)
        ## array.addColumn(InternalName.make("info"), 4, Geom.NTFloat32, Geom.COther)
        vformat = GeomVertexFormat()
        vformat.addArray(array)
        vformat = GeomVertexFormat.registerFormat(vformat)
        return vformat

        
class Planet_Builder:
    
    def build_planet(self, recipe):
        self.__build_Planet(recipe)
    def generate_normal_map(self, recipe):
        self.__generate_Normal_Map_GPU(recipe)


    def __build_Planet(self, recipe):
        # Planet and LOD nodes.
        planet_name = recipe.__name__.lower()
        planet_np = NodePath("{}_model".format(planet_name))
        lod_node = LODNode("far_lod")
        lod_np = NodePath(lod_node)
        lod_np.reparentTo(planet_np)
        planet_path = "{}/{}".format(_path.BODIES, planet_name)
        recipe.planet_path = planet_path
        
        # Attach planet specs to dummy node.
        radius = recipe.radius
        r_dict ={}
        for attr_name in dir(recipe):
            if attr_name.startswith("__"): continue
            r_dict[attr_name] = getattr(recipe, attr_name)
        info_text = repr(r_dict)
        info_np = planet_np.attachNewNode(info_text)
        
        # Build models.
        far = 9999999999
        for rec, near in recipe.far_lod:
            with TimeIt("far LOD {} @ {}: ".format(rec, near)):
                # Load specified sphere model for each far LOD.
                sphere_path = "{}/sphere_{}.bam".format(_path.MODELS, rec)
                sphere_np = loader.loadModel(sphere_path).getChild(0)
                sphere_np.reparentTo(lod_np)
                lod_node.addSwitch(far, near)
                # Map terrain.
                sphere = Model(sphere_np)
                pts = sphere.read("vertex")
                pts = list(map(lambda pt: pt*radius, pts))
                sphere.modify("vertex", pts)
                far = near
                
        # Write bam for main planet model.
        model_path = "{}/{}.bam".format(planet_path, planet_name)
        planet_np.writeBamFile(model_path)

    def __assign_Terrains(self, model, recipe, final_rec=False):
        tex_dict = {}
        _set_col, _set_tex = False, False
        _sea_on = "sea_colour" in recipe
        enum_terrains = list(enumerate(recipe['terrains']))
        i = 0
        pts = model.read("vertex")
        cols = model.read("color")
        infos = model.read("info")
        
        for pt, col, info in zip(pts, cols, infos):
            terrain = None
            r, g, b, a = col
            for ti, ter in enum_terrains:
                # Default.
                if "default" in ter:
                    if ter['default']:
                        terrain = ter
                
                # Altitude.
                if "alt_range" in ter:
                    alt = pt.length()-recipe['radius']
                    low, high = ter['alt_range']
                    if alt >= low and alt <= high:
                        terrain = ter
                    else: continue
                
                # Colours.
                if "red_range" in ter:
                    low, high = ter['red_range']
                    if r >= low and r <= high:
                        terrain = ter
                    else: continue
                if "green_range" in ter:
                    low, high = ter['green_range']
                    if g >= low and g <= high:
                        terrain = ter
                    else: continue
                if "blue_range" in ter:
                    low, high = ter['blue_range']
                    if b >= low and b <= high:
                        terrain = ter
                    else: continue
                
                # Set terrain.
                if terrain:
                    infos[i][3] = ti
                    if "colour" in terrain:
                        cols[i] = terrain['colour']
                        _set_col = True
                    if "texture" in terrain:
                        tex_dict[i] = terrain['name']
            i += 1
            
        pts = None
        model.modify("color", cols)
        cols = None
        model.modify("info", infos)
        return tex_dict




class Model:
    
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
        vdata = self.model_np.node().getGeom(0).getVertexData()
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
            
        geom = self.model_np.node().modifyGeom(0)
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
            self.model_np.setTexture(ts, tex, i*10)
            


