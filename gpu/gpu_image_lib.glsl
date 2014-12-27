#version 430
// ==============
// image_lib.glsl
// ==============
// 
// - a library of shaders used with GPU_Image context manager to
//   manipulate images on the GPU using the Panda3D game engine.


// Each function in this image lib works with at least one ref_tex 
// and exactly one mod_tex so we declare these along with some other
// useful global constants and objects.
layout (rgba8) uniform readonly image2D ref_tex;
uniform writeonly image2D mod_tex;

// Image invocation coords.
const ivec2 G_COORDS = ivec2(gl_GlobalInvocationID.xy);
const int GX = G_COORDS.x;
const int GY = G_COORDS.y;

// Work group invocation coords.
const ivec2 L_COORDS = ivec2(gl_LocalInvocationID.xy);
const int LX = L_COORDS.x;
const int LY = L_COORDS.y;

// Image size constants.
const ivec2 G_SIZE = imageSize(ref_tex)-1;  // img_size in coord form.
const int GX_SIZE = G_SIZE.x;
const int GY_SIZE = G_SIZE.y;

// Work group size constants.
const uint LX_SIZE = gl_WorkGroupSize.x;
const uint LY_SIZE = gl_WorkGroupSize.y;

// Height mesh obj (needs to filled with a call to 'generate_height_mesh').
shared vec3 height_mesh[gl_WorkGroupSize.x+2][gl_WorkGroupSize.y+2];

// --------
// get_nbrs - private
// --------
// 
// Usage:
// 
//   border_map bm = border_map(uint, uint, uint, uint);
//   nbr_struct nbrs = get_nbrs(bm);
// 
// Return a struct that maps the coords of neighboring pixels to the
// 8 basic compass directions. This is useful for functions that require
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
border_map BM_TILE = border_map(GY, 0, 0, GY);     // v and h wrap.
border_map BM_SPHERE = border_map(0, 0, GY, GX);   // only h wrap.

// Function def.
nbr_struct get_nbrs(border_map bm) {
 
    // Fill in neighboring coord values for the current pixel.
    nbr_struct nbrs = nbr_struct(
        ivec2(GX-1,GY-1), ivec2(GX,GY-1), ivec2(GX+1,GY-1),
        ivec2(GX-1,GY),   ivec2(GX,GY),   ivec2(GX+1,GY),
        ivec2(GX-1,GY+1), ivec2(GX,GY+1), ivec2(GX+1,GY+1)
    );
    
    // Handle image borders by mapping to rows/columns given in 'bm'.
    if (GX == 0) {
        nbrs.nw.x = bm.left;
        nbrs.w.x = bm.left;
        nbrs.sw.x = bm.left;}
    else if (GX == GX_SIZE) {
        nbrs.ne.x = bm.right;
        nbrs.e.x = bm.right;
        nbrs.se.x = bm.right;}
    if (GY == 0) {
        nbrs.nw.y = bm.top;
        nbrs.n.y = bm.top;
        nbrs.ne.y = bm.top;}
    else if (GY == GY_SIZE) {
        nbrs.sw.y = bm.bottom;
        nbrs.s.y = bm.bottom;
        nbrs.se.y = bm.bottom;}
    
    return nbrs;
}

// ---------------
// get_height_mesh - private
// ---------------
// 
// Usage:
//   generate_height_mesh(float depth);
//   mesh_pt = height_mesh[LX+1][LX+1];
// 
// Fill values of 'height_mesh' for the current workgroup for functions that
// work with height maps. It produces a mesh that includes a buffer row around
// the outside of the workgroup to help with producing seamless results.

void generate_height_mesh(vec2 height_range) {
    // Mesh coords.
    int mx = LX + 1;  // Adjust by 1 to account for buffer col to left.
    int my = LY + 1;  // Adjust by 1 to account for buffer row above.
    
    // Since we need to be able to sample across workgroup seams
    // we have to get a copy of nbrs from 'get_nbrs'.
    nbr_struct nbrs = get_nbrs(BM_SPHERE);
        
    // Every pixel will add a height value for itself.
    float depth = height_range.y - height_range.x;
    float z = imageLoad(ref_tex, ivec2(GX,GY)).r * depth + height_range.x; // c
    vec3 c_pt = vec3(mx,my,z);
    height_mesh[mx][my] = c_pt;
    
    // Border pixels need to add a second pt (and third for corner pixels) to
    // the mesh to fill out the buffer rows/cols. This is why the size of 'height_mesh'
    // is always 2 units greater in each dimension (x, y) than the workgroup.
    // We find these buffer pixels by using the coords laid out in 'nbrs'.
    if (mx == 1) {
        z = imageLoad(ref_tex, nbrs.w).r * depth + height_range.x;   // w
        height_mesh[0][my] = vec3(0,my,z);}
    else if (mx == LX_SIZE) {
        z = imageLoad(ref_tex, nbrs.e).r * depth + height_range.x;   // e
        height_mesh[LX_SIZE+1][my] = vec3(LX_SIZE+1,my,z);}
    if (my == 1) {
        z = imageLoad(ref_tex, nbrs.n).r * depth + height_range.x;   // n
        height_mesh[mx][0] = vec3(mx,0,z);}
    else if (my == LY_SIZE) {
        z = imageLoad(ref_tex, nbrs.s).r * depth + height_range.x;   // s
        height_mesh[mx][LY_SIZE+1] = vec3(mx,LX_SIZE+1,z);}
        
    // Corner pixels must also add a fourth pt to the mesh to fill out the mesh's
    // own corner values.
    if (mx == 1 && my == 1) {
        z = imageLoad(ref_tex, nbrs.nw).r * depth + height_range.x;  // nw
        height_mesh[0][0] = vec3(0,0,z);}
    else if (mx == LX_SIZE && my == 1) {
        z = imageLoad(ref_tex, nbrs.ne).r * depth + height_range.x;  // ne
        height_mesh[LX_SIZE+1][0] = vec3(LX_SIZE+1,0,z);}
    else if (mx == 1 && my == LY_SIZE) {
        z = imageLoad(ref_tex, nbrs.sw).r * depth + height_range.x;  // sw
        height_mesh[0][LY_SIZE+1] = vec3(0,LY_SIZE+1,z);}
    else if (mx == LX_SIZE && my == LY_SIZE) {
        z = imageLoad(ref_tex, nbrs.se).r * depth + height_range.x;  // se
        height_mesh[LX_SIZE+1][LY_SIZE+1] = vec3(LX_SIZE+1,LY_SIZE+1,z);}
        
    // Use a barrier to ensure that 'height_mesh' is complete before
    // calling functions attempt to use values from it.
    barrier();
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
    // Get ref image's colour for this pixel.
    vec4 pixel = imageLoad(ref_tex, G_COORDS);
    float rgb[3] = float[3](pixel.r,pixel.g,pixel.b);
    
    // Apply swizzle mask.
    vec4 out_pixel = vec4(0.0,0.0,0.0,1.0);
    out_pixel.r = rgb[swizzle_mask.r];
    out_pixel.g = rgb[swizzle_mask.g];
    out_pixel.b = rgb[swizzle_mask.b];
    imageStore(mod_tex, G_COORDS, out_pixel);
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
uniform vec2 height_range;

// We'll use the global object 'height_mesh' to generate normal values using
// a standard normal generation algorithm on this mesh to find the normal vector
// for the output pixel at this point (xyz -> rgb).
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
    // Generate height mesh.
    generate_height_mesh(height_range);
    // Mesh coords.
    int mx = LX + 1;  // Adjust by 1 to account for buffer col to left.
    int my = LY + 1;  // Adjust by 1 to account for buffer row above.
    
    // Get the vectors that define the 4 psuedo-tris we need.
    vec3 c_pt = height_mesh[mx][my];
    vec3 n_vec = normalize(c_pt-height_mesh[mx][my-1]);    // n
    vec3 w_vec = normalize(c_pt-height_mesh[mx-1][my]);    // w
    vec3 s_vec = normalize(c_pt-height_mesh[mx][my+1]);    // s
    vec3 e_vec = normalize(c_pt-height_mesh[mx+1][my]);    // e
    
    // Get the normals for the face of each tri.
    vec3 norm_A = cross(w_vec, n_vec);
    vec3 norm_B = cross(s_vec, w_vec);
    vec3 norm_C = cross(e_vec, s_vec);
    vec3 norm_D = cross(n_vec, e_vec);
    
    // Get normal by averaging four tri normals.
    vec3 avg_norm = normalize(norm_A+norm_B+norm_C+norm_D);
    vec3 norm = normalize((1.0+avg_norm)/2.0);  // put into rgb form.
    imageStore(mod_tex, G_COORDS, vec4(norm, 1.0));
}
#endif

// --------------------
// generate_terrain_map
// --------------------
// 
// Generates a terrain map from by referencing a height map, colour_map
// and a uv map
// 
// py usage:    
// 
//   with GPU_Image(height_map) as gpu:
//       terrain_map = gpu.generate_terrain_map(depth=<float>,
//                                              col_map=<PNMImage>,
//                                              lat_ranges=<PTA_VecBase2f>,
//                                              ...)
// 
// depth:           float - height range for generating 'height_mesh'.
// col_map:         PNMImage - colour_map of planet.
// ''_ranges:       PTA_VecBase2f - ranges for each target condition.

#ifdef generate_terrain_map
layout (rgba8) uniform readonly image2D col_map;
layout (rgba8) uniform readonly image2D norm_map;
uniform vec2 height_range;

// Terrain qualification ranges.
uniform vec2 lat_ranges[2];
uniform vec2 lon_ranges[2];
uniform vec2 alt_ranges[2];
uniform vec2 red_ranges[2];
uniform vec2 green_ranges[2];
uniform vec2 blue_ranges[2];


// Find terrain index by using pixel's properties to qualify it for a terrain
// (based on range uniforms). Convert this index to a (0-1) float value for
// the terrain map's 'r' field.
float get_terrain_val() {
    float terrain_val = 1; // Pixel's with no terrain show up full red.
    int mx = LX + 1;
    int my = LY + 1;
    
    // Get properties of current pixel.
    float alt = height_mesh[mx][my].z;  // altitude

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
            terrain_val = float(i) / 64;
            break;
        }
    }
    return terrain_val;
}

// Find this pixel's tesselation density value by comparing the heights of all
// neighboring pixels to assess the elevation change for verts that would reference
// this pixel and thus the need for tesselation at that point (a flat plain needs
// essentially no tesselation whereas a mountain peak needs full tesselation.) The
// density value translates to the 'outer_tess' level in the tess control shader;
// the 'inner' level should be computed as the avg of the tri's 3 outer tess levels
// in the same control shader.

float get_density_val() {
    int mx = LX + 1;
    int my = LY + 1;
    // First get the total height variation
    float ch = height_mesh[mx][my].z;
    float density_tot = (abs(ch-height_mesh[mx-1][my-1].z) +   // nw
                         abs(ch-height_mesh[mx][my-1].z) +     // n
                         abs(ch-height_mesh[mx+1][my-1].z) +   // ne
                         abs(ch-height_mesh[mx+1][my].z) +     // e
                         abs(ch-height_mesh[mx+1][my+1].z) +   // se
                         abs(ch-height_mesh[mx][my+1].z) +     // s
                         abs(ch-height_mesh[mx-1][my+1].z) +   // sw
                         abs(ch-height_mesh[mx-1][my].z));     // w
    
    float density_val = min(density_tot/8/64, 1);
    return density_val; 
}

void main() {
    // Gen height mesh.
    generate_height_mesh(height_range);
    // Set terrain type (r).
    float terrain_val = get_terrain_val();
    // Set tesselation density value (g).
    float density_val = get_density_val();
    // Map main and blend terrain types.
    vec4 o_color = vec4(terrain_val,density_val,0,1);
    imageStore(mod_tex, G_COORDS, o_color);
}

#endif



