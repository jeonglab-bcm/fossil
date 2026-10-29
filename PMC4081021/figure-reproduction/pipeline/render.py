"""Our versions of Figs 2B-G, 3B-D, 4B-D, 5B-C and 6, drawn with matplotlib from figdata.py
in the paper's panel layout (schematic panels 1, 2A, 3A, 4A and 5A are not drawn)."""

import argparse
import os

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import figdata as fd  # noqa: E402

plt.rcParams.update({"font.size": 7, "font.family": "DejaVu Sans", "axes.linewidth": 0.6,
                     "xtick.direction": "in", "ytick.direction": "in",
                     "xtick.major.size": 2.5, "ytick.major.size": 2.5})


def draw(ax, panel):
    for L in panel["layers"]:
        k = L["kind"]
        if k == "line":
            ax.plot(L["x"], L["y"], L.get("style", "-"), color=L["rgb"], lw=L["lw"])
        elif k == "fill":
            ax.fill(L["x"], L["y"], color=L["rgb"], ec="k", lw=0.4)
        elif k == "rect":
            (x0, x1), (y0, y1) = L["x"], L["y"]
            x0, x1 = np.clip([x0, x1], *panel["xlim"])
            ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fc=L["rgb"], ec="k", lw=0.4))
        elif k == "markers":
            ax.plot(L["x"], L["y"], "o" if L.get("open") else ".", color=L["rgb"],
                    mfc="none" if L.get("open") else L["rgb"], ms=L["size"] if L.get("open") else L["size"] / 2,
                    lw=0)
        elif k == "errorbar":
            ax.errorbar(L["x"], L["y"], yerr=L["err"], fmt="none", ecolor="k", lw=1, capsize=1.5)
    ax.set_xlim(panel["xlim"])
    ax.set_ylim(panel["ylim"])
    if panel.get("xlog"):
        ax.set_xscale("log")
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    if panel.get("ylog"):
        ax.set_yscale("log")
        ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())


def fig2(sources, out, fits, refit_dir):
    f = plt.figure(figsize=(7.5, 8.4))
    for col, scen in enumerate((1, 2)):
        P = fd.fig2(sources, scen, fits, refit_dir)
        x0 = 0.06 + col * 0.5
        b, c, d = ("B", "C", "D") if scen == 1 else ("E", "F", "G")
        ax = f.add_axes([x0 + 0.1, 0.8, 0.3, 0.16])
        draw(ax, P[b])
        ax.set_xlabel("time [min]")
        ax.set_ylabel("concentration of B [nM]")
        ax.set_title(["homogeneous, non-overlapping subpopulations",
                      "heterogeneous, highly-overlapping subpopulations"][col], fontsize=7, weight="bold")
        f.text(x0 - 0.04, 0.96, b, fontsize=11, weight="bold")
        for k in range(6):
            ax = f.add_axes([x0 + (k % 3) * 0.145, 0.6 - (k // 3) * 0.11, 0.13, 0.09])
            draw(ax, P[c][k])
            ax.text(0.11, 0.088, f"t = {P[c][k]['t']:g} min", fontsize=6, weight="bold")
            ax.set_xticks([0.1, 0.3, 1], ["0.1", "0.3", "1"] if k >= 3 else [])
            ax.set_yticks([0, 0.05, 0.1], ["0", "0.05", "0.1"] if k % 3 == 0 else [])
            if k % 3 == 0:
                ax.set_ylabel("frequency")
            if k == 4:
                ax.set_xlabel("concentration of B [nM]")
        f.text(x0 - 0.04, 0.7, c, fontsize=11, weight="bold")
        for j, name in enumerate(["k1", "k2", "k3", "w1"]):
            xx = x0 + (j % 2) * 0.23
            yy = 0.35 - (j // 2) * 0.24
            ax = f.add_axes([xx, yy, 0.2, 0.09])
            draw(ax, P[d][name + "_density"])
            ax.set_yticks([])
            ax.set_xticks([])
            ests = [n for n in P[d] if n.startswith(name) and n.endswith("estimate")]
            for i, n in enumerate(ests):
                h = 0.045 / len(ests)
                ax2 = f.add_axes([xx, yy - 0.05 + (len(ests) - 1 - i) * h, 0.2, h])
                draw(ax2, P[d][n])
                ax2.set_yticks([])
                if i < len(ests) - 1:
                    ax2.set_xticklabels([])
            ax2.set_xlabel({"k1": "$k_1$", "k2": "$k_2$", "k3": "$k_3$", "w1": "$w_1$"}[name])
        f.text(x0 - 0.04, 0.45, d, fontsize=11, weight="bold")
    f.savefig(os.path.join(out, "fig2_ours.png"), dpi=300)
    plt.close(f)


def fig34(sources, out, fits, refit_dir, which, num):
    P = fd.fig34(sources, which, fits, refit_dir)
    f = plt.figure(figsize=(7.5, 6.6))
    names = ["M$_{" + which + ",2}$", "M$_{" + which + ",3}$"]
    for mi in range(2):
        for j, kind in enumerate(["kinetic", "dose"]):
            ax = f.add_axes([0.58 + j * 0.2, 0.78 - mi * 0.17, 0.18, 0.15])
            draw(ax, P["B"][f"{kind}_{mi}"])
            if kind == "dose":
                ax.set_xticks(10.0 ** np.arange(-4, 2), ["0", "0.001", "0.01", "0.1", "1", "10"] if mi else [])
                ax.set_yticklabels([])
            else:
                ax.set_xticks([0, 15, 30, 45, 60], [] if mi == 0 else None)
                ax.set_ylabel(f"pErk level [UI]\n{names[mi]}")
            if mi == 1:
                ax.set_xlabel("time, t [min]" if kind == "kinetic" else "NGF concentration, [NGF]$_0$ [nM]")
    f.text(0.52, 0.95, "B", fontsize=11, weight="bold")
    for e, kind, n in [(0, "kinetic", 5), (1, "dose", 6)]:
        for k in range(n):
            ax = f.add_axes([0.08 + e * 0.23, 0.82 - k * 0.135, 0.2, 0.11])
            draw(ax, P["C"][f"{kind}_{k}"])
            lab = (f"t = {[0, 5, 15, 30, 60][k]} min" if e == 0 else
                   f"[NGF]$_0$ = {[0, 0.001, 0.01, 0.1, 1, 10][k]:g} nM")
            ax.text(0.13, 0.05, lab, fontsize=6, weight="bold")
            ax.set_xticks([0.1, 1, 10, 100], ["0.1", "1", "10", "100"] if k == n - 1 else [])
            if e == 0:
                ax.set_ylabel("frequency")
            if k == n - 1:
                ax.set_xlabel("pErk level [UI]")
    f.text(0.02, 0.95, "C", fontsize=11, weight="bold")
    ax = f.add_axes([0.62, 0.12 if which == "H3" else 0.08, 0.34, 0.3])
    draw(ax, P["D"]["rates"])
    ax.set_yticks([])
    labels = (["k1", "k2", "k4", "k5", "s[Erk]0", "k3[TrkA]0"] if which == "H1" else
              ["k1", "k2", "k4", "k5", "s[Erk]0", "k3[TrkA]0,1", "k3[TrkA]0,2"])
    for i, lab in enumerate(labels, start=1):
        ax.text(10 ** -2.55, i * -2.5 - 0.5, lab, ha="right", va="center", fontsize=6)
    ax.set_xlabel("parameter values")
    if which == "H3":
        ax2 = f.add_axes([0.62, 0.04, 0.34, 0.035])
        draw(ax2, P["D"]["w1"])
        ax2.set_yticks([])
        ax2.text(-0.02, -3.0, "w1", ha="right", va="center", fontsize=6)
    f.text(0.55, 0.45, "D", fontsize=11, weight="bold")
    f.savefig(os.path.join(out, f"fig{num}_ours.png"), dpi=300)
    plt.close(f)


def fig5(sources, out, fits, refit_dir):
    F = fd.fig5(sources, fits, refit_dir)
    f = plt.figure(figsize=(6.2, 4.6))
    ax = f.add_axes([0.13, 0.45, 0.82, 0.5])
    cols = [(1, 0, 0), (1, 0.35, 0), (1, 0.7, 0)]
    for j in range(3):
        ax.bar(np.arange(1, 10) + (j - 1) * 0.2222, F["BIC"][:, j], width=0.1778, color=cols[j],
               ec="k", lw=0.4, label=f"Pathway model {'ABC'[j]}")
    ax.set_ylim(np.exp(11.15), np.exp(11.65))
    ax.set_xlim(0.5, 9.5)
    for x in (3.5, 6.5):
        ax.axvline(x, color="k", lw=0.6)
    ax.set_xticks(range(1, 10), [f"M$_{{H{h},{v}}}$" for h in (1, 2, 3) for v in (1, 2, 3)])
    ax.set_ylabel("Bayesian information criterion, BIC")
    ax.legend(loc="upper right", frameon=False)
    f.text(0.02, 0.95, "B", fontsize=11, weight="bold")
    for j in range(3):
        ax = f.add_axes([0.1 + j * 0.3, 0.04, 0.22, 0.28])
        w = F["w_H33"][j]
        ax.pie([w[0], w[1]], colors=[(0.5, 0.5, 0.5), (0.8, 0.8, 0.8)], startangle=90 + 360 * w[1],
               autopct="%.1f%%", textprops={"fontsize": 7})
        ax.set_title(f"Pathway model {'ABC'[j]}\nModel M$_{{H3,3}}$", fontsize=7)
    f.text(0.02, 0.33, "C", fontsize=11, weight="bold")
    f.savefig(os.path.join(out, "fig5_ours.png"), dpi=300)
    plt.close(f)


def fig6(sources, out):
    F = fd.fig6(sources)
    from scipy.stats import multivariate_normal as mvn
    f = plt.figure(figsize=(6.7, 3.3))
    y_hist = np.linspace(-1, 1, 40)

    def h(v):
        return np.histogram(v, np.r_[y_hist, np.inf])[0][:-1] / 1500
    ctrl, stim, i1, i2 = F["control"], F["stimulated"], F["ind1"], F["ind2"]
    both = np.r_[i1, i2]
    hmax = h(ctrl[both, 1]).max()
    for col, (title, pts) in enumerate([("Control", [ctrl]), ("Stimulation", [ctrl, stim])]):
        x0 = 0.1 + col * 0.5
        ax = f.add_axes([x0 + 0.1, 0.4, 0.25, 0.5])
        for P in pts:
            ax.plot(P[:, 0], P[:, 1], "k.", ms=0.8)
        rho = F["rho_control"] if col == 0 else F["rho_stimulated"]
        ax.text(-0.5, 0.85, f"ρ = {rho:.3f}", ha="center")
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"{title}\n(t = 30 min, [NGF]$_0$ = {col} nM)", fontsize=7)
        if col == 1:
            g = np.linspace(-1, 1, 400)
            X1, X2 = np.meshgrid(g, g)
            for k, c in enumerate([(0, 0.8, 0), (0.6, 0, 0.6)]):
                Pk = mvn.pdf(np.dstack([X1, X2]), F["gm"]["mu"][k], F["gm"]["Sigma"][k])
                ax.contour(X1, X2, Pk / Pk.max(), [np.exp(-2)], colors=[c], linewidths=0.6)
                ax.text(np.log10(10 / 3.5), [0, np.log10(6)][k], f"{100 * F['gm']['p'][k]:.1f} %",
                        color=c, ha="center")
        axl = f.add_axes([x0, 0.4, 0.08, 0.5])
        axb = f.add_axes([x0 + 0.1, 0.22, 0.25, 0.14])
        st = lambda v: fd.staircase(y_hist, v)   # noqa: E731
        if col == 0:
            sx, sy = st(h(ctrl[both, 1]))
            axl.fill(sy, sx, color=(0.7, 0.7, 0.7), ec="k", lw=0.4)
            sx, sy = st(h(ctrl[both, 0]))
            axb.fill(sx, sy, color=(0.7, 0.7, 0.7), ec="k", lw=0.4)
        else:
            for idx, c in [(both, (0, 0.8, 0)), (i2, (0.6, 0, 0.6))]:
                sx, sy = st(h(stim[idx, 1]))
                axl.fill(sy, sx, color=c, ec="k", lw=0.4)
                sx, sy = st(h(stim[idx, 0]))
                axb.fill(sx, sy, color=c, ec="k", lw=0.4)
        axl.set_ylim(-1, 1)
        axl.set_xlim(0, 1.1 * hmax)
        axl.set_xticks([])
        axl.set_yticks([-1, 0, 1], ["0.1", "1", "10"])
        axl.set_ylabel("pErk level [UI]")
        axb.set_xlim(-1, 1)
        axb.set_ylim(0, 1.1 * hmax)
        axb.set_yticks([])
        axb.set_xticks([-1, 0, 1], ["0.1", "1", "10"])
        axb.set_xlabel("total Erk level [UI]")
        f.text(x0 - 0.07, 0.93, "AB"[col], fontsize=11, weight="bold")
    f.savefig(os.path.join(out, "fig6_ours.png"), dpi=300)
    plt.close(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fits", default="saved", choices=["saved", "refit"])
    ap.add_argument("--refit-dir")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    fig2(a.sources, a.out, a.fits, a.refit_dir)
    fig34(a.sources, a.out, a.fits, a.refit_dir, "H1", 3)
    fig34(a.sources, a.out, a.fits, a.refit_dir, "H3", 4)
    fig5(a.sources, a.out, a.fits, a.refit_dir)
    fig6(a.sources, a.out)


if __name__ == "__main__":
    main()
