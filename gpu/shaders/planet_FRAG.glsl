#version 440

// In.
in vec3 te_normal;
in vec4 te_color;
in vec2 te_tex_uv;
in vec3 te_eye_vec;
in float te_dist;

// Out.
out vec4 o_color;

// Uniform.
uniform mat4 p3d_ModelViewMatrix;
uniform sampler2D p3d_Texture0;
uniform sampler2D p3d_Texture1;
uniform vec3 light_dir;
uniform float ambient_val;
uniform vec3 tex_blend;


// Main.
void main()
{
    vec3 eye_vec = te_eye_vec;
    vec3 light_vec = (p3d_ModelViewMatrix * vec4(light_dir, 0.0)).xyz;
    float intensity = max(dot(te_normal, light_vec), 0.0) * 4.0;
    vec4 color = te_color;
    
    vec4 tex_col_near = color * texture(p3d_Texture0, te_tex_uv);
    vec4 tex_col_far = color * texture(p3d_Texture1, te_tex_uv);
    float blend = smoothstep(tex_blend.x, tex_blend.y, te_dist);
    vec4 tex_col = mix(tex_col_near, tex_col_far, blend) * 2;
    color = mix(color, tex_col, clamp(1-(te_dist/tex_blend.z), 0, 1));
        
        
    vec4 ambient = vec4(ambient_val, ambient_val, ambient_val, 1.0);
    o_color = max(color, ambient) * intensity;
}

// Only calc spec value if fragment is lit.
    /* if (intensity > 0.0) {
        // Use half vec between light and eye pov.
        vec3 half_vec = normalize(light_vec + eye_vec);
        float intSpec = max(dot(half_vec, v_norm), 0.0);
        spec = p3d_Material.emission * pow(intSpec, p3d_Material.shininess);
    } */
