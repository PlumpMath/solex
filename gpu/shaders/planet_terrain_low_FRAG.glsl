#version 440

// In.
in vec3 v_normal;
in vec4 v_color;

// Uniform.
uniform mat4 p3d_ModelViewMatrix;
uniform mat3 p3d_NormalMatrix;
uniform vec3 light_vec;
uniform float ambient_val;

// Out.
out vec4 o_color;

// Main.
void main()
{
    // Lighting.
    vec3 f_light_vec = (p3d_ModelViewMatrix * vec4(light_vec, 0.0)).xyz;
    float intensity = max(dot(v_normal, f_light_vec), 0.0);
    vec4 ambient = vec4(ambient_val, ambient_val, ambient_val, 1.0);
    
    // Final output color.
    o_color = max(v_color, ambient) * intensity;
}
