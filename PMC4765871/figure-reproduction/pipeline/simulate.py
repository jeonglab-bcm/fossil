"""Single-cell snapshot data from the OR-gate I1-FFL and the six-gene toggle switch.

Euler-Maruyama on the stochastic difference equations of supp. sections 2.1.1 and 2.2.1, with the
kinetic parameters of supp. Tables 3 and 5. The paper does not give the time step, the system noise,
the initial values, the FFL input process gX(t) or the toggle switch stopping rule; the values used
here are in params/simulation.json and recorded as assumptions in results.json.

Each cell is one realisation, sampled once at a time drawn uniformly on [0, t_stop] (supp. 2.2.7).
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PAR = json.loads((HERE / "params" / "simulation.json").read_text())


def act(x, k, h):
    x = np.maximum(x, 0.0)
    return 1.0 / (1.0 + (k / np.maximum(x, 1e-12)) ** h)


def rep(x, k, h):
    return 1.0 - act(x, k, h)


# ---------------------------------------------------------------- FFL


def ffl_input_drift(gx, p):
    lo, hi, r = p["gx_low"], p["gx_high"], p["gx_rate"]
    u = (gx - lo) / (hi - lo)
    return r * (gx - lo) * (1 - u)


def ffl_drift(g, p, k=None):
    """g: (..., 3) gX, gY, gZ. k: kinetic parameters (defaults: supp. Table 3)."""
    k = k or p["kinetics"]
    gx, gy, gz = g[..., 0], g[..., 1], g[..., 2]
    fx = act(gx, k["kp"], k["hp"])
    dx = ffl_input_drift(gx, p)
    dy = k["alpha"] * fx - k["lambda"] * gy
    if k.get("delete_gy"):
        # gY deleted: its term leaves the OR gate (Fig. 4, left: gZ falls towards 0, then rises
        # to 400 once gX crosses kappa+)
        dz = k["alpha"] * fx - k["lambda"] * gz
    else:
        dz = k["alpha"] * (fx + rep(gy, k["km"], k["hm"])) - k["lambda"] * gz
    return np.stack([dx, dy, dz], -1)


def ffl_paths(n, seed, p=None, k=None, noise=None, record=False):
    """n stochastic realisations; each stops when gX > stop. Returns stop times and, with
    record, the full paths on the step grid."""
    p = p or PAR["ffl"]
    k = k or p["kinetics"]
    rng = np.random.default_rng(seed)
    dt = p["dt"]
    s = p["sigma_s"] if noise is None else noise
    g = np.tile(np.array(p["initial"], float), (n, 1))
    if k.get("gz0") is not None:
        g[:, 2] = k["gz0"]
    alive = np.ones(n, bool)
    t_stop = np.full(n, np.nan)
    t = 0.0
    paths = [g.copy()] if record else None
    while alive.any() and t < p["t_max"]:
        dW = rng.standard_normal(g.shape)
        g = g + dt * ffl_drift(g, p, k) + s * np.sqrt(dt) * dW * alive[:, None]
        g[:, 0] = np.maximum(g[:, 0], p["gx_low"] + 1.0)  # the input stays above its floor
        t += dt
        if record:
            paths.append(g.copy())
        done = alive & (g[:, 0] > p["stop_gx"])
        t_stop[done] = t
        alive &= ~done
    return t_stop, (np.array(paths) if record else None)


def ffl_snapshot(n, seed, p=None):
    """Snapshot: each realisation sampled at t_a ~ U(0, t_stop). Returns (cells x 3), t_a, t_stop."""
    p = p or PAR["ffl"]
    rng = np.random.default_rng(seed)
    t_stop, paths = ffl_paths(n, int(rng.integers(2**31)), p, record=True)
    ta = rng.uniform(0, t_stop)
    idx = np.minimum((ta / p["dt"]).astype(int), len(paths) - 1)
    X = paths[idx, np.arange(n)]
    return X, ta, t_stop


def ffl_deterministic(T, p=None, k=None, dt=None):
    """Deterministic FFL (sigma_s = 0) on [0, T]."""
    p = p or PAR["ffl"]
    k = k or p["kinetics"]
    dt = dt or p["dt"]
    g = np.array(p["initial"], float)
    if k.get("gz0") is not None:
        g[2] = k["gz0"]
    out = [g.copy()]
    for _ in range(int(round(T / dt))):
        g = g + dt * ffl_drift(g, p, k)
        out.append(g.copy())
    return np.arange(len(out)) * dt, np.array(out)


# ---------------------------------------------------------------- toggle switch


def toggle_drift(g, k):
    A, B, C, D, E, F = (g[..., i] for i in range(6))
    a, lam = k["alpha"], k["lambda"]
    kp, hp, km, hm = k["kp"], k["hp"], k["km"], k["hm"]
    return np.stack([
        a * rep(B, km, hm) - lam * A,
        a * rep(A, km, hm) - lam * B,
        a * act(A, kp, hp) * rep(D, km, hm) - lam * C,
        a * act(A, kp, hp) * rep(C, km, hm) - lam * D,
        a * act(B, kp, hp) * rep(F, km, hm) - lam * E,
        a * act(B, kp, hp) * rep(E, km, hm) - lam * F,
    ], -1)


def toggle_symmetric_state(k):
    """A = B at the unstable symmetric steady state: lambda A = alpha km^h / (A^h + km^h)."""
    from scipy.optimize import brentq
    f = lambda A: k["alpha"] * k["km"] ** k["hm"] / (A ** k["hm"] + k["km"] ** k["hm"]) - k["lambda"] * A
    return brentq(f, 1e-6, k["alpha"] / k["lambda"])


def toggle_paths(n, seed, p=None):
    p = p or PAR["toggle"]
    k = p["kinetics"]
    rng = np.random.default_rng(seed)
    dt, s = p["dt"], p["sigma_s"]
    a0 = toggle_symmetric_state(k)
    g = np.zeros((n, 6))
    g[:, :2] = a0
    alive = np.ones(n, bool)
    t_stop = np.full(n, np.nan)
    t = 0.0
    paths = [g.copy()]
    while alive.any() and t < p["t_max"]:
        dW = rng.standard_normal(g.shape)
        g = g + (dt * toggle_drift(g, k) + s * np.sqrt(dt) * dW) * alive[:, None]
        t += dt
        paths.append(g.copy())
        done = alive & (g[:, 2:].max(1) > p["stop_late"])
        t_stop[done] = t
        alive &= ~done
    t_stop[np.isnan(t_stop)] = t
    return t_stop, np.array(paths)


def toggle_snapshot(n, seed, p=None, obs_noise=None):
    """obs_noise: None, ('add', sigma) or ('mul', sigma) (supp. section 2.2.3).
    Returns cells x 6 (observed), the noise-free values, t_a, t_stop and the fate of each cell
    (index of the late gene that won: 0 C, 1 D, 2 E, 3 F)."""
    p = p or PAR["toggle"]
    rng = np.random.default_rng(seed)
    t_stop, paths = toggle_paths(n, int(rng.integers(2**31)), p)
    ta = rng.uniform(0, t_stop)
    idx = np.minimum((ta / p["dt"]).astype(int), len(paths) - 1)
    X = paths[idx, np.arange(n)]
    last = paths[np.minimum((t_stop / p["dt"]).astype(int), len(paths) - 1), np.arange(n)]
    fate = last[:, 2:].argmax(1)
    Xo = X.copy()
    if obs_noise:
        kind, sg = obs_noise
        if kind == "add":
            Xo = X + rng.normal(0, sg, X.shape)
        else:
            Xo = X * rng.normal(1, sg, X.shape)
    return Xo, X, ta, t_stop, fate


if __name__ == "__main__":
    which = sys.argv[1]
    if which == "ffl":
        X, ta, ts = ffl_snapshot(PAR["ffl"]["n_cells"], PAR["ffl"]["seed"])
        print(X.min(0), X.max(0), ts.mean())
    else:
        Xo, X, ta, ts, fate = toggle_snapshot(PAR["toggle"]["n_cells"], PAR["toggle"]["seed"])
        print(X.min(0), X.max(0), ts.mean(), np.bincount(fate))
