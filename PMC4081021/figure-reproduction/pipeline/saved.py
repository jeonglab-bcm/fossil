"""Access to the authors' code and saved results in Text S1 (ODEMM_implementation_v01)."""

import os

import numpy as np
import scipy.io as sio

from odemm import parse_fitting_script

STUDIES = {
    # key: (folder, pathway, models in the paper's table order)
    "cr1": ("conversion_reaction/scenario_1___low_variability", "conversion",
            ["1norm", "1logn_mean", "1logn_median",
             "2norm_k1a", "2logn_mean_k1a", "2logn_median_k1a",
             "2norm_k1b", "2logn_mean_k1b", "2logn_median_k1b",
             "2norm_k2", "2logn_mean_k2", "2logn_median_k2"]),
    "cr2": ("conversion_reaction/scenario_2___high_variability", "conversion", None),
    "ngfA": ("NGF_induced_Erk_phosphorylation/pathway_model_A", "ngf_A",
             ["1norm", "1logn_mean", "1logn_median",
              "2norm_Erk0", "2logn_mean_Erk0", "2logn_median_Erk0",
              "2norm_TrkA0", "2logn_mean_TrkA0", "2logn_median_TrkA0"]),
    "ngfB": ("NGF_induced_Erk_phosphorylation/pathway_model_B", "ngf_B", None),
    "ngfC": ("NGF_induced_Erk_phosphorylation/pathway_model_C", "ngf_C", None),
}
STUDIES["cr2"] = (STUDIES["cr2"][0], "conversion", STUDIES["cr1"][2])
STUDIES["ngfB"] = (STUDIES["ngfB"][0], "ngf_B", STUDIES["ngfA"][2])
STUDIES["ngfC"] = (STUDIES["ngfC"][0], "ngf_C", STUDIES["ngfA"][2])

# Paper labels: the 12 conversion-reaction models M_H1,1 ... M_H4,3 (Table 1) and the
# 9 NGF models M_H1,1 ... M_H3,3 (Table 2, Fig. 5B).
LABELS = {
    "cr": ["H1,1", "H1,2", "H1,3", "H2,1", "H2,2", "H2,3", "H3,1", "H3,2", "H3,3",
           "H4,1", "H4,2", "H4,3"],
    "ngf": ["H1,1", "H1,2", "H1,3", "H2,1", "H2,2", "H2,3", "H3,1", "H3,2", "H3,3"],
}


def code_root(sources):
    return os.path.join(sources, "ODEMM_implementation_v01")


def load_mat(path):
    return sio.loadmat(path, squeeze_me=True, struct_as_record=False)


def to_D(Dmat):
    D = []
    for De in np.atleast_1d(Dmat):
        y = np.atleast_2d(np.asarray(De.y, float))
        D.append({"type": De.type, "t": np.atleast_1d(np.asarray(De.t, float)),
                  "u": np.atleast_1d(np.asarray(De.u, float)) if De.type == "dose response"
                  else float(De.u), "y": y,
                  "Ey": np.atleast_2d(np.asarray(De.Ey, float)) if hasattr(De, "Ey") else None})
    return D


def load_model(sources, study, model):
    folder, pathway, _ = STUDIES[study]
    root = os.path.join(code_root(sources), folder)
    spec = parse_fitting_script(os.path.join(root, f"fitting__{model}.m"), pathway)
    m = load_mat(os.path.join(root, "project", "results", f"{model}_all.mat"))
    return spec, m


def model_list(study):
    return STUDIES[study][2]
