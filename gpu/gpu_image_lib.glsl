#version 430
// ==============
// image_lib.glsl
// ==============
// 
// - a library of shaders to be used with GPU_Image context manager
//   to manipulate images on the GPU.


// Each function in this image lib works with at least one ref_tex 
// and exactly one mod_tex so we declare these along with some other
// useful global constants.
layout (rgba8) uniform readonly image2D ref_tex;
uniform writeonly image2D mod_tex;
const ivec2 max_coords = imageSize(ref_tex)-1;  // img_size in coord form.


// --------
// get_nbrs - private
// --------
// 
//   border_map bm = border_map(int, int, int, int);
//   nbr_struct nbrs = nbr_struct(bm);
// 
// 
// Create and return a struct that maps the coords of neighboring pixels
// to the 8 basic compass directions. This is useful for functions that require
// pixels to access values of surrounding pixels since it removes the
// complication of dealing with borders between workgroups. It also takes
// care of handling the actual image borders by either clamping or wrapping
// based on values given in the 'border_map' input.
struct nbr_struct {
    ivec2 nw; ivec2 n; ivec2 ne;
    ivec2 w;  ivec2 c; ivec2 e;
    ivec2 sw; ivec2 s; ivec2 se;
};

// A 'border_map' is expected as an input to this function. The 4 values
// correspond to row or column indices that each respective image border should
// reference as its buffer sampling row/col. For images that wrap/tile each border
// should wrap to its opposite (i.e. left=max_coords.x; right=0); non-wrapping
// images can just have each border map to itself (left=0).
struct border_map {
    int top;
    int right;
    int bottom;
    int left;
};

// Pre made border_maps for common situations.
border_map BM_TILE = border_map(max_coords.y, 0, 0, max_coords.y);     // v and h wrap.
border_map BM_SPHERE = border_map(0, 0, max_coords.y, max_coords.x);   // only h wrap.

// Function def.
nbr_struct get_nbrs(border_map bm) {

    // Global coords (image).
    ivec2 g_coords = ivec2(gl_GlobalInvocationID.xy);
    int gx = g_coords.x;
    int gy = g_coords.y;
 
    // Fill in neighboring coord values for the current pixel.
    nbr_struct nbrs = nbr_struct(
        ivec2(gx-1,gy-1), ivec2(gx,gy-1), ivec2(gx+1,gy-1),
        ivec2(gx-1,gy),   ivec2(gx,gy),   ivec2(gx+1,gy),
        ivec2(gx-1,gy+1), ivec2(gx,gy+1), ivec2(gx+1,gy+1)
    );
    
    // Handle image borders by mapping to rows/columns given in 'bm'.
    if (gx == 0) {
        nbrs.nw.x = bm.left;
        nbrs.w.x = bm.left;
        nbrs.sw.x = bm.left;}
    else if (gx == max_coords.x) {
        nbrs.ne.x = bm.right;
        nbrs.e.x = bm.right;
        nbrs.se.x = bm.right;}
    if (gy == 0) {
        nbrs.nw.y = bm.top;
        nbrs.n.y = bm.top;
        nbrs.ne.y = bm.top;}
    else if (gy == max_coords.y) {
        nbrs.sw.y = bm.bottom;
        nbrs.s.y = bm.bottom;
        nbrs.se.y = bm.bottom;}
    
    return nbrs;
}

// -----------
// swizzle_rgb
// -----------
// 
// Accepts an image and returns a colour swizzled version based
// on the "swizzle_mask" given.
// 
// py usage:        with GPU_Image(ref_img) as gpu:
//                      gpu.swizzle_rgb(swizzle_mask=LVector3i(int,int,int)>)
// 
// ref_img:         PNMImage  - height_map from which to extract normals.
// swizzle_mask:    LVector3i - swizzle order as vec of indices.
//                                -> LVector3i(1,2,0) -> pixel.gbr
//                                -> indices must be >= -2 and <= 2

#ifdef swizzle_rgb
uniform ivec3 swizzle_mask;

void main () {
    ivec2 coords = ivec2(gl_GlobalInvocationID.xy);
    vec4 pixel = imageLoad(ref_tex, coords);
    float rgb[3] = float[3](pixel.r,pixel.g,pixel.b);
    // Apply swizzle mask.
    vec4 out_pixel = vec4(0.0,0.0,0.0,1.0);
    out_pixel.r = rgb[swizzle_mask.r];
    out_pixel.g = rgb[swizzle_mask.g];
    out_pixel.b = rgb[swizzle_mask.b];
    imageStore(mod_tex, coords, out_pixel);
}
#endif

// -------------------
// generate_normal_map
// -------------------
// 
// Generates a normal map from a height map using 'depth' to establish
// the z range of the psuedo_mesh we generate to find the normal.
// 
// py usage:    with GPU_Image(height_map) as gpu:
//                  norm_map = gpu.generate_normal_map(depth=<FloatType>)
// 
// height_map:      PNMImage - height_map from which to extract normals.
// depth:           float    - max height of terrain in units.

#ifdef generate_normal_map
uniform float depth;
shared vec3 psuedo_mesh[gl_WorkGroupSize.x+2][gl_WorkGroupSize.y+2];

// psuedo_mesh - to generate normals we'll create a psuedo terrain mesh with the
// x, y values matching the local invocation x, y values and the z being the 
// brightness of the pixel mulitplied by the 'depth' input. We then use a standard
// normal generation algorithm on this mesh to find the normal vector for the 
// output pixel at this point (xyz -> rgb).
// 
//        nw     n     ne
//          +----+----+
//          |  / | \  |             A - norm of tri (c, n, w)
//          | / A|B \ |             B - norm of tri (c, e, n)
//        w +--- c ---+ e           C - norm of tri (c, s, e)
//          | \ C|D / |             D - norm of tri (c, w, s)
//          |  \ | /  |
//          +----+----+             c normal = normalize((1+(A+B+C+D))/2)
//        sw     s     se

void main() {
    // Global coords (image).
    ivec2 g_coords = ivec2(gl_GlobalInvocationID.xy);
    int gx = g_coords.x;
    int gy = g_coords.y;
    
    // Local coords (workgroup).
    ivec2 l_coords = ivec2(gl_LocalInvocationID.xy);
    int lx = l_coords.x+1;  // Adjust by 1 to account for buffer col to left.
    int ly = l_coords.y+1;  // Adjust by 1 to account for buffer row above.
    
    // Since we need to be able to sample across workgroup seams we have to get
    // a copy of nbrs from 'get_nbrs'. The majority of pixels in the workgroup will
    // not even reference this object; the amount that do halves with every
    // doubling of the workgroup dimensions: 16x16->24%, 32x32->12%, 64x64->%6, ...
    nbr_struct nbrs = get_nbrs(BM_SPHERE);
    
    // Next we need to create 'psuedo_mesh'.
    
    // Every pixel will add a pt to psuedo_mesh corresponding to itself. We
    // just sample the 'r' value since all 3 colour values are identical.
    float z = imageLoad(ref_tex, ivec2(gx,gy)).r * depth; // c
    vec3 c_pt = vec3(lx,ly,z);
    psuedo_mesh[lx][ly] = c_pt;
    
    // Border pixels need to add a second pt to psuedo_mesh to make a buffer
    // row/col. This is why the size of psuedo_mesh is always 2 units greater
    // in each dimension (x, y) than the workgroup. We find these buffer
    // pixels by using the coords laid out in 'nbrs'.
    
    // Left border.
    if (lx == 1) {
        float z = imageLoad(ref_tex, nbrs.w).r * depth;   // w
        psuedo_mesh[0][ly] = vec3(0,ly,z);}
    // Right border.
    else if (lx == gl_WorkGroupSize.x-1) {
        float z = imageLoad(ref_tex, nbrs.e).r * depth;   // e
        psuedo_mesh[gl_WorkGroupSize.x+1][ly] = vec3(gl_WorkGroupSize.x+1,ly,z);}
    // Top border.
    if (ly == 1) {
        float z = imageLoad(ref_tex, nbrs.n).r * depth;   // n
        psuedo_mesh[lx][0] = vec3(lx,0,z);}
    // Bottom border.
    else if (ly == gl_WorkGroupSize.y-1) {
        float z = imageLoad(ref_tex, nbrs.s).r * depth;   // s
        psuedo_mesh[lx][gl_WorkGroupSize.y+1] = vec3(lx,gl_WorkGroupSize.y+1,z);}
        
    // Use a barrier to ensure that psuedo_mesh is complete before
    // getting values from it.
    barrier();
    
    // Get the vectors that define the 4 psuedo-tris we need.
    vec3 n_vec = normalize(c_pt-psuedo_mesh[lx][ly-1]);    // n
    vec3 w_vec = normalize(c_pt-psuedo_mesh[lx-1][ly]);    // w
    vec3 s_vec = normalize(c_pt-psuedo_mesh[lx][ly+1]);    // s
    vec3 e_vec = normalize(c_pt-psuedo_mesh[lx+1][ly]);    // e
    
    // Get the normals for the face of each tri.
    vec3 norm_A = cross(w_vec, n_vec);
    vec3 norm_B = cross(s_vec, w_vec);
    vec3 norm_C = cross(e_vec, s_vec);
    vec3 norm_D = cross(n_vec, e_vec);
    
    // Get normal by averaging four tri normals.
    vec3 avg_norm = normalize(norm_A+norm_B+norm_C+norm_D);
    vec3 norm = normalize((1.0+avg_norm)/2.0);  // put into rgb form.
    imageStore(mod_tex, g_coords, vec4(norm, 1.0));
}
#endif

// --------------------
// generate_terrain_map
// --------------------
// 
// Generates a terrain map from by referencing a height map, colour_map
// and a uv map.
// 
// py usage:    with GPU_Image(height_map) as gpu:
//                  terrain_map = gpu.generate_terrain_map(col_map=<PNMImage>,
//                                                         norm_map=<PNMImage>,
//                                                         lat_ranges=<PTA_VecBase2f>,
//                                                         ...)
// 
// col_map:         PNMImage - colour_map of planet.
// norm_map:        PNMImage - norm_map of planet.
// ''_ranges:       PTA_VecBase2f - ranges for each target condition.

#ifdef generate_terrain_map
uniform float radius;
uniform float min_height;
uniform float height_range;
layout (rgba8) uniform readonly image2D col_map;
layout (rgba8) uniform readonly image2D norm_map;
uniform vec2 lat_ranges[2];
uniform vec2 lon_ranges[2];
uniform vec2 alt_ranges[2];
uniform vec2 red_ranges[2];
uniform vec2 green_ranges[2];
uniform vec2 blue_ranges[2];

shared int type_mesh[gl_WorkGroupSize.x+2][gl_WorkGroupSize.y+2];

// Func to find terrain for pixel.
int get_terrain_type(ivec2 g_coords) {
    int terrain_type = 10;
    
    // Get altitude of current pixel.
    float map_val = imageLoad(ref_tex, g_coords).r;
    float alt = (min_height+(map_val*height_range)) - radius;

    // Search for qualifying terrain.
    bool qualifies;
    for (int i=0; i<lat_ranges.length(); i++) {
        qualifies = false;
        // Altitude.
        if (alt_ranges[i] != 0) {
            if (alt >= alt_ranges[i].x && alt < alt_ranges[i].y) {
                qualifies = true;}
            else {
                qualifies = false;
            }
        }
        // If pixel qualifies for this terrain add it to o_color.
        if (qualifies == true) {
            terrain_type = i;
            break;
        }
    }
    return terrain_type;
}

void main() {
    // Global coords (image).
    ivec2 g_coords = ivec2(gl_GlobalInvocationID.xy);
    int gx = g_coords.x;
    int gy = g_coords.y;
    
    // Local coords (workgroup).
    ivec2 l_coords = ivec2(gl_LocalInvocationID.xy);
    int lx = l_coords.x+1;  // Adjust by 1 to account for buffer col to left.
    int ly = l_coords.y+1;  // Adjust by 1 to account for buffer row above.
    
    // Get nbrs.
    nbr_struct nbrs = get_nbrs(BM_SPHERE);
    
    // Set terrain type.
    int terrain_type = get_terrain_type(g_coords);
    type_mesh[lx][ly] = terrain_type;
    // Handle workgroup border cases.
    if (lx == 1) {
        type_mesh[0][ly] = get_terrain_type(nbrs.w);}
    else if (lx == gl_WorkGroupSize.x-1) {
        type_mesh[gl_WorkGroupSize.x+1][ly] = get_terrain_type(nbrs.e);}
    if (ly == 1) {
        type_mesh[lx][0] = get_terrain_type(nbrs.n);}
    else if (ly == gl_WorkGroupSize.y-1) {
        type_mesh[lx][gl_WorkGroupSize.y+1] = get_terrain_type(nbrs.s);}
    
    // 'type_mesh' must have values for whole workgroup before we access it.
    barrier();
    
    // Map main and blend terrain types.
    vec4 o_color = vec4(float(terrain_type)/64,0,0,1);
    int blend_count = 0;
    ivec4 nbr_types = ivec4(type_mesh[lx][ly-1], type_mesh[lx][ly+1],
                            type_mesh[lx-1][ly], type_mesh[lx+1][ly]);
    ivec4 used_types = ivec4(terrain_type);
    for (int i=0; i<4; i++) {
        int n_type = nbr_types[i];
        if (n_type == used_types[0] || n_type == used_types[1] ||
            n_type == used_types[2] || n_type == used_types[3]) {
            continue;
        }
        if (n_type != terrain_type) {
            o_color[blend_count+1] = float(n_type)/64;
            used_types[i+1] = n_type;
            blend_count++;
            if (blend_count == 3) {
                break;
            }
        }
    }
    imageStore(mod_tex, g_coords, o_color);
}

#endif



