# =========================
# Solex - _build_spheres.py
# =========================

RECS = 8
MODE = "tris"  # 'tris' or 'patches'.

if __name__ == "__main__":
    from planet_gen.model import Sphere_Builder
    sb = Sphere_Builder(RECS, MODE)
    sb.build_spheres()

