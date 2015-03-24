#version 440

// Uniform.
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrix;
 
// In.
in vec4 p3d_Vertex;

// Out.
out vec4 v_vertex;
out vec3 v_vertex_dir;
 
 
// Main.
void main() {
    v_vertex = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    v_vertex_dir = normalize((p3d_ModelViewMatrix*p3d_Vertex).xyz);
    gl_Position = v_vertex;
}

