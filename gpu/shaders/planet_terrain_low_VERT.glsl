#version 440

// Uniform inputs
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat3 p3d_NormalMatrix;
 
// Vertex inputs
in vec4 p3d_Vertex;
in vec4 p3d_Color;
 
// Output to fragment shader
out vec4 v_color;
out vec3 v_normal;

// Main.
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    v_normal = p3d_NormalMatrix * normalize(vec3(p3d_Vertex.xyz));
    v_color = p3d_Color;
}

