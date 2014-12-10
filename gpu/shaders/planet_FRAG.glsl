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
uniform vec3 light_dir;
uniform float ambient_val;
uniform vec3 tex_lod[4];
uniform sampler2DArray tex_array;  // temp for mono terrain prototype.


// Main.
void main()
{
    // Lighting vars.
    vec3 eye_vec = te_eye_vec;
    vec3 light_vec = (p3d_ModelViewMatrix * vec4(light_dir, 0.0)).xyz;
    float intensity = max(dot(te_normal, light_vec), 0.0) * 4.0;
    vec4 color = te_color;
    // Terrain texturing.
    float tex_master_blend = clamp(((1200-te_dist)/1200), 0, 1);
    vec4 tex_col = vec4(0);  // Track blending of texture values 
    if (tex_master_blend > 0) {
        float prev_far = 0.0;
        // Check each tex lod level and blend in each one's contribution
        // based on this frags distance from the camera (te_dist).
        for (int i=0; i<4; i++) {
            vec3 lod = tex_lod[i];  // lod.x -> near, lod.y -> far, lod.z -> tex_uv_multi
            float next_near = tex_lod[i+1].x;
            if (te_dist > lod.x && te_dist <= lod.y) {
                vec4 current_tex_col = texture(tex_array, vec3(te_tex_uv*lod.z, i));
                float blend = 1.0;  // No lod overlap.
                if (te_dist < prev_far) {
                    // Blend between this lod and prev lod level.
                    blend = smoothstep(lod.x, prev_far, te_dist);}
                else if (te_dist > next_near) {
                    // Blend between this lod and next lod level.
                    blend = 1.0 - smoothstep(next_near, lod.y, te_dist);}
                // Add this lod layer's contribution to tex_col.
                tex_col += current_tex_col * blend;
                prev_far = lod.y;
            }
        }
        // Texture contribution to o_color.
        color = mix(color, normalize(tex_col*color)*2.0, tex_master_blend);
    } 
    // Basic o_color.
    vec4 ambient = vec4(ambient_val, ambient_val, ambient_val, 1.0);
    o_color = max(color, ambient) * intensity;
}
