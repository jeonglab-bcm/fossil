"""Run the Python port of LIMPIC 1.1 on Additional Files 2 and 3.

Usage: python run_limpic.py <invitro_dir> <plasma_dir> <outdir>

Writes the same files as octave/run_limpic.m, so check_port.py can compare the two:
plasma_classes.csv, plasma_peaks.csv, p15_*.csv, invitro_peaks.csv, invitro_<conc>_classes.csv.
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import limpic  # noqa: E402

CONCENTRATIONS = ["2.5", "5", "7.5", "10", "25", "50"]


def write_classes(path, value, amp):
    n = (amp > 0).sum(axis=0)
    with open(path, "w") as f:
        f.write("mz,n," + ",".join(f"s{i + 1}" for i in range(amp.shape[0])) + "\n")
        for j in range(len(value)):
            f.write(f"{value[j]:.6f},{n[j]}," + ",".join(f"{a:.6f}" for a in amp[:, j]) + "\n")


def main(invitro, plasma, out):
    os.makedirs(out, exist_ok=True)

    # Plasma: P_1..P_30, then multiple_spectra with 300 ppm and PDR 0.5.
    results = [limpic.single_spectrum(os.path.join(plasma, f"P_{i}.txt")) for i in range(1, 31)]
    value, amp, nel, sel = limpic.multiple_spectra([(r["peak_mass"], r["peak_intensity"]) for r in results])
    write_classes(os.path.join(out, "plasma_classes.csv"), value, amp)

    with open(os.path.join(out, "plasma_peaks.csv"), "w") as f:
        f.write("spectrum,mz,intensity,noise,sigma\n")
        for i, r in enumerate(results, 1):
            # sigma: the noise standard deviation alone, the denominator of Eq. 4 (SNR).
            sigma = r["norm_factor"] * limpic._interp_ends(r["xr"], r["x_int"], r["s_int"])
            for p in r["peak_point"]:
                f.write(f"{i},{r['xr'][p]:.2f},{r['wxrbn'][p]:.6f},{r['noise_lev'][p]:.6f},{sigma[p]:.6f}\n")

    # The example spectrum of Figs 2 to 8.
    s = results[14]
    np.savetxt(os.path.join(out, "p15_raw.csv"), np.c_[s["x"], s["w"], s["wx"]], fmt="%.6f", delimiter=",")
    np.savetxt(
        os.path.join(out, "p15_processed.csv"),
        np.c_[s["xr"], s["wxr"], s["baseline"], s["wxrbn"], s["noise_lev"]],
        fmt="%.6f",
        delimiter=",",
    )
    np.savetxt(
        os.path.join(out, "p15_blocks.csv"),
        np.c_[s["x_int"], s["m_int"], s["v_int"], s["s_int"]],
        fmt="%.6f",
        delimiter=",",
    )
    np.savetxt(os.path.join(out, "p15_norm.csv"), [s["norm_factor"]], fmt="%.10f")
    smooth = [limpic.prepro(s["w"], f) for f in (10, 20, 30, 40)]
    np.savetxt(os.path.join(out, "p15_smooth.csv"), np.c_[s["x"], *smooth], fmt="%.6f", delimiter=",")

    # In vitro: each concentration (5 replicates) on its own.
    with open(os.path.join(out, "invitro_peaks.csv"), "w") as f:
        f.write("conc,replicate,file,mz,intensity\n")
        for c in CONCENTRATIONS:
            folder = os.path.join(invitro, f"SOL_{c}_TXT")
            files = sorted(n for n in os.listdir(folder) if n.endswith(".txt"))
            peaks = []
            for i, name in enumerate(files, 1):
                r = limpic.single_spectrum(os.path.join(folder, name))
                peaks.append((r["peak_mass"], r["peak_intensity"]))
                for m, a in zip(r["peak_mass"], r["peak_intensity"]):
                    f.write(f"{c},{i},{name},{m:.2f},{a:.6f}\n")
            value, amp, nel, sel = limpic.multiple_spectra(peaks)
            write_classes(os.path.join(out, f"invitro_{c}_classes.csv"), value, amp)


if __name__ == "__main__":
    main(*sys.argv[1:4])
