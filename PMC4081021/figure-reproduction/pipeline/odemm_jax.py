"""JAX version of odemm.log_likelihood with exact gradients, for multi-start refitting.

Same models and likelihood as odemm.py (which is checked against the authors' saved optima);
the ODEs are solved with diffrax (Kvaerno5, an implicit Runge-Kutta method for stiff systems)
and the gradient comes from automatic differentiation instead of CVODES forward sensitivities.
"""

import jax

jax.config.update("jax_enable_x64", True)

import diffrax  # noqa: E402
import jax.numpy as jnp  # noqa: E402
import numpy as np  # noqa: E402

DOSES = (0.0, 0.001, 0.01, 0.1, 1.0, 10.0)


def _rhs_A(t, x, args):
    th, u = args
    return jnp.stack([th[0] * u * (th[4] - x[0]) - th[1] * x[0],
                      (th[2] + x[0]) * (th[5] - x[1]) - th[3] * x[1]])


def _x0_A(th):
    return jnp.stack([0.0, th[2] * th[5] / (th[2] + th[3])])


def _rhs_BC(feedback):
    def rhs(t, x, args):
        p, u = args
        k1, k2, k4, k5, k7, k9, k11, TrkA0, Ras0, Raf0, Mek0, Erk0 = [p[i] for i in range(12)]
        act = x[0]
        if feedback:
            sK, n = p[12], p[13]
            r = jnp.maximum(x[4], 0.0) / sK
            act = x[0] * jnp.exp(-jnp.logaddexp(0.0, n * jnp.log(jnp.maximum(r, 1e-300))))
        return jnp.stack([k1 * u * (TrkA0 - x[0]) - k2 * x[0],
                          (act + k4) * (Ras0 - x[1]) - k5 * x[1],
                          x[1] * (Raf0 - x[2]) - k7 * x[2],
                          x[2] * (Mek0 - x[3]) - k9 * x[3],
                          x[3] * (Erk0 - x[4]) - k11 * x[4]])
    return rhs


def _x0_BC(p):
    k4, k5, k7, k9, k11 = p[2], p[3], p[4], p[5], p[6]
    Ras0, Raf0, Mek0, Erk0 = p[8], p[9], p[10], p[11]
    x2 = k4 * Ras0 / (k4 + k5)
    x3 = x2 * Raf0 / (x2 + k7)
    x4 = x3 * Mek0 / (x3 + k9)
    x5 = x4 * Erk0 / (x4 + k11)
    return jnp.stack([0.0, x2, x3, x4, x5])


PATHWAYS = {"ngf_A": (_rhs_A, _x0_A), "ngf_B": (_rhs_BC(False), _x0_BC),
            "ngf_C": (_rhs_BC(True), _x0_BC)}


def _ode_solver(pathway, T, rtol, atol, max_steps):
    rhs, x0f = PATHWAYS[pathway]
    term = diffrax.ODETerm(rhs)
    solver = diffrax.Kvaerno5()
    ctrl = diffrax.PIDController(rtol=rtol, atol=atol)
    ts = jnp.asarray(T, float)

    def solve(th, u):
        sol = diffrax.diffeqsolve(term, solver, t0=0.0, t1=float(T[-1]), dt0=None, y0=x0f(th),
                                  args=(th, u), saveat=diffrax.SaveAt(ts=ts),
                                  stepsize_controller=ctrl, max_steps=max_steps, throw=False)
        ok = sol.result == diffrax.RESULTS.successful
        return sol.ys, ok
    return solve


def build(spec, D, rtol=1e-8, atol=1e-10, max_steps=20000):
    """Return f(xi) -> (logL, dlogL/dxi) as jitted JAX functions for the model spec and data D
    (the format of saved.to_D)."""
    pathway = spec.pathway
    kin = [e for e, De in enumerate(D) if De["type"] == "kinetic"]
    dr = [e for e, De in enumerate(D) if De["type"] == "dose response"]
    Tk = np.asarray(D[kin[0]]["t"], float)
    if dr:
        assert np.all(np.asarray(D[dr[0]]["u"]) == np.asarray(DOSES))
        t_dr = float(np.atleast_1d(D[dr[0]]["t"])[0])
        T = np.union1d(Tk, [t_dr])
    else:
        T = Tk
    ik = np.searchsorted(T, Tk)
    u_kin = float(D[kin[0]]["u"])

    # data: NaN replaced by 1 and masked
    data = []
    for De in D:
        y = np.asarray(De["y"], float)
        mask = ~np.isnan(y)
        data.append((jnp.asarray(np.where(mask, y, 1.0)), jnp.asarray(mask)))

    if pathway == "conversion":
        def states(th):
            # columns: kinetic time points (u = u_kin); no dose response in this study
            a = th[0] + th[2] * u_kin
            lam = a + th[1]
            x0 = th[0] / (th[0] + th[1])
            xinf = a / lam
            return (xinf + (x0 - xinf) * jnp.exp(-lam * jnp.asarray(Tk)))[:, None], None, True
    else:
        solve = _ode_solver(pathway, T, rtol, atol, max_steps)
        us = jnp.asarray(DOSES if dr else (u_kin,))
        u_index = DOSES.index(u_kin) if dr else 0
        i_dr = int(np.searchsorted(T, t_dr)) if dr else None

        def states(th):
            ys, ok = jax.vmap(lambda u: solve(th, u))(us)      # (n_u, n_T, n_x)
            kinx = ys[u_index][ik]
            drx = ys[:, i_dr, :] if dr else None
            return kinx, drx, jnp.all(ok)

    readout = spec.readout
    S = spec.n_subpop

    def weights(xi):
        w = []
        for kind, k in spec.weight:
            w.append(1.0 if kind == "const" else (xi[k] if kind == "xi" else 1.0 - xi[k]))
        return w

    def logdens(dist, y, logy, mu, sigma):
        if dist == "logn":
            z = (logy - mu) / sigma
            return -0.5 * z * z - logy - jnp.log(sigma) - 0.5 * jnp.log(2 * jnp.pi)
        z = (y - mu) / sigma
        return -0.5 * z * z - jnp.log(sigma) - 0.5 * jnp.log(2 * jnp.pi)

    def loglik(xi):
        w = weights(xi)
        X = []
        ok_all = True
        for s in range(S):
            th = 10.0 ** xi[jnp.asarray(spec.theta_idx[s])]
            kx, dx, ok = states(th)
            X.append((kx, dx))
            ok_all = jnp.logical_and(ok_all, ok)
        total = 0.0
        for e, De in enumerate(D):
            y, mask = data[e]
            logy = jnp.log(y)
            terms = []
            for s in range(S):
                ro = readout[(s, e)]
                x = X[s][0][:, ro.state] if De["type"] == "kinetic" else X[s][1][:, ro.state]
                sigma = 10.0 ** xi[jnp.asarray(ro.sigma_idx)]
                if ro.log:
                    mu = jnp.log(jnp.maximum(x, 1e-300)) - (sigma ** 2 / 2 if ro.mean_shift else 0.0)
                else:
                    mu = x
                lw = jnp.log(jnp.maximum(w[s], 1e-300)) if not isinstance(w[s], float) else 0.0
                terms.append(lw + logdens(spec.dist[s], y, logy, mu[:, None], sigma[:, None]))
            lp = jax.scipy.special.logsumexp(jnp.stack(terms), axis=0)
            total = total + jnp.sum(jnp.where(mask, lp, 0.0))
        return jnp.where(ok_all & jnp.isfinite(total), total, -jnp.inf)

    f = jax.jit(loglik)
    g = jax.jit(jax.value_and_grad(loglik))
    return f, g
