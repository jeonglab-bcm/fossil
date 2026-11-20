"""Read Additional file 2 (13059_2014_484_MOESM2_ESM.xlsx), the paper's list of 3,706 mutations.

One sheet; row 1 is the title, rows 2-3 the headers, rows 4-3,709 the mutations, then a blank row and a
footnote. Columns A-BM: mutation, SNV flag (K), sources, COSMIC v68 id (N), functional evidence, the
functional classification (AC), presence in six training sets (AD-AI), and a category and a score for
each of the 15 predictors (AJ-BM).
"""
import warnings

import openpyxl

PRED = ["CHASM (breast)", "CHASM (lung)", "CHASM (melanoma)", "FATHMM (cancer)", "FATHMM (missense)",
        "Mutation Assessor", "MutationTaster", "PolyPhen-2", "PROVEAN", "SIFT", "VEST",
        "CanDrA (breast)", "CanDrA (lung)", "CanDrA (melanoma)", "Condel"]
SINGLE = PRED[:11]
META = PRED[11:]
TRAINING = ["CHASM (breast)", "CHASM (lung)", "CHASM (melanoma)", "FATHMM (cancer)", "FATHMM (missense)", "PolyPhen-2"]
# Columns AD-AI hold the training-set flags. The headers of AG and AH are swapped in the sheet: AG
# ('FATHMM (cancer) v2.3 training set') holds the entries 'Disease' (and 'Polymorphism') of
# FATHMM's inherited-disease (missense) training set, and AH ('FATHMM (missense) v2.3 training set') the
# entries 'CANCER' (and 'Polymorphism'). We read
# each column by its content; load() checks it.
TRAINING_COLUMNS = {"CHASM (breast)": 29, "CHASM (lung)": 30, "CHASM (melanoma)": 31, "FATHMM (cancer)": 33,
                    "FATHMM (missense)": 32, "PolyPhen-2": 34}
FIRST_ROW, LAST_ROW = 4, 3709


def load(xlsx):
    """Every mutation as a dict: type, gene, aa, snv (bool), cosmic (id or None), label
    ('non-neutral', 'neutral', 'uncertain'), training {predictor: bool}, cat {predictor: str or None},
    score {predictor: float or None}."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    ws = wb["Additional file 2"]
    out = []
    for r in ws.iter_rows(min_row=FIRST_ROW, max_row=LAST_ROW, max_col=65, values_only=True):
        rec = {"type": r[0], "gene": r[1], "aa": r[4], "snv": r[10] == "SNV",
               "cosmic": r[13] if r[13] not in (None, "") else None,
               "label": (r[28] or "").strip(),
               "training": {p: r[c] not in (None, "") for p, c in TRAINING_COLUMNS.items()},
               "training_entry": {p: r[c] for p, c in TRAINING_COLUMNS.items()},
               "cat": {}, "score": {}}
        for i, p in enumerate(PRED):
            c, s = r[35 + 2 * i], r[36 + 2 * i]
            rec["cat"][p] = c.strip() if isinstance(c, str) and c.strip() else None
            rec["score"][p] = float(s) if isinstance(s, (int, float)) else None
        out.append(rec)
    if len(out) != 3706 or out[-1]["gene"] is None:
        raise ValueError("Additional file 2 does not have the expected 3,706 mutations")
    entries = {p: {str(r["training_entry"][p]).strip().upper() for r in out if r["training"][p]} for p in ("FATHMM (cancer)", "FATHMM (missense)")}
    if not ("CANCER" in entries["FATHMM (cancer)"] and "DISEASE" not in entries["FATHMM (cancer)"]
            and "DISEASE" in entries["FATHMM (missense)"] and "CANCER" not in entries["FATHMM (missense)"]):
        raise ValueError(f"FATHMM training-set columns are not as expected: {entries}")
    return out


def snvs(rows):
    return [r for r in rows if r["snv"]]
