#version 440

// Uniform.
uniform vec3 light_vec;
uniform vec4 atmos_colour;
uniform float atmos_ceiling;
uniform float atmos_radius;
uniform vec4 atmos_vals;   // (cam_dist, cam_height, body_angle, atmos_angle)
uniform vec3 body_dir;

uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat3 p3d_NormalMatrix;
uniform mat4 p3d_ModelViewMatrix;

// In.
in vec4 v_vertex;
in vec3 v_vertex_dir;

// Out.
out vec4 o_color;


// Main.
void main()
{
    float cam_height = atmos_vals[1];
    if (cam_height > atmos_radius) {
        float cam_dist = atmos_vals[0];
        vec3 light_vec = (p3d_ModelViewProjectionMatrix * vec4(light_vec, 0.0)).xyz;
        vec3 normal = normalize(v_vertex.xyz);
        float brightness = clamp(dot(normal, light_vec),0.0,1.0);
        
        vec3 body_dir = (p3d_ModelViewMatrix * vec4(body_dir, 0.0)).xyz;
        float angle = degrees(acos(dot(v_vertex_dir,body_dir)));
        vec4 color = atmos_colour;
        float body_angle = atmos_vals[2];
        if (angle < body_angle) {
            discard;
        } else {
            float atmos_angle = atmos_vals[3];
            color.a = (atmos_angle-angle)/(atmos_angle-body_angle) * brightness;
            color *= brightness;
            o_color = color;
        }
    } else {
        discard;
    }
}

