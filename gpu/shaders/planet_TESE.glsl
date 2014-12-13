#version 440

// In.
layout(triangles, equal_spacing, ccw) in;
in vec3 tc_verts[];
in vec2 tc_map_uvs[];
in vec2 tc_tex_uvs[];

// Out.
out vec3 te_normal;
out vec4 te_color;
out vec2 te_tex_uv;
out vec3 te_eye_vec;
out float te_dist;

// Uniform.
uniform float radius;
uniform vec4 terrain_specs;
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
    te_normal = normalize(vert);
    te_color = vec4(0.4,0.4,0.4,1.0);
    te_tex_uv = vec2(0.0);
    
    // Get vert map UV for height and colour.
    #if defined height_map_on || defined colour_map_on
    vec2 muv_A = gl_TessCoord.s * tc_map_uvs[0];
    vec2 muv_B = gl_TessCoord.t * tc_map_uvs[1];
    vec2 muv_C = gl_TessCoord.p * tc_map_uvs[2];
    vec2 map_uv = (muv_A+muv_B+muv_C);
    #endif
    
    // Height Mapping.
    #ifdef height_map_on
    float min_height = terrain_specs[0];
    float elev_range = terrain_specs[1];
    float map_val = texture(height_map, map_uv)[0];
    float map_height = min_height + (map_val*elev_range);
    float elev_ratio = map_height / radius;
    vert = vert * elev_ratio;
    // Normal mapping.
    vec3 map_norm = texture(normal_map, map_uv).xyz;
    te_normal = normalize(p3d_NormalMatrix*(map_norm+te_normal));
    te_eye_vec = -(p3d_ModelViewMatrix * vec4(vert, 1.0)).xyz;
    #endif
    
    // Set final vert pos.
    gl_Position = p3d_ModelViewProjectionMatrix * vec4(vert, 1.0);
    te_dist = length(gl_Position);
    
    // Color mapping.
    #ifdef colour_map_on
    te_color = texture(col_map, map_uv);
    #endif
    
    // Texture mapping.
    #ifdef tex_on
    vec2 tuv_A = gl_TessCoord.s * tc_tex_uvs[0];
    vec2 tuv_B = gl_TessCoord.t * tc_tex_uvs[1];
    vec2 tuv_C = gl_TessCoord.p * tc_tex_uvs[2];
    te_tex_uv = (tuv_A+tuv_B+tuv_C);
    #endif
}

