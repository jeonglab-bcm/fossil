import csv, ctypes, json, os, sys, time
import numpy as np
from scipy.optimize import minimize
from scipy.special import digamma, gammaln

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("FOSSIL_HMP", os.path.join(HERE, "..", "hmp-data"))
_name = "libmesh.dylib" if sys.platform == "darwin" else "libmesh.so"
lib = ctypes.CDLL(os.path.abspath(_name) if os.path.exists(_name) else os.path.join(HERE, _name))
lib.ll_total.restype = ctypes.c_double
lib.ll_total.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_double), ctypes.c_double]
dp = lambda a: a.ctypes.data_as(ctypes.POINTER(ctypes.c_double))

def load(site):
    with open(os.path.join(DATA, f"{site}.csv")) as f:
        r = csv.reader(f); next(r)
        return np.array([[float(v) for v in row[1:]] for row in r])

def ll_mesh(X, p, psi):
    X = np.ascontiguousarray(X, dtype=float); p = np.ascontiguousarray(p, dtype=float)
    return lib.ll_total(dp(X), X.shape[0], X.shape[1], dp(p), psi)

def ll_lgamma(X, alpha):
    A = alpha.sum(); N = X.sum(1)
    return float((gammaln(A) - gammaln(A + N)).sum() + (gammaln(alpha + X) - gammaln(alpha)).sum())

def fit(X):
    pbar = X.sum(0) / X.sum()
    def f(theta):
        alpha = np.exp(theta); A = alpha.sum()
        v = ll_mesh(X, alpha / A, 1.0 / A)
        g = (digamma(alpha + X) - digamma(alpha)).sum(0) - (digamma(A + X.sum(1)) - digamma(A)).sum()
        return -v, -(g * alpha)
    best = None
    for psi0 in (0.001, 0.005, 0.02, 0.1):
        r = minimize(f, np.log(pbar / psi0), jac=True, method="L-BFGS-B", options=dict(maxiter=20000, ftol=1e-15, gtol=1e-9))
        if best is None or r.fun < best.fun: best = r
    alpha = np.exp(best.x); A = alpha.sum()
    return dict(psi=1.0 / A, p=(alpha / A).tolist(), ll=-best.fun, nit=int(best.nit), msg=str(best.message), alpha=alpha)

paper = {"saliva": 0.00389, "throat": 0.00639, "tongue": 0.00802, "tonsils": 0.01039}
out = {}
for site in paper:
    X = load(site); t0 = time.perf_counter(); r = fit(X); dt = time.perf_counter() - t0
    a = r.pop("alpha")
    # cross-check 1: same optimum under the plain lgamma formula (constant multinomial term excluded in both)
    diff = ll_lgamma(X, a) - r["ll"]
    # cross-check 2: profile scan in psi (re-optimising p at fixed psi is overkill; scan with p fixed at MLE)
    grid = r["psi"] * np.array([0.98, 0.99, 1.0, 1.01, 1.02])
    prof = [ll_mesh(X, np.array(r["p"]), g) for g in grid]
    out[site] = dict(psi=r["psi"], paper=paper[site], samples=X.shape[0], taxa=X.shape[1], reads=int(X.sum()),
                     ll=r["ll"], nit=r["nit"], seconds=round(dt, 2), lgamma_minus_mesh=diff,
                     profile_peak_at_center=bool(np.argmax(prof) == 2), p=r["p"])
    print(f"{site:8s} psi_hat={r['psi']:.6f}  paper={paper[site]:.5f}  rounded={round(r['psi'], 5):.5f}  "
          f"ll={r['ll']:.4f} nit={r['nit']} {dt:.1f}s  lgamma-mesh={diff:.2e}  profile_ok={out[site]['profile_peak_at_center']}  [{r['msg'][:30]}]", flush=True)
json.dump(out, open("table1_result.json", "w"), indent=1)
