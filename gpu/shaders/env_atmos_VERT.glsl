#version 440

// Uniform.
uniform mat4 p3d_ModelViewProjectionMatrix;
 
// In.
in vec4 p3d_Vertex;

// Out.
 
 
// Main.
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
}

