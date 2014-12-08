# =================
# gen_normal_map.py
# =================

# Panda3d imports.
from panda3d.core import PNMImage, Filename
import direct.directbase.DirectStart

# Local imports.
from panda3d_gpu import GPU_Image, TimeIt

# Load ref image.
ref_img = PNMImage()
ref_img.read(Filename("earth_height.jpg"))

# Create normal map from height map.
with GPU_Image(ref_img, print_times=True) as gpu:
    norm_img = gpu.generate_normal_map(depth=72)

with TimeIt("  write") as write_timer:
    norm_img.write(Filename("earth_norm.jpg"))


