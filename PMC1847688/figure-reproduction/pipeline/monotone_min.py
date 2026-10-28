"""The monotone-minimum baseline of Fig. 5 (the comparison method, not LIMPIC's).

The paper credits it to APEX, CENTROID and CROMWELL and gives no settings. CROMWELL first
denoises with an undecimated discrete wavelet transform, then takes the minimum. These
settings reproduce the published blue curve (99.99% of its pixels within 2 px); they were
found by searching wavelet (db2, db4, db8, sym4), levels (3 to 9), threshold (2 to 10
times the noise) and hard or soft thresholding, and the neighbouring settings miss badly:

- undecimated DWT, Daubechies 8-tap wavelet (pywt "db4", CROMWELL's daubcqf(8)), 9 levels;
- hard threshold at 6 times the noise, noise = median |finest detail| / 0.6745;
- running minimum from the low-mass end, over 5 to 20 kDa.
"""

import numpy as np
import pywt

WAVELET, LEVELS, THRESHOLD = "db4", 9, 6


def denoise(y, wavelet=WAVELET, level=LEVELS, k=THRESHOLD):
    n = len(y)
    pad = (-n) % (2**level)
    coeffs = pywt.swt(np.pad(y, (0, pad), mode="edge"), wavelet, level=level, trim_approx=True)
    sigma = np.median(np.abs(coeffs[-1])) / 0.6745
    coeffs = [coeffs[0]] + [pywt.threshold(c, k * sigma, "hard") for c in coeffs[1:]]
    return pywt.iswt(coeffs, wavelet)[:n]


def monotone_minimum(x, y, upper=20000):
    """Running minimum of the denoised spectrum, from the low-mass end up to `upper` Da."""
    keep = x <= upper
    return x[keep], np.minimum.accumulate(denoise(y)[keep])
