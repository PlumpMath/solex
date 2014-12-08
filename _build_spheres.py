# =========================
# Solex - _build_spheres.py
# =========================

RECS = 8

if __name__ == "__main__":
    from planet_gen.model import Sphere_Builder
    sb = Sphere_Builder(RECS)
    sb.build_spheres()

