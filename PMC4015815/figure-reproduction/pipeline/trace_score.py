"""Two-way trace scores (Paper2Repro figure-scoring): the share of published trace pixels within
`tol` px of ours, and of ours within `tol` px of the published; the score is the smaller."""
import numpy as np
from scipy import ndimage


def two_way(published_mask, our_mask, tol=2.0):
    if not published_mask.any() or not our_mask.any():
        return {"published_near_ours": 0.0, "ours_near_published": 0.0, "score": 0.0}
    d_ours = ndimage.distance_transform_edt(~our_mask)
    d_pub = ndimage.distance_transform_edt(~published_mask)
    a = float(np.mean(d_ours[published_mask] <= tol))
    b = float(np.mean(d_pub[our_mask] <= tol))
    return {"published_near_ours": round(a, 5), "ours_near_published": round(b, 5),
            "score": round(min(a, b), 5)}
