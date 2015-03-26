#version 440

// Uniform.
uniform vec4 atmos_colour;
uniform mat4 p3d_ModelViewProjectionMatrix;

// In.

// Out.
out vec4 o_color;


// Main.
void main()
{
    // Basic colour.
    o_color = atmos_colour;
}

