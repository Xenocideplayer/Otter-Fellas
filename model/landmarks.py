ADULT = dict(scale=1.0, head_y=0.44, muzzle_z=0.165, bib_low=0.22, hand_x=0.205, tail_tip_z=-0.54,
             ear=(0.083,0.497,0.035), nose=(0.0,0.441,0.226), whisker=(0.034,0.42,0.212),
             eye=(0.038,0.497,0.147), eye_r=0.0115,
             tail_start_z=-0.17, muzzle_c=(0.0,0.43,0.2), sash=(0.27,0.85,0.034), clasp_x=0.0)
CHILD = dict(scale=0.62, head_y=0.262, muzzle_z=0.088, bib_low=0.13, hand_x=0.115, tail_tip_z=-0.265,
             ear=(0.048,0.305,0.03), nose=(0.0,0.2645,0.128), whisker=(0.0238,0.2505,0.1135),
             eye=(0.024,0.299,0.087), eye_r=0.0076,
             tail_start_z=-0.105, muzzle_c=(0.0,0.255,0.115), sash=None, clasp_x=0.0)


def _scaled(L, c, k):
    """Move head landmarks to match the enlarged head (scaled by k around c)."""
    import numpy as np
    out = dict(L)
    c = np.asarray(c)
    for key in ("ear", "nose", "whisker", "eye", "muzzle_c"):
        out[key] = tuple(c + (np.asarray(L[key]) - c) * k)
    out["head_y"] = float(c[1] + (L["head_y"] - c[1]) * k)
    out["muzzle_z"] = float(c[2] + (L["muzzle_z"] - c[2]) * k)
    out["eye_r"] = L["eye_r"] * k * 1.18   # bigger, more expressive eyes
    return out


import otter_shape as _os
ADULT = _scaled(ADULT, *_os.ADULT_FEATURES["head_scale"][:2])
CHILD = _scaled(CHILD, *_os.CHILD_FEATURES["head_scale"][:2])
