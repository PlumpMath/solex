#version 440

// Uniform.
uniform sampler2D height_map;
uniform sampler2D terrain_map;
uniform vec4 terrain_specs;

// In.
in vec4 p3d_Vertex;
in vec2 mapcoord;
in vec2 texcoord;

// Out.
out vec3 verts;
out vec2 map_uvs;
out vec2 tex_uvs;
out int ter_inds;       // For FRAG shader
out float tess_vals;    // For TESC shader.
out float heights;      // For TESC shader.


// Main.
void main()
{
    // Basic vals.
    verts = p3d_Vertex.xyz;
    map_uvs = mapcoord;
    tex_uvs = texcoord;
    // Setup terrain and tess density vals for this vert.
    vec4 map_col = texture(terrain_map, mapcoord);
    ter_inds = int(map_col.r * 64);
    tess_vals = map_col.g * 64;
    // Height.
    float elev_range = terrain_specs[1];
    float map_val = texture(height_map, mapcoord).r;
    heights = map_val*elev_range;
}

