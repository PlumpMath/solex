#version 440

// In.
in vec4 p3d_Vertex;
in vec2 mapcoord;
in vec2 texcoord;

// Uniform.
uniform sampler2D terrain_map;

// Out.
out vec3 verts;
out vec2 map_uvs;
out vec2 tex_uvs;
out int ter_inds;


// Main.
void main() {
    // Setup terrain vals for this vert.
    ter_inds = int(texture(terrain_map, mapcoord).r * 64);
    verts = p3d_Vertex.xyz;
    map_uvs = mapcoord;
    tex_uvs = texcoord;
}

