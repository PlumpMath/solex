#version 440

// In.
in vec3 te_normal;
in vec4 te_color;
in vec2 te_tex_uv;
in vec3 te_eye_vec;
in float te_dist;
in flat ivec3 te_ter_inds;
in vec3 te_ter_blends;

// Out.
out vec4 o_color;

// Uniform.
uniform mat4 p3d_ModelViewMatrix;
uniform vec3 light_dir;
uniform float ambient_val;
uniform vec4 terrain_specs; // (min_height, elev_range, terrain_count, ?)
uniform vec3 tex_lod[4];
uniform sampler2DArray near_tex;
uniform sampler2DArray far_tex;

// Find texture color based on its blending requirements (based
// on the terrain of each vertex of the pixel's tri). Having this 
// as a function is both cleaner and the only way to switch between
// using 'near_tex' and 'far_tex' as the array to sample from.
vec4 sample_texture(sampler2DArray tex_array, float multi) {
    // The terrain layer indices found by the vert shader.
    int ti_A = te_ter_inds[0];
    int ti_B = te_ter_inds[1];
    int ti_C = te_ter_inds[2];
    vec4 sample_col;
    // The most common and simplest case is when all 3 verts of the
    // tri share the same terrain; no blending required:
    if (ti_A == ti_B && ti_B == ti_C) {
        sample_col = texture(tex_array, vec3(te_tex_uv*multi, ti_A));}
    // The next 3 cases all are the '2 vs 1' scenarios; blending is
    // based on the blend value given (in 'te_ter_blends') for the vertex
    // with only one terrain. A vs B,C:
    else if (ti_A != ti_B && ti_B == ti_C) {
        vec4 ncol_A = texture(tex_array, vec3(te_tex_uv*multi, ti_A));
        vec4 ncol_B = texture(tex_array, vec3(te_tex_uv*multi, ti_B));
        sample_col = mix(ncol_B, ncol_A, te_ter_blends[0]);}
    // B vs C,A:
    else if (ti_B != ti_C && ti_C == ti_A) {
        vec4 ncol_B = texture(tex_array, vec3(te_tex_uv*multi, ti_B));
        vec4 ncol_C = texture(tex_array, vec3(te_tex_uv*multi, ti_C));
        sample_col = mix(ncol_C, ncol_B, te_ter_blends[1]);}
    // C vs A,B:
    else if (ti_C != ti_A && ti_A == ti_B) {
        vec4 ncol_C = texture(tex_array, vec3(te_tex_uv*multi, ti_C));
        vec4 ncol_A = texture(tex_array, vec3(te_tex_uv*multi, ti_A));
        sample_col = mix(ncol_A, ncol_C, te_ter_blends[2]);}
    // The rarest case is when all 3 vertices are different terrains.
    // Blending is a fairly simple mix of all 3 given blend values:
    else if (ti_A != ti_B && ti_B != ti_A) {
        vec4 ncol_A = texture(tex_array, vec3(te_tex_uv*multi, ti_A));
        vec4 ncol_B = texture(tex_array, vec3(te_tex_uv*multi, ti_B));
        vec4 ncol_C = texture(tex_array, vec3(te_tex_uv*multi, ti_C));
        sample_col = (ncol_A*te_ter_blends[0]) +
                     (ncol_B*te_ter_blends[1]) +
                     (ncol_C*te_ter_blends[2]);
    }
    return sample_col;
}


// Main.
void main()
{   
    // Start with basic color sampled by the tess eval shader.
    vec4 color = te_color;
    
    // Only add terrain texturing contribution if this pixel is in
    // tex LOD range; use 'tex_master_blend' to fade in texturing.
    float lod_radius = tex_lod[3][1];
    float tex_master_blend = clamp(((lod_radius-te_dist)/tex_lod[3][1]), 0, 1);
    if (tex_master_blend > 0) {
        vec4 tex_col = vec4(0);  // Accumulate required texture values.
        vec4 mix_tex_col;   // Hold return value from func 'sample_texture'.
        
        // Used to track which LOD levels to blend between.
        float prev_far = 0.0;
        float next_near;
        vec3 lod; // near, far, tex_uv_multi
        
        // Loop through LOD levels and add texture value from any
        // LOD level that qualifies (max 2).
        for (int i=0; i<tex_lod.length(); i++) {
            lod = tex_lod[i];  // Values relevant to this LOD level.
            next_near = tex_lod[i+1].x;
            
            // Check if the pixel's cam distance qualifies it for this level.
            if (te_dist > lod.x && te_dist <= lod.y) {
                // The nearest LOD level use texture from 'near_tex';
                // all subsequent levels use texture from 'far_tex'.
                if (i == 0) {mix_tex_col = sample_texture(near_tex, lod.z);}
                else {mix_tex_col = sample_texture(far_tex, lod.z);}
                
                // Blend between levels if this pixel is in overlap zone.
                float blend = 1.0;  // No lod overlap.
                if (te_dist < prev_far) {
                    // Blend between this lod and prev lod level.
                    blend = smoothstep(lod.x, prev_far, te_dist);}
                else if (te_dist > next_near) {
                    // Blend between this lod and next lod level.
                    blend = 1.0 - smoothstep(next_near, lod.y, te_dist);}
                // Add layer's contribution to tex_col (or 2 if overlap).
                tex_col += (mix_tex_col*blend);
                prev_far = lod.y;
            }
        }
        // Total texture contribution to o_color.
        color = mix(color, normalize(tex_col*color)*2.0, tex_master_blend);
    }
    // Lighting values.
    vec3 eye_vec = te_eye_vec;
    vec3 light_vec = (p3d_ModelViewMatrix * vec4(light_dir, 0.0)).xyz;
    float intensity = max(dot(te_normal, light_vec), 0.0) * 4.0;
    vec4 ambient = vec4(ambient_val, ambient_val, ambient_val, 1.0);
    
    // Final output color.
    o_color = max(color, ambient) * intensity;
}
