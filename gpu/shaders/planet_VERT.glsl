#version 440

// In.
in vec4 p3d_Vertex;
in vec2 mapcoord;
in vec2 texcoord;

// Out.
out vec3 verts;
out vec2 map_uvs;
out vec2 tex_uvs;


// Main.
void main() {
    verts = p3d_Vertex.xyz;
    map_uvs = mapcoord;
    tex_uvs = texcoord;
}

