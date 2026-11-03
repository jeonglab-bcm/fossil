"""LIMPIC 1.1 (Mantini et al. 2007, Additional File 1) ported from MATLAB to Python.

Each function follows the MATLAB file of the same name statement by statement; indices
are shifted from 1-based to 0-based and nothing else is changed. check_port.py compares
the port with the authors' code run in GNU Octave.

Two points where the MATLAB code cannot run as published:
- read_txt.m opens a file dialog; read_txt() here takes a path.
- find_intervals.m calls kurtosis(block, 0) and keeps blocks with a value below 1. MATLAB's
  kurtosis is 3 for Gaussian noise and never below 1, so no block passes and
  rem_baseline.m fails. The authors' run used an excess kurtosis (0 for Gaussian noise):
  with it the peaks of Figs 7 and 8 come back at the published positions and heights.
"""

import numpy as np


def read_txt(path):
    """read_txt.m: two columns (m/z, intensity); the first 50 points are discarded.

    Lines that do not hold two numbers are skipped. The only such line in the supplied
    data is line 32768 of SOL_5_TXT/SOL_calib_08e.txt, damaged in the publisher's archive.
    """
    rows = []
    with open(path) as f:
        for line in f:
            parts = line.split()
            if len(parts) == 2:
                rows.append((float(parts[0]), float(parts[1])))
    data = np.array(rows)
    return data[50:, 1], data[50:, 0]


def kurtosis(v):
    """Normalized excess kurtosis (biased estimator)."""
    v = v - v.mean()
    return np.mean(v**4) / np.mean(v**2) ** 2 - 3


def kaiser(y, f, k=2):
    """kaiser.m: a Savitzky-Golay smoother (degree k, frame f), uniform-data branch.

    The name notwithstanding, this is the moving least-squares polynomial filter of
    MATLAB's smooth(..., 'sgolay'), not a Kaiser-window FIR filter.
    """
    k = min(k, f)
    n = len(y)
    f = int(np.floor(f))
    f = min(f, n)
    f = f - (f - 1) % 2  # subtract 1 if the frame is even
    if f <= k:
        return y.copy()
    hf = (f - 1) // 2
    t = np.arange(-hf, hf + 1, dtype=float)
    v = np.vander(t, k + 1, increasing=True)
    q, _ = np.linalg.qr(v)
    b = q @ q[hf, :]
    ymid = np.convolve(y, b)[:n]  # filter(b, 1, y)
    ybegin = q[:hf, :] @ (q.T @ y[:f])
    yend = q[hf + 1 :, :] @ (q.T @ y[n - f :])
    return np.concatenate([ybegin, ymid[f - 1 :], yend])


def prepro(w, factor=20):
    """prepro.m: smooth, reverse, smooth again, reverse back."""
    xt = kaiser(w, round_half_away(factor / 2))[::-1]
    return kaiser(xt, round_half_away(factor / 2))[::-1]


def round_half_away(a):
    """MATLAB round: halves go away from zero."""
    return int(np.sign(a) * np.floor(abs(a) + 0.5))


def resample_sig(sig, x, step=0.25):
    """resample_sig.m: linear interpolation onto a regular m/z grid."""
    val1 = step * np.ceil(x[0] / step)
    val2 = step * np.fix(x[-1] / step)
    xn = val1 + step * np.arange(int(round((val2 - val1) / step)) + 1)
    return np.interp(xn, x, sig), xn


def find_intervals(sig, x, division=400):
    """find_intervals.m: blocks without significant peaks (kurtosis < 1, mean below the spectrum mean)."""
    nblocks = len(sig) // division
    blocks = [slice(i * division, (i + 1) * division) for i in range(nblocks)]
    kx = np.array([kurtosis(sig[b]) for b in blocks])
    x_int = np.array([x[b].mean() for b in blocks])
    v_int = np.array([sig[b].mean() for b in blocks])
    m_int = np.array([sig[b].min() for b in blocks])
    s_int = np.array([sig[b].std(ddof=1) for b in blocks])
    thres = 1
    ref_val = sig.mean()
    keep = np.flatnonzero((kx < thres) & (v_int < ref_val))
    return keep, x_int[keep], v_int[keep], m_int[keep], s_int[keep]


def _interp_ends(x, x_int, y_int):
    """interp1([x(1) x_int x(end)], [y_int(1) y_int 0], x)"""
    return np.interp(x, np.r_[x[0], x_int, x[-1]], np.r_[y_int[0], y_int, 0.0])


def rem_baseline(sig, x, m_int, x_int):
    """rem_baseline.m: baseline through the block minima, pinned to 0 at the last m/z."""
    baseline = _interp_ends(x, x_int, m_int)
    return sig - baseline, baseline


def normalize(sig, x, ref_peak, ppm=300, amp=1000):
    """normalize.m: scale so the maximum within +-300 ppm of the calibrant is 1000."""
    p1 = np.argmin(np.abs(x - ref_peak * (1 - ppm / 1e6)))
    p2 = np.argmin(np.abs(x - ref_peak * (1 + ppm / 1e6)))
    norm_factor = amp / sig[p1 : p2 + 1].max()
    return norm_factor * sig, norm_factor


def estimate_noise(x, s_int, b_int, x_int, iupac_thres, norm_factor):
    """estimate_noise.m: norm_factor * (mean - min + 3 * sd), interpolated between blocks."""
    sigma = _interp_ends(x, x_int, s_int)
    base = _interp_ends(x, x_int, b_int)
    return norm_factor * (base + iupac_thres * sigma)


def prctile(a, p):
    """MATLAB prctile: sorted values sit at percentiles 100*(i-0.5)/n, linear in between."""
    a = np.sort(a)
    n = len(a)
    return np.interp(p, 100 * (np.arange(1, n + 1) - 0.5) / n, a)


def find_peaks(sig, noise_lev, peak_width):
    """find_peaks.m: local maxima (Yasui), then the noise-level and slope tests."""
    d = np.diff(sig)
    col = len(sig)
    pos = []
    for i in range(peak_width, col - peak_width):  # MATLAB i = peak_width : col-peak_width-1
        j = i - 1  # 0-based index of diff_sig(i)
        flag1 = d[j] * d[j + 1] <= 0
        flag2 = np.all(d[j - peak_width + 1 : j] > 0)
        flag3 = d[j] >= 0 and d[j + 1] <= 0
        flag4 = np.all(d[j + 2 : j + peak_width] < 0)
        if flag1 and flag2 and flag3 and flag4:
            pos.append(j + 1)  # MATLAB pos i+1
    pos = [p for p in pos if not sig[p] < noise_lev[p]]
    base = int(np.ceil(0.5 * peak_width))
    height_thres = 0.5 * base * prctile(np.abs(d), 75)
    keep = []
    for p in pos:
        p1, p2 = p - peak_width, p + peak_width
        if p1 >= 0 and p2 <= col - 1:
            if sig[p] - 0.5 * (sig[p1] + sig[p2]) < height_thres:
                continue
        keep.append(p)
    return np.array(keep, dtype=int)


def single_spectrum(path, factor=20):
    """single_spectrum.m with the authors' settings; returns every intermediate signal."""
    r = {}
    r["w"], r["x"] = read_txt(path)
    r["wx"] = prepro(r["w"], factor)
    step = 0.25
    r["wxr"], r["xr"] = resample_sig(r["wx"], r["x"], step)
    mz_block = 100
    r["int"], r["x_int"], r["v_int"], r["m_int"], r["s_int"] = find_intervals(
        r["wxr"], r["xr"], round_half_away(mz_block / step)
    )
    r["wxrb"], r["baseline"] = rem_baseline(r["wxr"], r["xr"], r["m_int"], r["x_int"])
    r["wxrbn"], r["norm_factor"] = normalize(r["wxrb"], r["xr"], 16952.25)
    r["noise_lev"] = estimate_noise(r["xr"], r["s_int"], r["v_int"] - r["m_int"], r["x_int"], 3, r["norm_factor"])
    r["peak_point"] = find_peaks(r["wxrbn"], r["noise_lev"], int(np.ceil(0.5 / step)))
    r["peak_mass"] = r["xr"][r["peak_point"]]
    r["peak_intensity"] = r["wxrbn"][r["peak_point"]]
    return r


def multiple_spectra(peaks, ppm=300, pdr=0.5):
    """multiple_spectra.m: cluster peaks across spectra.

    peaks: list of (peak_mass, peak_intensity) per spectrum, in reading order.
    Returns class m/z (lista_value), the spectra x classes amplitude matrix (lista_amp),
    the number of peaks per class (lista_nel) and the selected classes (lista_nel > pdr*n).
    """
    nspectra = len(peaks)
    data = np.vstack([np.c_[m, a, np.full(len(m), i)] for i, (m, a) in enumerate(peaks)])
    order = np.argsort(data[:, 0], kind="stable")
    data = data[order]
    value = list(data[:, 0])
    nel = [1] * len(value)
    amp = []
    for _, a, s in data:
        col = np.zeros(nspectra)
        col[int(s)] = a
        amp.append(col)
    i = 1  # MATLAB i = 2
    while i < len(value) - 1:  # MATLAB while i < length(lista_value)
        value_b, v, value_p = value[i - 1], value[i], value[i + 1]
        db = v - value_b
        dp = value_p - v
        thres = v * ppm / 1e6
        pat = amp[i] > 0
        if not np.all(amp[i - 1][pat] == 0):
            db = np.inf
        if not np.all(amp[i + 1][pat] == 0):
            dp = np.inf
        if db <= dp and db < thres:
            value[i - 1] = (nel[i] * v + nel[i - 1] * value_b) / (nel[i - 1] + nel[i])
            nel[i - 1] += nel[i]
            amp[i - 1] = amp[i - 1] + amp[i]
            del value[i], nel[i], amp[i]
        elif db > dp and dp < thres:
            value[i + 1] = (nel[i] * v + nel[i + 1] * value_p) / (nel[i + 1] + nel[i])
            nel[i + 1] += nel[i]
            amp[i + 1] = amp[i + 1] + amp[i]
            del value[i], nel[i], amp[i]
        else:
            i += 1
    value = np.array(value)
    nel = np.array(nel)
    selection = np.flatnonzero(nel > pdr * nspectra)
    return value, np.array(amp).T, nel, selection
