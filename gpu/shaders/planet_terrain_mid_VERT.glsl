#version 440

// Uniform.
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat3 p3d_NormalMatrix;
 
// In.
in vec4 p3d_Vertex;
in vec2 mapcoord;
 
// Out.
out vec3 v_normal;
out vec2 v_texcoord;

// Main.
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    v_normal = p3d_NormalMatrix * normalize(vec3(p3d_Vertex.xyz));
    v_texcoord = mapcoord;
}

