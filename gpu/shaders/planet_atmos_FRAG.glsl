#version 440

// Uniform.
uniform vec3 light_vec;
uniform vec4 atmos_colour;
uniform float atmos_ceiling;
uniform float atmos_radius;
uniform vec4 atmos_vals;   // (cam_dist, fade_multi, body_angle, atmos_angle)
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
    // The goal is to have the brightness of the atmosphere nimbus peak right
    // at the surface of the planet (body_angle) and fade off exponentially (**4)
    // toward the edge of the atmosphere (atmos_angle). These angles,
    // along with 'pixel_angle' are in reference to a vec leading from
    // render(0,0,0) (camera pos) to the center of the planet.
    vec3 body_dir = (p3d_ModelViewMatrix * vec4(body_dir,0.0)).xyz;
    float pixel_angle = degrees(acos(dot(v_vertex_dir,body_dir)));
    float body_angle = atmos_vals[2];
    float atmos_angle = atmos_vals[3];
    
    // Discard any pixels behind the planet.
    if (pixel_angle < body_angle) {
        discard;
    // Use pixels surrounding planet to render atmospheric nimbus.
    } else {
        // Basic colour.
        vec4 color = atmos_colour;
        float fade_multi = atmos_vals[1];
        // Brightness is determined by the angle of 'light_vec' compared (dot)
        // to the angle of the vertex normal. The brightness equation results
        // in a value from 0.5 to 1.0 allowing planet to mainain a partial
        // nimbus even when the star is behind the camera. The nimbus fades
        // out according to 'fade_multi' as the camera descends below the
        // 'atmos_ceiling' height and is gone at half this height.
        vec3 light_vec = (p3d_ModelViewMatrix * vec4(light_vec,0.0)).xyz;
        float brightness = ((dot(v_vertex_dir,light_vec)/4.0)+.75) * fade_multi;
        // Opacity is determined by the pixel angle compared to atmos and body angles.
        color.a = pow((atmos_angle-pixel_angle)/(atmos_angle-body_angle),4);
        color *= brightness;
        o_color = color;
    }
}

