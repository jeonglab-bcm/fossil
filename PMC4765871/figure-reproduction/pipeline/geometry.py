"""Diffusion map, branch clustering, Wanderlust and GENIE3, as the paper uses them.

* Diffusion map (supp. 1.1, Haghverdi et al. 2015): Gaussian kernel exp(-d^2 / (2 sigma^2)) with
  the diagonal removed, density normalisation K_ij / (z_i z_j), row-stochastic transition matrix;
  diffusion components are its eigenvectors 2, 3, 4. <d>(sigma) = d log(sum K) / d log(sigma)
  (supp. Figs 32-33).
* Branch clustering (supp. 1.2): Dijkstra shortest path from a start cell to an end cell on a
  k-nearest-neighbour graph of the embedding, plus the Nn nearest neighbours of each path cell.
* Wanderlust (Bendall et al. 2014; supp. 1.3): l-NN graph, k random neighbours of l kept per cell,
  num_graphs graphs, num_landmarks random waypoints, exponential weighting, realignment until the
  correlation of successive trajectories exceeds 0.9999. Ported from dpeerlab/cyt3
  src/wanderlust/wanderlust.m (commit 1e8ec47) with band sampling and landmark flocking off, as in
  the 2014 release.
* GENIE3 (Huynh-Thu et al. 2010; supp. 1.4): one tree ensemble per target on unit-variance inputs;
  the weight of an edge is the input's importance, normalised to sum to 1 per target. Extra-trees
  with sqrt(p) candidate inputs per split: of GENIE3's settings, the one that gives Fig. 7C.
"""
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial.distance import cdist


# ---------------------------------------------------------------- diffusion map


def diffusion_map(X, sigma, n_comp=3):
    D2 = cdist(X, X, "sqeuclidean")
    K = np.exp(-D2 / (2 * sigma**2))
    np.fill_diagonal(K, 0.0)
    z = K.sum(1)
    K = K / np.outer(z, z)
    d = K.sum(1)
    S = K / np.sqrt(np.outer(d, d))  # symmetric conjugate of the transition matrix
    w, V = np.linalg.eigh(S)
    order = np.argsort(w)[::-1]
    w, V = w[order], V[:, order]
    psi = V / np.sqrt(d)[:, None]
    psi = psi / np.linalg.norm(psi, axis=0)
    # fix the sign of each component (largest absolute entry positive) for reproducibility
    for j in range(psi.shape[1]):
        if psi[np.argmax(np.abs(psi[:, j])), j] < 0:
            psi[:, j] *= -1
    return psi[:, 1:n_comp + 1], w[1:n_comp + 4]


def local_maxima(x, y):
    """Interior local maxima of y(x), highest first."""
    i = [k for k in range(1, len(y) - 1) if y[k] > y[k - 1] and y[k] >= y[k + 1]]
    return sorted(((float(x[k]), float(y[k])) for k in i), key=lambda t: -t[1])


def intrinsic_dimension(X, log10_sigmas):
    """<d>(sigma) = d log S / d log sigma, S = sum_ij exp(-d_ij^2 / (2 sigma^2)), i != j."""
    D2 = cdist(X, X, "sqeuclidean")
    off = ~np.eye(len(X), dtype=bool)
    d2 = D2[off]
    ls = np.asarray(log10_sigmas, float)
    logS = np.array([np.log(np.exp(-d2 / (2 * (10**l) ** 2)).sum() + 1e-300) for l in ls])
    dim = np.gradient(logS, ls * np.log(10))
    return dim


# ---------------------------------------------------------------- branch clustering


def knn_graph(X, k):
    D = cdist(X, X)
    n = len(X)
    idx = np.argsort(D, axis=1)[:, 1:k + 1]
    rows = np.repeat(np.arange(n), k)
    cols = idx.ravel()
    G = csr_matrix((D[rows, cols], (rows, cols)), shape=(n, n))
    return G.maximum(G.T)


def branch_cluster(Y, start, end, Nn, k_graph=10):
    """Cells of the branch from start to end: the Dijkstra path on a k_graph-NN graph of the
    embedding Y, and the Nn nearest neighbours of every path cell."""
    # a k-NN graph of noisy data can fall apart; raise k until the end cell is reachable
    for k in range(k_graph, 61):
        G = knn_graph(Y, k)
        _, pred = dijkstra(G, indices=start, return_predecessors=True)
        if end == start or pred[end] >= 0:
            break
    path = [end]
    while path[-1] != start:
        p = pred[path[-1]]
        if p < 0:
            raise RuntimeError("end cell not reachable from start cell")
        path.append(p)
    path = path[::-1]
    D = cdist(Y[path], Y)
    nn = np.argsort(D, axis=1)[:, :Nn + 1]
    cells = np.unique(np.concatenate([np.array(path), nn.ravel()]))
    return cells, np.array(path)


# ---------------------------------------------------------------- Wanderlust


def _lnn(X, l, metric="euclidean"):
    D = cdist(X, X, metric)
    idx = np.argsort(D, axis=1)[:, 1:l + 1]
    return D, idx


def wanderlust(X, start, l=18, k=6, num_graphs=25, num_landmarks=20, seed=0, metric="euclidean"):
    """Returns the trajectory (mean over graphs, scaled to [0, 1]) and the per-graph trajectories."""
    rng = np.random.default_rng(seed)
    n = len(X)
    D, idx = _lnn(X, l, metric)
    T = np.zeros((num_graphs, n))
    for g in range(num_graphs):
        # k random neighbours out of l for each node, then symmetrise (spdists_undirected)
        keep = np.array([rng.choice(l, k, replace=False) for _ in range(n)])
        cols = idx[np.arange(n)[:, None], keep].ravel()
        rows = np.repeat(np.arange(n), k)
        G = csr_matrix((D[rows, cols], (rows, cols)), shape=(n, n))
        G = G.maximum(G.T)
        # landmarks: the start cell and num_landmarks - 1 random cells
        others = rng.choice(np.setdiff1d(np.arange(n), [start]), num_landmarks - 1, replace=False)
        lm = np.concatenate([[start], others])
        dist = dijkstra(G, directed=False, indices=lm)
        if np.isinf(dist).any():
            # connect components by the closest pair (cyt's search_connected_components)
            G = _connect(G, X, dist, lm)
            dist = dijkstra(G, directed=False, indices=lm)
        traj = dist.copy()
        for i in range(1, len(lm)):
            v = dist[0, lm[i]]
            before = dist[0] < v
            traj[i, before] = -dist[i, before]
            traj[i] += v
        sdv = np.mean(np.std(dist, axis=0, ddof=1)) * 3
        W = np.exp(-0.5 * (dist / sdv) ** 2)
        W = W / W.sum(0)
        t_prev = traj[0].copy()
        t = (traj * W).sum(0)
        for it in range(16):
            traj = dist.copy()
            for i in range(len(lm)):
                v = t[lm[i]]
                before = t < v
                traj[i, before] = -dist[i, before]
                traj[i] += v
            t_new = (traj * W).sum(0)
            c = np.corrcoef(t_new, t)[0, 1]
            t = t_new
            if c > 0.9999:
                break
        T[g] = t
    traj = T.mean(0)
    traj = (traj - traj.min()) / (traj.max() - traj.min())
    return traj, T


def _connect(G, X, dist, lm):
    G = G.tolil()
    reach = ~np.isinf(dist[0])
    while not reach.all():
        a = np.where(reach)[0]
        b = np.where(~reach)[0]
        D = cdist(X[a], X[b])
        i, j = np.unravel_index(np.argmin(D), D.shape)
        G[a[i], b[j]] = D[i, j]
        G[b[j], a[i]] = D[i, j]
        reach = ~np.isinf(dijkstra(G.tocsr(), directed=False, indices=lm[0]))
    return G.tocsr()


# ---------------------------------------------------------------- GENIE3


def genie3(X, ntrees=1000, max_features="sqrt", seed=0, n_jobs=1, tree_method="ET"):
    """W[i, j]: weight of the edge from gene i to gene j. tree_method: 'RF' (random forests) or
    'ET' (extra-trees), GENIE3's two options."""
    from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor

    Z = (X - X.mean(0)) / X.std(0, ddof=1)
    n_genes = X.shape[1]
    W = np.zeros((n_genes, n_genes))
    for j in range(n_genes):
        inputs = [i for i in range(n_genes) if i != j]
        Est = ExtraTreesRegressor if tree_method == "ET" else RandomForestRegressor
        rf = Est(n_estimators=ntrees, max_features=max_features, random_state=seed + j,
                 n_jobs=n_jobs)
        rf.fit(Z[:, inputs], Z[:, j])
        W[inputs, j] = rf.feature_importances_
    return W


def correlation_signs(X, W, w_thr, r_thr=None, p_thr=None):
    """Directed edges with weight above w_thr, with the sign of the Pearson correlation where it is
    significant (|r| > r_thr, or p < p_thr), else 0 (sign uncertain)."""
    from scipy.stats import pearsonr

    edges = []
    n = X.shape[1]
    for i in range(n):
        for j in range(n):
            if i != j and W[i, j] > w_thr:
                r, p = pearsonr(X[:, i], X[:, j])
                sig = (abs(r) > r_thr) if r_thr is not None else (p < p_thr)
                edges.append((i, j, float(W[i, j]), float(r), float(p), int(np.sign(r)) if sig else 0))
    return edges
