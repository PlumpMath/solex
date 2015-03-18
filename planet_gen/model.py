# ================
# Solex - model.py
# ================

# System imports.
from ast import literal_eval
from math import sqrt, degrees, asin

# Panda3d imports.
from direct.showbase.ShowBase import ShowBase
from panda3d.core import GeomVertexWriter, GeomVertexReader
from panda3d.core import GeomVertexData, GeomVertexFormat, GeomVertexArrayFormat
from panda3d.core import Geom, GeomNode, GeomTriangles, GeomPatches
from panda3d.core import NodePath, LODNode, Texture, TextureStage, InternalName
from panda3d.core import LVector2f, LVector3f, LVector3i, LVector4f, LPoint3f, PTA_LVecBase2f
from panda3d.core import PNMImage, Filename

# Local imports.
from etc.settings import _path
from etc.util import TimeIt
from etc.shiva import Shiva_Compiler as SC
from solex.texture import Texture_Manager as TM
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
           
    for i, pt in enumerate(pts):
        pt.normalize()
    
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
    
    # Texture uvs (how pts map to terrain textures.)
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
    
    def __init__(self, recs, mode):
        self.RECS = recs
        self.mode = mode
        self.__generate_Vformats()
        
    
    def __build_Spheres(self):
        sphere = Hexasphere()
        sphere.coords = []
        for pt in sphere.pts:
            sphere.coords.append(self.__get_Pt_Coords(pt))
        
        # Recursively generate spheres.
        for rec in range(self.RECS+1):
            if rec > 0:
                with TimeIt("Recursion {}".format(rec)):
                    sphere = self.__recurse_Sphere(sphere)
            
            name = "sphere_{}".format(rec)
            with TimeIt("Build {}".format(name)):
                if self.mode == "tris":
                    sphere_np = self.__build_Tris(sphere)
                    sphere_path = "{}/{}t.bam".format(_path.MODELS, name)
                elif self.mode == "patches":
                    sphere_np = self.__build_Patches(sphere)
                    sphere_path = "{}/{}.bam".format(_path.MODELS, name)
                sphere_np.setName(name)
                sphere_np.writeBamFile(sphere_path)
                
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
        new_pts, new_tris, new_uvs = [], [], []  # Derived from previous recursion vals.
        new_coords = []  # (map_u, map_v, latitude, longitude)
        i = 0
        for tri in sphere.tris:
            # New pts.
            a, b, c = tri
            pA, pB, pC = pts[a], pts[b], pts[c]
            pD = mid_point(pB, pC)
            pE = mid_point(pA, pC)
            pF = mid_point(pA, pB)
            # New uvs.
            uvA, uvB, uvC = uvs[a]*2, uvs[b]*2, uvs[c]*2
            uvD = (uvB+uvC) / 2
            uvE = (uvA+uvC) / 2
            uvF = (uvA+uvB) / 2
            # Gather and assemble old and new pts into new tris.
            p_list = (pA,pB,pC,pD,pE,pF)
            uv_list = (uvA,uvB,uvC,uvD,uvE,uvF)
            pi_list = []
            for p, uv in zip(p_list, uv_list):
                # Add pt if it doesn't exist.
                if p not in pt_dict:
                    new_pts.append(p)
                    new_uvs.append(uv)
                    new_coords.append(self.__get_Pt_Coords(p))
                    pi_list.append(i)
                    pt_dict[p] = i
                    i += 1
                # Pull it from pt_dict if it does exist.
                else:
                    pi_list.append(pt_dict[p])
            # New tris.
            a, b, c, d, e, f = pi_list
            tA = (a, f, e)
            tB = (f, b, d)
            tC = (e, d, c)
            tD = (d, e, f)
            new_tris.extend([tA,tB,tC,tD])

        # Create sphere for this recursion level.
        new_sphere = Hexasphere()
        new_sphere.pts = new_pts
        new_sphere.tris = new_tris
        new_sphere.uvs = new_uvs
        new_sphere.coords = new_coords
        
        return new_sphere

    def __build_Tris(self, sphere):
        vdata = GeomVertexData("Data", self.__tris_vformat, Geom.UHStatic)
        vertices = GeomVertexWriter(vdata, "vertex")
        ## colors = GeomVertexWriter(vdata, "color")
        normals = GeomVertexWriter(vdata, "normal")
        mapcoords = GeomVertexWriter(vdata, "texcoord")
        
        _num_rows = len(sphere.pts)
        vertices.reserveNumRows(_num_rows)
        ## colors.reserveNumRows(_num_rows)
        normals.reserveNumRows(_num_rows)
        mapcoords.reserveNumRows(_num_rows)
        
        # Pts.
        norm_vec = LVector3f(0,0,0)
        for pt, mc in zip(sphere.pts, sphere.coords):
            vertices.addData3f(*pt)
            ## colors.addData4f(.1,.1,.1,0)
            norm_vec.set(*pt)
            norm_vec.normalize()
            normals.addData3f(*norm_vec)
            u, v = mc[:2]
            mapcoords.addData2f(u,v)
        
        # Tris.
        prim = GeomTriangles(Geom.UHStatic)
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

    def __build_Patches(self, sphere):
        vdata = GeomVertexData("Data", self.__patches_vformat, Geom.UHStatic)
        vertices = GeomVertexWriter(vdata, "vertex")
        mapcoords = GeomVertexWriter(vdata, "mapcoord")
        texcoords = GeomVertexWriter(vdata, "texcoord")
        
        _num_rows = len(sphere.pts)
        vertices.reserveNumRows(_num_rows)
        mapcoords.reserveNumRows(_num_rows)
        texcoords.reserveNumRows(_num_rows)
        
        # Pts.
        for pt, uv, coords, in zip(sphere.pts, sphere.uvs, sphere.coords):
            vertices.addData3f(*pt)
            mapcoords.addData2f(*coords)
            texcoords.addData2f(*uv) ## *.99+.01)
        
        # Patches.
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

    def __get_Pt_Coords(self, pt, z_norm=LVector3f(), ref_vec=LVector3f(0,-1,0)):
        x, y, z = pt
        z_norm.set(*pt)
        z_norm.normalize()
        z = z_norm[-1]
        # u / longitude.
        u_vec = LVector3f(x,y,0)
        u_vec.normalize()
        lon = u_vec.angleDeg(ref_vec)
        if x < 0: lon = 180 + (180-lon)
        lon -= 180
        mu = lon/360
        # v / latitude.
        lat = degrees(asin(z))
        mv = (lat+90) / 180
        return mu, mv

    def __generate_Vformats(self):
        # Tris.
        array = GeomVertexArrayFormat()
        array.addColumn(InternalName.make("vertex"), 3, Geom.NTFloat32, Geom.CPoint)
        array.addColumn(InternalName.make("normal"), 3, Geom.NTFloat32, Geom.CVector)
        array.addColumn(InternalName.make("color"), 4, Geom.NTFloat32, Geom.CColor)
        array.addColumn(InternalName.make("texcoord"), 2, Geom.NTFloat32, Geom.CTexcoord)
        vformat = GeomVertexFormat()
        vformat.addArray(array)
        self.__tris_vformat = GeomVertexFormat.registerFormat(vformat)
        # Patches.
        array = GeomVertexArrayFormat()
        array.addColumn(InternalName.make("vertex"), 3, Geom.NTFloat32, Geom.CPoint)
        array.addColumn(InternalName.make("mapcoord"), 2, Geom.NTFloat32, Geom.CTexcoord)
        array.addColumn(InternalName.make("texcoord"), 2, Geom.NTFloat32, Geom.CTexcoord)
        vformat = GeomVertexFormat()
        vformat.addArray(array)
        self.__patches_vformat = GeomVertexFormat.registerFormat(vformat)

        
class Planet_Builder(ShowBase):
    

    def build_low_models(self, planet_spec):
        planet = Planet(planet_spec)
        near = planet.radius
        recs = list(map(lambda lod: lod[0], planet.far_lod)) + [planet.preview_rec]
        for rec in recs:
            model_np = self.__build_Simple_Model(planet, rec)
            if rec == recs[-1]: name="pre"
            else: name = rec
            model_np.writeBamFile("{}/{}_{}.bam".format(planet.path, planet.name, name))
            
    def build_high_model(self, planet_spec):
        pass
    def build_all(self, planet_spec):
        pass
    

    def __build_Simple_Model(self, planet, rec):
        model_path = "{}/sphere_{}t.bam".format(_path.MODELS, rec)
        model_np = loader.loadModel(model_path).getChild(0)
        model_np.setName("model_{}".format(rec))
        model = Model(model_np)
        
        # Inflate sphere model to planet radius.
        pts = model.read("vertex")
        pts = list(map(lambda pt: pt*planet.radius, pts))
        model.modify("vertex", pts)
        
        # Map planet topography.
        if "height_map" in planet.__dict__:
            self.__map_Topography(planet, model, pts)
        
        farts = {8:(1,0,0,1),7:(0,1,0,1),4:(0,0,1,1)}
        # Map planet colours.
        if "colour_map" in planet.__dict__ and rec != 6:
            fart_col = farts[rec]
            self.__map_Colours(planet, model, rec, fart_col)
        
        model_np.attachNewNode("planet_label")
        return model_np

    def __map_Colours(self, planet, model, rec, fart_col, pts=[]):
        col_map_path = planet.colour_map.replace(".","_low.")
        col_map_fn = Filename("{}/maps/{}".format(planet.path, col_map_path))
        
        '''if rec >= 6:
            col_map = loader.loadTexture(col_map_fn)
            model.NP.setTexture(col_map)
        else:'''
        col_map = PNMImage()
        col_map.read(col_map_fn)
        _cu_size = col_map.getXSize()-1
        _cv_size = col_map.getYSize()-1
       
        cols = []
        if not pts: pts = model.read("vertex")
        for pt in pts:
            u, v = self.__get_Pt_Uv(pt, _cu_size, _cv_size)
            r = col_map.getRed(u, v)
            g = col_map.getGreen(u, v)
            b = col_map.getBlue(u, v)
            pt_col = (r, g, b, 1)
            cols.append(fart_col)
        model.modify("color", cols)

    def __map_Topography(self, planet, model, pts=[]):
        height_map = PNMImage()
        height_map_path = "{}/maps/{}".format(planet.path, planet.colour_map)
        height_map.read(Filename(height_map_path))
        _hu_size = height_map.getXSize()-1
        _hv_size = height_map.getYSize()-1
        
        radius = planet.radius
        bottom = radius + planet.height_min
        elev_range = planet.height_max - planet.height_min
        _has_sea = "sea_level" in planet.__dict__
        if _has_sea:
            sea_level = planet.sea_level + planet.radius
        
        if not pts:
            pts = model.read("vertex")
            
        for pt in pts:
            u, v = self.__get_Pt_Uv(pt, _hu_size, _hv_size)
            height_val = height_map.getGray(u, v)  ## watch when extending w colours.
            height = bottom + elev_range*height_val
            ratio = height / radius
            pt *= ratio
            
            # If planet has sea then raise vert to sea level.
            if _has_sea:
                len_pt = pt.length()
                if len_pt <= sea_level:
                    ratio = sea_level/len_pt
                    pt *= ratio
        
        model.modify("vertex", pts)
        ## self.__set_Normals(model)
                
    def __get_Pt_Uv(self, pt, u_size, v_size, z_norm=LVector3f(), ref_vec=LVector3f(0,-1,0)):
        x, y, z = pt
        z_norm.set(*pt)
        z_norm.normalize()
        z = z_norm[-1]
        u_vec = LVector3f(x,y,0)
        u_vec.normalize()
        u_deg = u_vec.angleDeg(ref_vec) + 180
        if x < 0: u_deg = 180 + (180-u_deg)
        u = u_deg / 360
        v_deg = degrees(asin(z))
        v = (v_deg+90) / 180
        u = int(u*u_size)
        v = int((1-v)*v_size)
        return u, v

    def __build_Normal_Map(self, recipe):
        # Load ref image.
        ref_img = PNMImage()
        height_map_path = "{}/maps/{}".format(recipe['path'], recipe['height_map'])
        ref_img.read(Filename(height_map_path))
        
        # Create normal map from height map with GPU.
        with GPU_Image(ref_img, print_times=True) as gpu:
            height_range = LVector2f(recipe['height_min'], recipe['height_max'])
            norm_img = gpu.generate_normal_map(height_range=height_range)
            norm_img.write(Filename("{}/maps/earth_norm.jpg".format(recipe['path'])))
        
        return recipe
        
    def __build_Terrain_Map(self, recipe):
        # Height map.
        height_map = PNMImage()
        height_map_path = "{}/maps/{}".format(recipe['path'], recipe['height_map'])
        height_map.read(Filename(height_map_path))
        # Colour map.
        col_map = PNMImage()
        col_map_path = "{}/maps/{}".format(recipe['path'], recipe['colour_map'])
        col_map.read(Filename(col_map_path))
        # Normal map.
        norm_map = PNMImage()
        norm_map_path = "{}/maps/{}".format(recipe['path'], recipe['normal_map'])
        norm_map.read(Filename(norm_map_path))
        
        # Dict of range qualifiers to pass directly to 'generate_terrain_map'.
        t_count = len(recipe['terrains'])
        ranges_dict = {'lat_ranges':PTA_LVecBase2f([LVector2f(x*0,0) for x in range(t_count)]),
                       'lon_ranges':PTA_LVecBase2f([LVector2f(x*0,0) for x in range(t_count)]),
                       'alt_ranges':PTA_LVecBase2f([LVector2f(x*0,0) for x in range(t_count)]),
                       'red_ranges':PTA_LVecBase2f([LVector2f(x*0,0) for x in range(t_count)]),
                       'green_ranges':PTA_LVecBase2f([LVector2f(x*0,0) for x in range(t_count)]),
                       'blue_ranges':PTA_LVecBase2f([LVector2f(x*0,0) for x in range(t_count)])}
                       
        for i, terrain in enumerate(recipe['terrains']):
            for attr, val in list(terrain.items()):
                if attr.endswith("range"):
                    ranges_dict[attr+"s"][i] = LVector2f(*val)

        # Create terrain map with GPU.
        height_range = LVector2f(recipe['height_min'],recipe['height_max'])
        with GPU_Image(height_map, print_times=True) as gpu:
            terrain_img = gpu.generate_terrain_map(height_range=height_range,
                                                   col_map=col_map,
                                                   **ranges_dict)
            file_path = "{}/maps/{}_ter.png".format(recipe['path'], recipe['name'].lower())
            terrain_img.write(Filename(file_path))


class Planet:

    # Setup.
    def __init__(self, planet_spec):
        self.recipe = self.__get_Recipe(planet_spec)
        self.__dict__.update(self.recipe)
        self.path = "{}/{}".format(_path.BODIES, self.name)

        

    def __get_Recipe(self, planet_spec):
        if type(planet_spec) == type(""):
            # Shiva str.
            if "\n" in planet_spec:
                recipe = SC.compile_body_recipe(planet_spec)
            # Planet name.
            else:
                shv_path = Filename("{}/{}/{}.shv".format(_path.BODIES, planet_spec, planet_spec))
                with open(shv_path.toOsLongName()) as shv_file:
                    lines = shv_file.readlines()
                shiva_str = "".join(lines)
                recipe = SC.compile_body_recipe(shiva_str)
        # Recipe given.
        else:
            recipe = planet_spec
        
        return recipe


class Model:
    get_dict = {
        'vertex':(GeomVertexReader.getData3f, LPoint3f),
        'color':(GeomVertexReader.getData4f, LVector4f),
        'mapcoord':(GeomVertexReader.getData2f, LVector2f),
        'texcoord':(GeomVertexReader.getData2f, LVector2f)}
    set_dict = {
        'vertex':GeomVertexWriter.setData3f,
        'color':GeomVertexWriter.setData4f,
        'mapcoord':GeomVertexWriter.setData2f,
        'texcoord':GeomVertexWriter.setData2f}
    
    # Public.
    def read(self, field):
        return self.__read_Model(field)
    def modify(self, field, data=None):
        self.__modify_Model(field, data)
    def apply_textures(self, recipe, tex_dict):
        self.__apply_Textures(recipe, tex_dict)
    
    # Setup.
    def __init__(self, model_np):
        self.NP = model_np
        self.node = model_np.node()
            
    def __read_Model(self, field):
        data = []
        vdata = self.node.getGeom(0).getVertexData()
        reader = GeomVertexReader(vdata, field)
        get_data, v_type = self.get_dict[field]
        while not reader.isAtEnd():
            datum = v_type(get_data(reader))
            data.append(datum)
            
        return data

    def __modify_Model(self, field, data):
        geom = self.node.modifyGeom(0)
        vdata = geom.modifyVertexData()
        vwriter = GeomVertexWriter(vdata, field)
        vwriter.reserveNumRows(len(data))
        set_data = self.set_dict[field]
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
            


