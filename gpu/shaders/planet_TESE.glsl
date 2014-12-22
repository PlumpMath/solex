#version 440

// In.
layout(triangles, fractional_even_spacing, ccw) in;
in vec3 tc_verts[];
in vec2 tc_map_uvs[];
in vec2 tc_tex_uvs[];
in int tc_ter_inds[];

// Out.
out float te_dist;
out vec3 te_normal;
out vec4 te_color;
out vec2 te_tex_uv;
out vec3 te_eye_vec;
out flat ivec3 te_ter_inds;
out vec3 te_ter_blends;

// Uniform.
uniform float radius;
uniform vec4 terrain_specs; // (min_height, elev_range, terrain_count, ?)
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrix;
uniform mat3 p3d_NormalMatrix;
uniform sampler2D height_map;
uniform sampler2D normal_map;
uniform sampler2D col_map;


// Main.
void main()
{
    // Establish tesselated vert basic attrs.
    vec3 pA = gl_TessCoord.s * tc_verts[0];
    vec3 pB = gl_TessCoord.t * tc_verts[1];
    vec3 pC = gl_TessCoord.p * tc_verts[2];
    vec3 vert = (pA+pB+pC);
    
    // Get vert map UV for height and colour.
    vec2 muv_A = gl_TessCoord.s * tc_map_uvs[0];
    vec2 muv_B = gl_TessCoord.t * tc_map_uvs[1];
    vec2 muv_C = gl_TessCoord.p * tc_map_uvs[2];
    vec2 map_uv = (muv_A+muv_B+muv_C);
    
    // Height Mapping.
    float min_height = terrain_specs[0];
    float elev_range = terrain_specs[1];
    float map_val = texture(height_map, map_uv)[0];
    float map_height = min_height + (map_val*elev_range);
    float elev_ratio = map_height / radius;
    vert = vert * elev_ratio;
    // Normal mapping.
    te_normal = normalize(vert);
    vec3 map_norm = texture(normal_map, map_uv).xyz;
    te_normal = normalize(p3d_NormalMatrix*(map_norm+te_normal));
    te_eye_vec = -(p3d_ModelViewMatrix * vec4(vert, 1.0)).xyz;
    
    // Set final vert pos.
    gl_Position = p3d_ModelViewProjectionMatrix * vec4(vert, 1.0);
    te_dist = length(gl_Position);
    
    // Color mapping.
    te_color = texture(col_map, map_uv);
    
    // Terrain.
    te_ter_inds = ivec3(tc_ter_inds[0],tc_ter_inds[1],tc_ter_inds[2]);
    te_ter_blends = gl_TessCoord;
    
    // Texture uvs.
    vec2 tuv_A = gl_TessCoord.s * tc_tex_uvs[0];
    vec2 tuv_B = gl_TessCoord.t * tc_tex_uvs[1];
    vec2 tuv_C = gl_TessCoord.p * tc_tex_uvs[2];
    te_tex_uv = (tuv_A+tuv_B+tuv_C);
}

