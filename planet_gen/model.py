# ================
# Solex - model.py
# ================

# System imports.
from ast import literal_eval
from math import sqrt, degrees, asin

# Panda3d imports.
from panda3d.core import GeomVertexWriter, GeomVertexReader
from panda3d.core import GeomVertexData, GeomVertexFormat, GeomVertexArrayFormat
from panda3d.core import Geom, GeomNode, GeomTriangles, GeomPatches
from panda3d.core import NodePath, LODNode, Texture, TextureStage, InternalName
from panda3d.core import LVector2f, LVector3f, LVector4f, LPoint3f, PTA_LVecBase2f
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
    
    def __init__(self, recs):
        self.RECS = recs
        self.vformat = self.__generate_Vformat()
        
    
    def __build_Spheres(self):
        sphere = Hexasphere()
        sphere.coords = []
        for pt in sphere.pts:
            sphere.coords.append(self.__get_Pt_Coords(pt))
        
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
        for pt, uv, coords, in zip(sphere.pts, sphere.uvs, sphere.coords):
            vertices.addData3f(*pt)
            mapcoords.addData2f(*coords)
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
        mu = lon/360
        # v / latitude.
        lat = degrees(asin(z))
        mv = (lat+90) / 180
        return mu, mv

    def __generate_Vformat(self):
        # Vformat.
        array = GeomVertexArrayFormat()
        array.addColumn(InternalName.make("vertex"), 3, Geom.NTFloat32, Geom.CPoint)
        array.addColumn(InternalName.make("mapcoord"), 2, Geom.NTFloat32, Geom.CTexcoord)
        array.addColumn(InternalName.make("texcoord"), 2, Geom.NTFloat32, Geom.CTexcoord)
        vformat = GeomVertexFormat()
        vformat.addArray(array)
        vformat = GeomVertexFormat.registerFormat(vformat)
        return vformat

        
class Planet_Builder:
    
    def init(self, shiva_str):
        return self.__init_Planet(shiva_str)
    def build(self, planet_np, recipe=None):
        self.__build_Planet(planet_np, recipe)
    def save(self, planet_np, name):
        model_path = "{}/{}/{}.bam".format(_path.PLANET_GEN, name, name)
        planet_np.writeBamFile(model_path)
    def export(self, planet_np, name):
        model_path = "{}/{}.bam".format(_path.BODIES, name)
        planet_np.writeBamFile(model_path)



    def __init_Planet(self, shiva_str):
        # Interpret shiv str into recipe.
        recipe = SC.compile(shiva_str)
        
        # Planet and LOD nodes.
        planet_np = NodePath("{}_model".format(recipe['name']))
        lod_node = LODNode("far_lod")
        lod_np = NodePath(lod_node)
        lod_np.reparentTo(planet_np)
        # Recipe NP.
        recipe_np = NodePath("{}")
        recipe_np.setName(repr(recipe))
        recipe_np.reparentTo(planet_np)
        
        # Build models.
        far = 9999999999
        for rec, near in recipe['far_lod']:
            with TimeIt("far LOD {} @ {}: ".format(rec, near)):
                # Load specified sphere model for each far LOD.
                sphere_path = "{}/sphere_{}.bam".format(_path.MODELS, rec)
                sphere_np = loader.loadModel(sphere_path).getChild(0)
                sphere_np.reparentTo(lod_np)
                lod_node.addSwitch(far, near)
                # Create and setup model.
                sphere = Model(sphere_np)
                pts = sphere.read("vertex")
                pts = list(map(lambda pt: pt*recipe['radius'], pts))
                sphere.modify("vertex", pts)
                far = near
                
        return planet_np
                
    def __build_Planet(self, planet_np, recipe):
        # Update existing 'planet_recipe' with with new vals in 'recipe'.
        recipe_np = planet_np.getChild(1)
        planet_recipe = literal_eval(recipe_np.getName())
        
        # If a recipe is given then update the current one.
        if recipe:
            planet_recipe.update(recipe)
            recipe_np.setName(repr(planet_recipe))
        # If no recipe is given then use the current one.
        else:
            recipe = planet_recipe
        
        '''# Height map.
        if "height_map" in recipe:
            self.__set_Map_Texture(planet_np, recipe, recipe['height_map'], 0)
        
        # Generate normal map if requested.
        if "normal_map" in recipe:
            if recipe['normal_map'] == True:
                recipe = self.__build_Normal_Map(recipe)
            self.__set_Map_Texture(planet_np, recipe, recipe['normal_map'], 1)
        
        # Colour map.
        if "colour_map" in recipe:
            self.__set_Map_Texture(planet_np, recipe, recipe['colour_map'], 2)'''
        
        # Terrains.
        if "terrains" in recipe:
            with TimeIt("terrains"): pass
                ## self.__build_Terrain_Map(planet_np, recipe)
        
    def __build_Normal_Map(self, recipe):
        # Load ref image.
        ref_img = PNMImage()
        height_map_path = "{}/maps/{}".format(recipe['path'], recipe['height_map'])
        ref_img.read(Filename(height_map_path))
        
        # Create normal map from height map with GPU.
        with GPU_Image(ref_img, print_times=True) as gpu:
            depth = recipe['max_elevation'] - recipe['min_elevation']
            norm_img = gpu.generate_normal_map(depth=depth)
            norm_img.write(Filename("{}/maps/earth_norm.jpg".format(recipe['path'])))
        
        recipe['normal_map'] = "earth_norm.jpg"
        return recipe
        
    def __build_Terrain_Map(self, planet_np, recipe):
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
        min_height = recipe['radius']+recipe['min_elevation']
        height_range = recipe['max_elevation']-recipe['min_elevation']
        with GPU_Image(height_map, print_times=True) as gpu:
            terrain_img = gpu.generate_terrain_map(radius=recipe['radius'],
                                                   min_height=min_height,
                                                   height_range=height_range,
                                                   col_map=col_map,
                                                   norm_map=norm_map,
                                                   **ranges_dict)
        
            terrain_img.write(Filename("{}/maps/earth_ter.png".format(recipe['path'])))

    def __assign_Terrains(self, model, recipe, final_rec=False):
        tex_dict = {}
        _set_col, _set_tex = False, False
        _sea_on = "sea_colour" in recipe
        enum_terrains = list(enumerate(recipe['terrains']))
        
        i = 0
        pts = list(map(lambda pt: pt*radius, pts))
        height_img = PNMImage()
            
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
            'mapcoord':(GeomVertexReader.getData2f, LVector2f),
            'texcoord':(GeomVertexReader.getData2f, LVector2f)}
            
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
            'mapcoord':GeomVertexWriter.setData2f,
            'texcoord':GeomVertexWriter.setData2f}
            
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
            


