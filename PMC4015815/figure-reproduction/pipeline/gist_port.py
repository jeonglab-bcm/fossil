"""Port of Gist 2.3 `gist-train-svm` / `gist-classify` with default options.

The paper trains with "the publicly available Gist SVM package version 2.3 ... The SVM parameters
were used by default". This module reproduces what Gist 2.3 does with no options, line by line
from its C source (svm.msl.ubc.ca/releases/gist-2.3.tar.gz, files given in brackets):

kernel   [kernel.c allocate_kernel, compute-kernel.c transform_kernel_matrix]
  base K(x, y) = x . y (dot product, no feature selection, no zero-mean, no variance-one)
  normalize    K(x, y) / (sqrt(K(x, x)) * sqrt(K(y, y)))  (both zero -> 1, one zero -> 0,
               NaN or > 1 -> 1 on the diagonal and 0 elsewhere)
  polynomial   (K + 10) * 1, to the power 1         (constant 10, coefficient 1, power 1)
  2-norm soft margin: diagonal factor 0.1. With m the median of the diagonal, n+ and n- the class
  sizes and N their sum, add (n+/N) 0.1 m to positive and (n-/N) 0.1 m to negative diagonals.

training [compute-weights.c, train-main.c]
  weights start at 0.5; seed for drand48 from the clock (we fix it); convergence threshold 1e-6
  (train-main.c #define; the help text says 0.00001); no iteration or time limit; no box
  constraint. Jaakkola, Diekhans and Haussler's update: for each item in a random permutation
  (Knuth shuffle with drand48, reshuffled after every pass)
      w_i <- max(0, (1 - y_i g_i + w_i K_ii) / K_ii),  g_i = sum_j w_j y_j K_ij,
  until the objective sum_i w_i (2 - y_i g_i) / N changes by less than the threshold between
  passes. Then the same on the support vectors (w > 1e-7) only, with the convergence state
  carried over (converged() keeps its static previous objective). Output weights are w_i y_i.

output   [train-main.c, rdb-matrix.c] weights are printed with "%.4g" (4 significant digits).

classify [classify.c, test-main.c]
  discriminant(x) = sum_i (w_i y_i) K(x, x_i) over the printed weights, with the test kernel
  normalized by the test and train self-values and the constant added, no diagonal term, bias 0.

The loops run in numba in the C code's order (sequential sums, no fast-math), so each step does
the same floating-point operations as the C code.
"""
import numpy as np
from numba import njit

DIAG_FACTOR = 0.1
CONSTANT = 10.0
CONVERGENCE = 1e-6
INITIAL_WEIGHT = 0.5
SLOP = 1e-7

_A = np.uint64(0x5DEECE66D)
_C = np.uint64(0xB)
_MASK = np.uint64((1 << 48) - 1)


@njit(cache=True)
def _drand48(state):
    # state is a one-element uint64 array: X <- (a X + c) mod 2^48, return X / 2^48
    x = (state[0] * np.uint64(0x5DEECE66D) + np.uint64(0xB)) & np.uint64(0xFFFFFFFFFFFF)
    state[0] = x
    return float(x) / 281474976710656.0


def srand48(seed):
    """State after srand48(seed): high 32 bits from the seed, low 16 bits 0x330E."""
    return np.array([((seed & 0xFFFFFFFF) << 16) | 0x330E], dtype=np.uint64)


@njit(cache=True)
def _shuffle(perm, state):
    n = perm.shape[0]
    for i in range(n):
        r = int(_drand48(state) * float(n - i)) + i
        t = perm[i]
        perm[i] = perm[r]
        perm[r] = t


@njit(cache=True)
def _discriminant(i, w, sign, K):
    s = 0.0
    for j in range(w.shape[0]):
        v = w[j] * K[i, j]
        s += v * sign[j]
    return s


@njit(cache=True)
def _objective(w, sign, K):
    n = w.shape[0]
    total = 0.0
    for i in range(n):
        d = _discriminant(i, w, sign, K) * sign[i]
        total += w[i] * (2.0 - d)
    return total / n


@njit(cache=True)
def _optimize(w, sign, K, state, conv, threshold, cap):
    """optimize_weights(): conv = [prev_objective, iteration] (the statics of converged()).

    cap: per-item box constraint (positive_constraint / negative_constraint); 0 means no cap for
    that item's class. Gist 2.3 (compute-weights.c, update_weight) turns the cap on for both
    classes once either constraint is set, so with only one set it clamps the other class's
    weights to 0; the port caps each class only by its own constraint. With both set (Gist's
    sample run) or neither (Gist's default, used here) the two agree.
    """
    n = w.shape[0]
    perm = np.arange(n)
    current = 0
    passes = 0
    while True:
        obj = _objective(w, sign, K)
        if np.isnan(obj):
            raise ValueError("objective is NaN: the updates diverged (indefinite kernel)")
        delta = obj - conv[0]
        conv[0] = obj
        conv[1] += 1
        if abs(delta) < threshold:
            break
        for _ in range(n):
            if current == 0:
                _shuffle(perm, state)
            i = perm[current]
            current += 1
            if current >= n:
                current = 0
            d = _discriminant(i, w, sign, K)
            kii = K[i, i]
            nw = 1.0 - sign[i] * d + w[i] * kii
            if kii == 0.0:
                nw /= nw
            else:
                nw /= kii
            if cap[i] != 0.0 and nw > cap[i]:
                nw = cap[i]
            elif nw < 0.0:
                nw = 0.0
            w[i] = nw
        passes += 1
    return passes + 1


# What to do with a normalized value above 1. Gist sets it to 1 on the diagonal and 0 elsewhere
# ("gist"). On x86-64 doubles, some identical sequences give K/(sqrt(K)*sqrt(K)) = 1 + 2^-52
# (279 of the 10,807 off-diagonal pairs at 1 or above at dMAX = 0), and the 0 makes the kernel
# indefinite: at dMAX = 0 the updates
# then diverge to NaN and Gist's loop never ends. CAP = 1 caps such values at 1 instead ("cap").
CLIP_GIST = 0
CLIP_CAP = 1


@njit(cache=True)
def _normalize(Kraw, self_rows, self_cols, clip):
    """Normalize a test-by-train kernel (rows: test, columns: train) and add the constant.

    A value above 1 is capped at 1 ("cap") or set to 0 ("gist"). Gist's normalize_kernel_matrix
    keeps 1 where the row index equals the column index even here, where that is not a diagonal;
    the port does not, so under "gist" every such value is 0.
    """
    nr, nc = Kraw.shape
    out = np.empty((nr, nc))
    for r in range(nr):
        rd = self_rows[r]
        rs = np.sqrt(rd)
        for c in range(nc):
            cd = self_cols[c]
            v = Kraw[r, c]
            if rd == 0.0 and cd == 0.0:
                v = 1.0
            elif rd == 0.0 or cd == 0.0:
                v = 0.0
            else:
                v = v / (rs * np.sqrt(cd))
                if np.isnan(v) or v > 1.0:
                    v = 1.0 if clip == CLIP_CAP else 0.0
            out[r, c] = (v + 10.0) * 1.0
    return out


@njit(cache=True)
def _normalize_square(Kraw, normalize, constant, clip):
    n = Kraw.shape[0]
    self_vals = np.empty(n)
    for i in range(n):
        self_vals[i] = Kraw[i, i]
    out = np.empty((n, n))
    for r in range(n):
        rd = self_vals[r]
        rs = np.sqrt(rd)
        for c in range(n):
            cd = self_vals[c]
            v = Kraw[r, c]
            if not normalize:
                pass
            elif rd == 0.0 and cd == 0.0:
                v = 1.0
            elif rd == 0.0 or cd == 0.0:
                v = 0.0
            else:
                v = v / (rs * np.sqrt(cd))
                if np.isnan(v) or v > 1.0:
                    v = 1.0 if (r == c or clip == CLIP_CAP) else 0.0
            out[r, c] = (v + constant) * 1.0
    return out


def train(Kraw, positive, seed=1, threshold=CONVERGENCE, diag_factor=DIAG_FACTOR,
          normalize=True, constant=CONSTANT, pos_constraint=0.0, neg_constraint=0.0,
          clip=CLIP_CAP):
    """Gist training on a raw (unnormalized) square dot-product kernel.

    Kraw: (n, n) float64, positive: bool array. Returns (signed weights w_i y_i, info dict).
    The keyword defaults are Gist 2.3's; the others exist to check the port on Gist's own
    sample run (doc/sample.weights, made with -nonormalize, constant 1 and constraints of 1).
    """
    sign = np.where(positive, 1.0, -1.0)
    cap = np.where(positive, pos_constraint, neg_constraint).astype(np.float64)
    K = _normalize_square(np.ascontiguousarray(Kraw, dtype=np.float64), normalize, constant, clip)
    n = K.shape[0]
    diag = np.sort(np.diag(K).copy())
    if n % 2 == 1:
        median = diag[n // 2]
    else:
        median = (diag[n // 2 - 1] + diag[n // 2]) / 2.0
    npos = int(positive.sum())
    pos_diag = (npos / n) * diag_factor * median
    neg_diag = ((n - npos) / n) * diag_factor * median
    if diag_factor != 0.0:
        idx = np.arange(n)
        K[idx, idx] += np.where(positive, pos_diag, neg_diag)

    w = np.full(n, INITIAL_WEIGHT)
    state = srand48(seed)
    conv = np.zeros(2)
    it = _optimize(w, sign, K, state, conv, threshold, cap)
    sv = np.flatnonzero(~((w - SLOP <= 0.0) & (w + SLOP >= 0.0)))
    it2 = 0
    if len(sv) > 0:
        Ksv = np.ascontiguousarray(K[np.ix_(sv, sv)])
        wsv = w[sv].copy()
        it2 = _optimize(wsv, sign[sv].copy(), Ksv, state, conv, threshold, cap[sv].copy())
        w[sv] = wsv
    objective = _objective(w, sign, K)
    return w * sign, {"iterations": int(it + it2), "objective": float(objective),
                      "support_vectors": int(len(sv)), "positive_diagonal": pos_diag,
                      "negative_diagonal": neg_diag}


def printed(signed_w):
    """The weights as gist-train-svm writes them and gist-classify reads them back: '%.4g'.

    train-main.c sets the output precision to |log10(threshold)| - 2 = 4 (minimum 4) and
    rdb-matrix.c prints with "%*.*g", so each weight keeps 4 significant digits.
    """
    return np.array([float("%.4g" % x) for x in signed_w])


def classify(Kraw_test_train, self_test, self_train, signed_w, clip=CLIP_CAP):
    """Discriminants of test rows: sum_i signed_w_i K(test, train_i), K normalized, +10.

    Pass the printed weights (printed()) to match gist-classify on gist-train-svm's output.
    """
    K = _normalize(np.ascontiguousarray(Kraw_test_train, dtype=np.float64),
                   np.ascontiguousarray(self_test, dtype=np.float64),
                   np.ascontiguousarray(self_train, dtype=np.float64), clip)
    return _classify(K, signed_w)


@njit(cache=True)
def _classify(K, w):
    out = np.empty(K.shape[0])
    for r in range(K.shape[0]):
        s = 0.0
        for c in range(K.shape[1]):
            if w[c] == 0.0:
                continue
            s += K[r, c] * w[c]
        out[r] = s
    return out
