#version 440

// In.
in vec3 verts[];
in vec2 map_uvs[];
in vec2 tex_uvs[];

// Out.
layout(vertices = 3) out;
out vec3 tc_verts[];
out vec2 tc_map_uvs[];
out vec2 tc_tex_uvs[];
patch out float dist;

// Uniform.
uniform mat4 p3d_ModelViewMatrix;
uniform vec3 geom_lod[8];
uniform vec2 tex_lod[4];

// Main.
void main()
{
    // Establish distance of triangle from camera.
    float dist_0 = length(p3d_ModelViewMatrix*vec4(verts[0],1.0));
    float dist_1 = length(p3d_ModelViewMatrix*vec4(verts[1],1.0));
    float dist_2 = length(p3d_ModelViewMatrix*vec4(verts[2],1.0));
    float dist = (dist_0+dist_1+dist_2) / 3.0;
    
    // Find tess levels based on cam dist.
    float tess_inner = 0;
    float tess_outer = 1;
    for (int i=0; i<8; i++) {
        if (dist < geom_lod[i].x) {
            tess_inner = geom_lod[i].y;
            tess_outer = geom_lod[i].z;
            break;
        }
    }
    
    // Find tex lod from cam dist.  // FIX
    float tex_multi = 1;
    for (int i=0; i<4; i++) {
        if (dist < tex_lod[i].x) {
            tex_multi = tex_lod[i].y;
            break;
        }
    }
    
    // Set tess levels.
    gl_TessLevelInner[0] = tess_inner;
    gl_TessLevelOuter[0] = tess_outer;
    gl_TessLevelOuter[1] = tess_outer;
    gl_TessLevelOuter[2] = tess_outer;
    
    // Map inputs to outputs.
    tc_verts[gl_InvocationID] = verts[gl_InvocationID];
    tc_map_uvs[gl_InvocationID] = map_uvs[gl_InvocationID];
    tc_tex_uvs[gl_InvocationID] = tex_uvs[gl_InvocationID] * tex_multi;
}

