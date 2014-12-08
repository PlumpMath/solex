# ===============
# swizzle_demo.py
# ===============

# Panda3d imports.
from panda3d.core import PNMImage, Filename
import direct.directbase.DirectStart

# Local imports.
from panda3d_gpu import GPU_Image, TimeIt, LVector3i

# Load ref image.
ref_img = PNMImage()
ref_img.read(Filename("earth_col.jpg"))

# Create 5 alternate versions of images with mixed up rgb vals.
rgb = "rgb"
mask_list = [(0,2,1),(1,0,2),(1,2,0),(2,0,1),(2,1,0)]
write_time = 0
with GPU_Image(ref_img, print_times=True) as gpu:
    for swizzle_mask in mask_list:
        mod_img = gpu.swizzle_rgb(swizzle_mask=LVector3i(*swizzle_mask))
        with TimeIt() as write_timer:
            a, b, c = swizzle_mask
            mod_img_name = "earth_col_{}{}{}.jpeg".format(rgb[a], rgb[b], rgb[c])
            mod_img.write(Filename(mod_img_name))
        write_time += write_timer.total_time

print()
print("  write: {}".format(round(write_time, 3)))

