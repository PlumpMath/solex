#version 440

// Uniform.
uniform vec3 light_vec;
uniform float ambient_val;
uniform sampler2D colour_map;

uniform mat4 p3d_ModelViewMatrix;
uniform mat3 p3d_NormalMatrix;

// In.
in vec3 v_normal;
in vec2 v_texcoord;

// Out.
out vec4 o_color;

// Main.
void main()
{
    // Texture.
    vec4 tex_color = texture(colour_map, v_texcoord);
    
    // Lighting.
    vec3 f_light_vec = (p3d_ModelViewMatrix * vec4(light_vec, 0.0)).xyz;
    float intensity = max(dot(v_normal, f_light_vec), 0.0);
    vec4 ambient = vec4(tex_color.rgb*ambient_val, 1.0);
    
    // Final output color.
    o_color = max(tex_color, ambient) * intensity;
}

