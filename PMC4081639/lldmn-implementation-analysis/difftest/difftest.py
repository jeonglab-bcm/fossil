"""Differential test: authors' lldmn binary vs a reimplementation of the decompiled logic vs exact Eq. (6).

Usage: uv run --with mpmath==1.3.0 python -I difftest.py <x86_64 driver>
"""
import math
import random
import subprocess
import sys
from fractions import Fraction

import mpmath

mpmath.mp.dps = 50
DELTA = 0.2
MIN_ALPHA = 1.0 / DELTA + 1.0  # vgam::_min_alpha = 1/__delta + 1
M = 20


def bernoulli_numbers(n_max):
    """B_0..B_n_max with B_1 = -1/2 (Akiyama-Tanigawa)."""
    a, out = [Fraction(0)] * (n_max + 1), []
    for m in range(n_max + 1):
        a[m] = Fraction(1, m + 1)
        for j in range(m, 0, -1):
            a[j - 1] = j * (a[j - 1] - a[j])
        out.append(a[0])
    out[1] = -out[1] if out[1] > 0 else out[1]
    return out


B = bernoulli_numbers(M)
# phi_n(y) = B_n(y) - B_n = sum_{k=0}^{n-1} C(n,k) B_k y^(n-k); store coefficient of y^j.
PHI = {n: {n - k: float(math.comb(n, k) * B[k]) for k in range(n)} for n in range(2, M + 1)}


def d_m(x, y):
    """D_m(x, y) = sum_{n=2}^{m} (-1)^n phi_n(y) x^(n-1) / (n(n-1)), evaluated via t = x*y."""
    t, total = x * y, 0.0
    for n in range(2, M + 1):
        # x^(n-1) y^j = t^j x^(n-1-j) for j < n, and t^(n-1) y for j = n
        term = sum(c * (t ** (n - 1) * y if j == n else t ** j * x ** (n - 1 - j)) for j, c in PHI[n].items())
        total += (-1) ** n * term / (n * (n - 1))
    return total


def ll_bern(x, p, psi):
    s = sum(xk * math.log(pk) + d_m(psi / pk, xk) for xk, pk in zip(x, p) if xk)
    return s - d_m(psi, sum(x))


def ll_vgam(x, p, psi):
    total, j = 0.0, 0
    for xk, pk in zip(x, p):
        for r in range(xk):
            if psi >= 1.0:
                total += math.log(pk / psi + r) - math.log(j + 1.0 / psi)
            else:
                total += math.log(r * psi + pk) - math.log(j * psi + 1.0)
            j += 1
    return total


def next_p_psi(p, psi, x):
    n = sum(x)
    denom = psi * n + 1.0
    psi2 = psi / denom if psi < 1.0 else 1.0 / (1.0 / psi + n)
    return [pk / denom + xk * psi2 for pk, xk in zip(p, x)], psi2


def alpha(p, psi):
    return [pk / psi if psi else math.inf for pk in p]


def ll_mesh(n, p, psi):
    n, total = list(n), 0.0
    if not any(n):
        return 0.0, 0
    steps = 0
    a = alpha(p, psi)
    x = [min(nk, math.ceil(MIN_ALPHA - ak)) if nk and ak < MIN_ALPHA else 0 for nk, ak in zip(n, a)]
    if any(nk and ak < MIN_ALPHA for nk, ak in zip(n, a)):  # VGAM warm-up (exact product)
        total += ll_vgam(x, p, psi)
        p, psi = next_p_psi(p, psi, x)
        n = [nk - xk for nk, xk in zip(n, x)]
    while any(n):  # Bernoulli mesh steps, Eq. (30) with the Eq. (32) cap
        a = alpha(p, psi)
        x = [(nk if ak * DELTA >= nk else math.floor(ak * DELTA)) if nk else 0 for nk, ak in zip(n, a)]
        total += ll_bern(x, p, psi)
        p, psi = next_p_psi(p, psi, x)
        n = [nk - xk for nk, xk in zip(n, x)]
        steps += 1
    return total, steps


def exact(n, p, psi):
    if psi == 0:
        return sum(nk * mpmath.log(pk) for nk, pk in zip(n, p) if nk)
    psi = mpmath.mpf(psi)
    total = -(mpmath.loggamma(1 / psi + sum(n)) - mpmath.loggamma(1 / psi))
    for nk, pk in zip(n, p):
        total += mpmath.loggamma(mpmath.mpf(pk) / psi + nk) - mpmath.loggamma(mpmath.mpf(pk) / psi)
    return total


def cases():
    yield "vignette example", [3, 5, 7], [.2, .3, .5], .01
    for psi in [0, 1e-15, 1e-10, 1e-5, 1e-3, 0.01, 0.1, 1, 10, 1e3]:
        yield f"Fig 2/4 x=(2,3,1) psi={psi:g}", [2, 3, 1], [.2, .3, .5], psi
    for n in [1, 10, 100, 1000, 10**4, 10**5]:
        yield f"Fig 5 n={n}", [n] * 4, [.1, .2, .3, .4], 1 / 200
    for n in [1, 10, 100, 1000, 10**4, 10**5, 10**6]:
        yield f"Fig 6 n={n}", [n, 2 * n, 3 * n], [1 / 6, 1 / 3, 1 / 2], 1 / 60
    rng = random.Random(4081639)
    for i in range(300):
        k = 21
        w = [rng.expovariate(1) for _ in range(k)]
        p = [v / sum(w) for v in w]
        scale = 10 ** rng.uniform(0, 5)
        n = [0 if rng.random() < 0.15 else int(rng.expovariate(1 / scale)) for _ in range(k)]
        psi = 0.0 if i % 25 == 0 else 10 ** rng.uniform(-8, 1)
        yield f"random #{i}", n, p, psi


def main():
    driver = sys.argv[1]
    rows = list(cases())
    payload = "".join(f"{len(n)} {psi!r} " + " ".join(map(str, n)) + " " + " ".join(repr(v) for v in p) + "\n"
                      for _, n, p, psi in rows)
    out = subprocess.run(["arch", "-x86_64", driver], input=payload, capture_output=True, text=True, check=True)
    results = [list(map(float, line.split())) for line in out.stdout.strip().splitlines()]
    assert len(results) == len(rows)
    worst_re, worst_bin = (0, None), (0, None)
    for (label, n, p, psi), (b_mesh, _, _) in zip(rows, results):
        mine, steps = ll_mesh(n, p, psi)
        ex = exact(n, p, psi)
        scale = max(1.0, abs(b_mesh))
        d_re = abs(mine - b_mesh) / scale
        d_bin = float(abs(mpmath.mpf(b_mesh) - ex)) / scale
        worst_re = max(worst_re, (d_re, label))
        worst_bin = max(worst_bin, (d_bin, label))
        if not label.startswith("random"):
            print(f"{label:34s} binary={b_mesh:.15g}  reimpl_diff={d_re:.1e}  binary_vs_exact={d_bin:.1e}  bern_steps={steps}")
    print(f"\n{len(rows)} cases. Max |reimpl - binary| (rel): {worst_re[0]:.2e} ({worst_re[1]})")
    print(f"Max |binary - exact Eq.(6)| (rel): {worst_bin[0]:.2e} ({worst_bin[1]})")


main()
