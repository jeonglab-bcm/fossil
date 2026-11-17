"""Write results_notes.json (the hand-written part of results.json). Kept as code so the long
inventory stays readable; run it after editing, then stamp the skill block with skill_version.py."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "results_notes.json"
old = json.loads(OUT.read_text()) if OUT.exists() else {}

S3 = "https://pmc-oa-opendata.s3.amazonaws.com/PMC3098087.1/"
inputs = []
for line in (HERE.parent / "pipeline" / "fetch_inputs.sh").read_text().split("<<LIST\n")[1].split("\nLIST")[0].splitlines():
    sha, name, url, *_ = line.split()
    inputs.append({"name": name, "url": url.replace("$S3/", S3), "sha256": sha})

A = {
    "simulation": [
        {"what": "Each simulated data set is a training set of 80 and separate test sets drawn from the same distributions, with round(80 k1train) Class 1 samples; the paper splits 100 samples into 80 and 20.", "source": "our_choice"},
        {"what": "Random seeds: one per setting and replicate (from the setting's name); the paper's seeds are not given.", "source": "our_choice"},
        {"what": "Replicates: 1,000 per setting as in the paper, except 500 for the settings of Fig. 4 and Additional file 7, of Fig. 3's right panels, of p = 10,000 and of MultDS (compute budget); the tolerance uses our replicate count.", "source": "our_choice"},
        {"what": "Ties: DLDA and DQDA give ties to Class 1 (as sma::stat.diag.da); k-NN breaks ties at random (class::knn); PLR breaks ties at 0.5 at random (as stated).", "source": "our_choice"},
        {"what": "RF: randomForest defaults (500 trees, mtry = sqrt(p)) with classwt = the training class proportions, as stated; RF-THR classifies as Class 1 when the vote share exceeds k1train.", "source": "paper"},
        {"what": "SVM: e1071::svm, linear kernel, scale = FALSE, class.weights = the training class proportions (as stated) and the default cost 1 (not stated).", "source": "our_choice"},
        {"what": "PAM: pamr.train with its default 30 thresholds; the largest threshold with the smallest training error (as stated).", "source": "paper"},
        {"what": "PLR: stepPlr::plr with lambda = 1 (as stated), Class 1 coded 1.", "source": "paper"},
        {"what": "AUC scores: share of neighbour votes (k-NN), difference of the two discriminants (DLDA, DQDA), vote share (RF), decision value (SVM), posterior (PAM), fitted probability (PLR). The paper says only that Hmisc was used.", "source": "our_choice"},
        {"what": "A predictive value has no value in a replicate whose denominator is 0 (PV1 when PA1 = 0 and PA2 = 1). Means are over the replicates where the value exists; a cell the paper prints as NA or NaN counts as equal when some of our replicates have no value.", "source": "our_choice"},
    ],
    "corrections": [
        {"what": "Over-sampling draws the max(n1, n2) - min(n1, n2) replicated minority samples with replacement; down-sizing keeps min(n1, n2) majority samples drawn without replacement.", "source": "our_choice"},
        {"what": "MultDS: 101 down-sized sets, t-test selection of 40 variables inside each, majority vote (as stated). At k1train = 0.5 no sample is left out, so all 101 classifiers are the same.", "source": "paper"},
        {"what": "Variable centering is applied to the training set the classifier is fitted on (after over- or down-sizing, inside each MultDS set) and to the test set separately.", "source": "our_choice"},
        {"what": "Predictive values use the original training proportion (k1train), also after a correction.", "source": "our_choice"},
    ],
    "er": [
        {"what": "Data: the BRB-ArrayTools project of Sotiriou et al. (2003) in the NCI BRB data archive; its RawData, ProcessedLog and FilteredAndNormalizedLog arrays are identical (median-centred log ratios); missing values set to 0, as stated.", "source": "our_choice"},
        {"what": "Each of the 500 draws per design takes the training samples and 20 test samples per class without replacement from the ER+ and ER- tumours; class 1 is ER+; predictive values use the training proportion of ER+.", "source": "our_choice"},
        {"what": "Fig. 6 and Additional file 12 draw the designs at their ER+ share (50, 66.7, 80, 85.7, 90% with 5 ER-; 50, 66.7, 75, 81.8% with 10 ER-); each plotted point is matched to the nearest design.", "source": "read_from_figure", "sensitivity": "The nearest design is at least 4 points of ER+ share away from the next; a wrong match would put a point 5 or more points off in x."},
    ],
    "figure_values": [
        {"what": "Published values are read from the vector figures: the paper's markers and the supplements' polyline vertices, mapped through each panel's tick marks (largest tick-fit residual below 0.0002 in y); points within 0.0005 of ours count as equal for reading error.", "source": "our_choice"},
        {"what": "Monte Carlo tolerance: |ours - paper| <= printed + z sqrt(se_ours^2 + se_paper^2), se = SD / sqrt(replicates), with the paper's SD where printed and ours otherwise, the paper's 1,000 (500 for the breast cancer data) replicates, and z the Bonferroni value for a 5% chance of any false miss in the item.", "source": "our_choice"},
    ],
    "mu_grid": [
        {"what": "The mu2 grid of Fig. 4 is 0, 0.1, ..., 2.0 and 3, read from the figure's markers; Methods gives 0.1, 0.2, ..., 1.9, 2, 3 and Results 0, 0.25, ..., 2, 2.5, 3.", "source": "read_from_figure",
         "sensitivity": "All 22 plotted x positions fall within 0.0002 of this grid; neither printed grid fits them (0.25 steps would put 13 of the 22 points off the grid)."},
    ],
    "pi": [
        {"what": "Prediction-interval ends are our 2.5th and 97.5th percentiles over replicates (R's quantile type 7); with a 20-sample test set they move in steps of 0.05, and they count as equal within one step.", "source": "our_choice"},
    ],
    "claims": [
        {"what": "Words such as 'about' are read as within 0.05; each claim's reading is stated in its fields and recomputed from the paper's own values first (text.arithmetic).", "source": "our_choice"},
    ],
}


CAUSES = {
    "svm": {"category": "undocumented_setting",
            "summary": "The SVM differs (other classifiers agree): the paper gives no cost and its class weights ('the proportion of samples from each class') leave the direction open. With the default cost 1 the training sets are separable and the weights do nothing, so our SVM is less biased than the paper's in the simulations (Additional file 3, k1train 0.1: PA1 {svm_af3_ours} against 0.03). A smaller cost with the stated weights brings Additional file 3 back (cost 0.1: {svm_c01_af3}; 0.03: {svm_c003_af3}) but sends the null case of Fig. 2 to 0 (cost 0.1: {svm_c01_null} against 0.038). The breast cancer tables need the opposite, weights inverse to the class sizes (20 ER+ / 5 ER-, PA ER-: {svm_inv_er} against 0.6; stated weights {svm_prop_er}). No single cost and weighting fits both.",
            "evidence": ["figure-reproduction/output/hypotheses.json"],
            "hypotheses": [
                {"hypothesis": "Default cost (1) with weights equal to the class proportions, as stated", "test": "Our main run; hypotheses.R grid, cost 1", "result": "rejected"},
                {"hypothesis": "A smaller cost with the stated weights", "test": "hypotheses.R: costs 0.001-1 on Additional file 3 (k1train 0.1, 0.2) and the null case of Fig. 2 (k1train 0.2)", "result": "inconclusive"},
                {"hypothesis": "Weights inverse to the class proportions (the weight vector applied to the other class)", "test": "hypotheses.R: the same grid on the simulations and on 20 ER+ / 5 ER- and 45 ER+ / 5 ER-", "result": "inconclusive"}],
            "status": "open"},
    "dqda_auc": {"category": "undocumented_setting",
                 "summary": "DQDA's AUC is lower than the paper's when the training set is imbalanced (Additional file 3, k1train 0.1: {dqda_auc_ours} against 0.91). The paper does not say which score it ranked. Ranking by the ratio of the two discriminants instead of their difference gives the paper's AUC at every k1train ({dqda_ratio}) and leaves DLDA's AUC where the paper has it ({dlda_ratio} at 0.1 against 0.94); the predictions do not change. Found by search over five scores; our run keeps the difference.",
                 "evidence": ["figure-reproduction/output/hypotheses.json"],
                 "hypotheses": [
                     {"hypothesis": "The AUC ranks the ratio of the DQDA discriminants", "test": "hypotheses.R: DQDA on the same data, AUC by five scores, k1train 0.1-0.5", "result": "supported"},
                     {"hypothesis": "The AUC ranks the predicted class", "test": "The same: 0/1 scores give 0.56 at k1train 0.1", "result": "rejected"}],
                 "status": "explained"},
    "af1": {"category": "paper_error",
            "summary": "Additional file 1 prints the same PA, PA1, PA2, PV1 and PV2 (and SDs) for all nine classifiers; they are PLR's: the paper's own Fig. 1 and Fig. 2 (same settings, p = 40) show other values for the other eight (RF and PAM PA1 near 0 at k1train 0.1, DLDA near 0.2), which our run reproduces. Those cells are listed as paper errors; the AUC columns, which differ by classifier, and PLR's cells are compared.",
            "evidence": ["figure-reproduction/output/published_values.json (af1 against fig1 and fig2)", "figure-reproduction/output/comparison.json"],
            "status": "explained"},
    "af10": {"category": "paper_error",
             "summary": "Additional file 10's caption says the test sets held 500 samples, but its interval ends all sit on a 0.05 grid, which only a 20-sample test set gives. Compared with our 20-sample test sets, {af10_hits} of {af10_n} interval ends match within one step; with 500-sample test sets, {af10_500_hits} of {af10_500_n}.",
             "evidence": ["figure-reproduction/output/comparison.json (af10, af10.ntest500)"],
             "hypotheses": [{"hypothesis": "The intervals come from 20-sample test sets, not 500", "test": "Compare the bar ends with our percentiles for both test sizes", "result": "supported"}],
             "status": "explained"},
}

paper = {"id": "PMC3098087", "title": "Class prediction for high-dimensional class-imbalanced data",
         "citation": "Blagus R, Lusa L. Class prediction for high-dimensional class-imbalanced data. BMC Bioinformatics 11:523 (2010)",
         "doi": "10.1186/1471-2105-11-523", "license": "CC BY 2.0"}


def fig(id_, label, src, sets, **kw):
    d = {"id": id_, "label": label, "kind": "figure", "source": "reconstructed", "method": "values", "from": f"comparison:{src}",
         "assumptions_from": sets, "outputs": kw.pop("outputs", [f"figure-reproduction/output/{src.split('.')[0]}_ours.png", f"figure-reproduction/output/{src.split('.')[0]}_overlay.png"])}
    d.update(kw)
    return d


def table(id_, label, src, sets, **kw):
    d = {"id": id_, "label": label, "kind": "table", "source": "reconstructed", "method": "values", "from": f"comparison:{src}", "assumptions_from": sets}
    d.update(kw)
    return d


def claim(id_, label, src="reconstructed", sets=("simulation", "claims"), **kw):
    d = {"id": id_, "label": label, "kind": "value", "source": src, "method": "values", "from": f"claims:{id_}", "assumptions_from": list(sets),
         "exceptions_rule": "arithmetic"}
    d.update(kw)
    return d


def none(id_, label, kind, category, summary, evidence):
    return {"id": id_, "label": label, "kind": kind, "source": "none", "method": "none",
            "cause": {"category": category, "summary": summary, "evidence": evidence, "status": "explained"}}


SIM = ["simulation", "figure_values"]
items = [
    fig("fig1", "Fig. 1: null case, p = 40, no selection; PA, PA1, PA2 against k1train (nine classifiers)", "fig1", SIM, cause_from="svm"),
    fig("fig2", "Fig. 2: null case, G = 40 of p = 40, 1000, 10000; PA1 (nine classifiers)", "fig2", SIM, cause_from="svm"),
    fig("fig3", "Fig. 3: alternative case, pDE = 20 or p, G = 40; PA1 (1-NN, DLDA, PLR)", "fig3", SIM, cause_from="mc"),
    fig("fig4", "Fig. 4: overall PA against mu2, k1train 0.5-0.9, centred samples or variables (1-NN, DLDA, PLR)", "fig4", SIM + ["mu_grid"], cause_from="mc"),
    fig("fig5", "Fig. 5: no correction, over-sampling, down-sizing, MultDS; PA, PA1, PA2 (3-NN, DLDA, PLR)", "fig5", SIM + ["corrections"], cause_from="mc"),
    fig("fig6", "Fig. 6: ER status, class-specific PA, no correction and MultDS (3-NN, DLDA, PLR), means", "fig6", ["er", "corrections", "figure_values"], cause_from="er"),
    fig("fig6.pi", "Fig. 6: 95% prediction intervals of the class-specific PA", "fig6.pi", ["er", "corrections", "figure_values", "pi"], cause_from="er_pi"),
    table("af1", "Additional file 1: null case, p = 40, balanced test sets of 20 and 500; PA, PA1, PA2, PV1, PV2, AUC", "af1", SIM, exceptions_rule="af1_plr_columns", cause_from="af1"),
    none("af2", "Additional file 2: eight variable-selection methods under the null and alternative", "figure", "undocumented_setting",
         "The paper does not give the settings of the eight selection methods (SAM, WSS and the others), and the figure's panels are not labelled with them in a way we could match to settings; not attempted.",
         ["Methods: 'We observed this behavior not only for t-test with equal variances but also for other commonly used parametric and non-parametric variable selection methods (Additional File 2)'; no settings are given."]),
    table("af3", "Additional file 3: alternative case, p = 1000, pDE = 20, mu2 = 1, test sets of 20 and 500; all measures", "af3", SIM, cause_from="svm"),
    fig("af4", "Additional file 4: Fig. 3 left for all nine classifiers", "af4", SIM, cause_from="svm"),
    fig("af5", "Additional file 5: Fig. 3 right (pDE = p) for all nine classifiers", "af5", SIM, cause_from="svm"),
    none("af6", "Additional file 6: alternative case without variable selection (G = p = 1000), nine classifiers", "figure", "undocumented_setting",
         "Placeholder", []),
    fig("af7", "Additional file 7: Fig. 4 for all nine classifiers", "af7", SIM + ["mu_grid"], cause_from="svm"),
    fig("af8", "Additional file 8: Fig. 5 for all nine classifiers (MultDS for six)", "af8", SIM + ["corrections"], cause_from="svm"),
    none("af9", "Additional file 9: over-sampling with centred variables", "figure", "undocumented_setting", "Placeholder", []),
    fig("af10", "Additional file 10: 95% prediction intervals of the overall PA, four corrections (3-NN, DLDA, RF, PLR)", "af10", SIM + ["corrections", "pi"], cause_from="af10", cause_always=True),
    fig("af11", "Additional file 11: RF-THR and PLR-THR; PA, PA1, PA2", "af11", SIM, cause_from="mc"),
    fig("af12", "Additional file 12: Fig. 6 for all nine classifiers, 95% prediction intervals", "af12", ["er", "corrections", "figure_values", "pi"], cause_from="er_pi"),
    table("af13", "Additional file 13: ER status, no correction; all measures, nine classifiers", "af13", ["er", "figure_values"], cause_from="er"),
    table("af14", "Additional file 14: ER status, MultDS; all measures, nine classifiers", "af14", ["er", "corrections", "figure_values"], cause_from="er"),
    claim("text.null_balanced", "Text: null case, PA = 0.5 and AUC = 0.5 with balanced test sets"),
    claim("text.fig2_1nn", "Text: 1-NN, k1train 0.1, G = 40: PA1 0.02 / 0.00, PA2 0.98 / 1.00 (p = 1000 / 10000)"),
    claim("text.selection_bias", "Text: variable selection biases most classifiers further towards the majority class"),
    claim("text.most_sensitive_null", "Text: RF, SVM and PAM most sensitive to imbalance without selection"),
    claim("text.dlda_least_sensitive", "Text: DLDA shows the smallest decrease in minority-class PA"),
    claim("text.fig4_balanced", "Text: balanced training set, PA reaches 1 at mu2 between 1 and 1.5"),
    claim("text.fig4_imbalanced", "Text: highly imbalanced training set needs mu2 >= 2"),
    claim("text.fig4_selection", "Text: all non-null variables selected in almost all runs when mu2 >= 1.5"),
    claim("text.variable_centering", "Text: centring the variables worsens PA on imbalanced data"),
    claim("text.oversampling", "Text: over-sampling changes little; only 3-NN and 5-NN benefit, 1-NN not at all", sets=("simulation", "corrections", "claims")),
    claim("text.downsizing", "Text: down-sizing at k1train 0.1 gives PA about 0.70 in both classes; full data PA1 = 0", sets=("simulation", "corrections", "claims")),
    claim("text.pam_downsizing", "Text: PAM, k1train 0.2, PA1 0.5 to 0.8 with down-sizing", sets=("simulation", "corrections", "claims")),
    claim("text.downsizing_pi", "Text: down-sizing prediction intervals 0.8-1.0 (k1train 0.5) and 0.50-0.90 (0.10)", sets=("simulation", "corrections", "pi", "claims")),
    claim("text.multds_flat", "Text: MultDS PA flat for k1train 0.20-0.80", sets=("simulation", "corrections", "claims")),
    claim("text.multds_k01", "Text: MultDS at k1train 0.1, PA about 0.85, interval 0.7-1.0", sets=("simulation", "corrections", "pi", "claims")),
    claim("text.multds_vs_down", "Text: MultDS consistently better than down-sizing", sets=("simulation", "corrections", "claims")),
    claim("text.thr_null", "Text: RF-THR and PLR-THR reduce but do not remove the dependence on imbalance (null case)"),
    claim("text.data_counts", "Text: 99 tumours, 7650 probes, ER- 34 / ER+ 65, grade 54 / 45", src="public_data", sets=("er",)),
    claim("text.er_20_5", "Text: ER, 20 ER+ / 5 ER-: PA ER+ > 0.90, PA ER- 0.2-0.6, PV and AUC ranges", sets=("er", "claims")),
    claim("text.er_downsizing", "Text: ER down-sizing, class-specific PA about 0.75 (5 per class) and 0.85 (10 per class)", sets=("er", "corrections", "claims")),
    claim("text.er_oversampling", "Text: ER over-sampling, gap of 0.22 between class-specific PA (DQDA, 20 ER+ / 10 ER-)", sets=("er", "corrections", "claims")),
    claim("text.er_multds_pi", "Text: ER, MultDS lower interval limits above 0.60 for most classifiers; down-sized intervals include 0.50", sets=("er", "corrections", "pi", "claims")),
    claim("text.pam_multds", "Text: ER, PAM benefits the most from MultDS", sets=("er", "corrections", "claims")),
    claim("text.er_variable_centering", "Text: ER, centring the variables increases the bias", sets=("er", "claims")),
    none("text.grade", "Text: grade 1-2 against 3: overall PA about 0.60 and 0.70, minority PA 0.10-0.20", "value", "undocumented_setting",
         "The training and test sizes of the grade problem are not stated and its results are 'data not shown'; not attempted.",
         ["Results: 'Grade of breast cancer was more difficult to predict than ER status (overall PA about 0.60 using the small balanced training set and about 0.70 when using the larger training set, data not shown)'."]),
    none("methods.equations", "Equations 1-6: classification rules and measures", "value", "not_a_result",
         "Definitions, not results: they are implemented in multds (dlda, dqda, evaluate, predictive_values) and checked by the port check and the package tests.",
         ["package/R/classifiers.R", "package/R/metrics.R"]),
    {"id": "text.arithmetic", "label": "Claims in the text recomputed from the paper's own figures and tables", "kind": "code_check", "source": "papers_data", "method": "check", "from": "arithmetic"},
    {"id": "port", "label": "DLDA and DQDA against sma::stat.diag.da (the code the paper used); AUC against Hmisc", "kind": "code_check", "source": "port", "method": "check", "from": "port"},
    {"id": "package", "label": "R package multds and its tutorial", "kind": "code_check", "source": "reconstructed", "method": "check", "from": "package",
     "outputs": ["package/tutorial/TUTORIAL.md"]},
]

notes = {
    "paper": paper,
    "run": {"date": "2026-11-17", "pipeline": "PMC3098087/figure-reproduction/main.nf",
            "command": "nextflow run PMC3098087/figure-reproduction/main.nf --outdir results", "inputs": inputs},
    "session": {"ledger": "session/ledger.json"},
    "skill": old.get("skill", {}),
    "assumption_sets": A,
    "causes": CAUSES,
    "items": items,
    "page": old.get("page", {}),
}
OUT.write_text(json.dumps(notes, indent=1, ensure_ascii=False) + "\n")
print(f"{OUT}: {len(items)} items")
