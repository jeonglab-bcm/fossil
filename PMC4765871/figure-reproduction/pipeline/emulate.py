"""Emulators of input genes (supp. 1.5.2.2): Gaussian-process regression with a squared-exponential
kernel and Gaussian noise, hyperparameters by maximum marginal likelihood (GPML's usual use; here
scikit-learn). For the haematopoietic data the paper uses piecewise-linear interpolators instead
(supp. 2.3.2); ``linear_emulator`` interpolates a running mean of the series."""
import numpy as np


def gp_fit(t, x, seed=0):
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, WhiteKernel

    t = np.asarray(t, float)[:, None]
    x = np.asarray(x, float)
    span = float(t.max() - t.min()) or 1.0
    k = (C(1.0, (1e-3, 1e3)) * RBF(span / 10, (span / 200, span * 2))
         + WhiteKernel(0.05, (1e-6, 10.0)))
    gp = GaussianProcessRegressor(kernel=k, normalize_y=True, n_restarts_optimizer=3,
                                  random_state=seed)
    gp.fit(t, x)
    noise_sd = float(np.sqrt(gp.kernel_.k2.noise_level) * gp._y_train_std)

    def f(tt):
        return gp.predict(np.asarray(tt, float)[:, None])

    return f, noise_sd, gp


def linear_emulator(t, x, window=9):
    t = np.asarray(t, float)
    x = np.asarray(x, float)
    o = np.argsort(t, kind="stable")
    t, x = t[o], x[o]
    pad = window // 2
    xp = np.pad(x, pad, mode="edge")
    sm = np.convolve(xp, np.ones(window) / window, mode="valid")

    def f(tt):
        return np.interp(np.asarray(tt, float), t, sm)

    return f
