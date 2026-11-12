"""Classifier statistics as Weka 3.4 reports them for a two-class ADTree.

``scores`` are additive ADTree scores (negative = class 0). Weka turns a score s into the class-0
probability 1 / (1 + e^s) and predicts the class with the larger probability, so a score of exactly
0 goes to class 0. The ROC curve and its area follow weka.classifiers.evaluation.ThresholdCurve.
"""

from __future__ import annotations

import math


def class0_probability(score: float) -> float:
    return 1.0 / (1.0 + math.pow(math.e, score))


def predict(score: float) -> int:
    p0 = class0_probability(score)
    p1 = 1.0 / (1.0 + math.pow(math.e, -score))
    return 0 if not p1 > p0 else 1


def confusion(classes: list[int], scores: list[float]) -> list[list[int]]:
    """[[class 0 predicted 0, class 0 predicted 1], [class 1 predicted 0, class 1 predicted 1]]"""
    if len(classes) != len(scores):
        raise ValueError("classes and scores differ in length")
    cm = [[0, 0], [0, 0]]
    for c, s in zip(classes, scores):
        cm[c][predict(s)] += 1
    return cm


def kappa(cm) -> float:
    rows = [cm[0][0] + cm[0][1], cm[1][0] + cm[1][1]]
    cols = [cm[0][0] + cm[1][0], cm[0][1] + cm[1][1]]
    total = float(sum(rows))
    chance = (rows[0] * cols[0] + rows[1] * cols[1]) / (total * total)
    correct = (cm[0][0] + cm[1][1]) / total
    return (correct - chance) / (1 - chance) if chance < 1 else 1.0


def roc_curve(classes: list[int], scores: list[float], positive: int = 0) -> list[tuple[float, float, float]]:
    """Weka's threshold curve for ``positive``: (FP rate, TP rate, threshold) from (1, 1) down."""
    probs = [class0_probability(s) if positive == 0 else 1.0 / (1.0 + math.pow(math.e, -s)) for s in scores]
    tot_pos = float(sum(1 for c in classes if c == positive))
    tot_neg = float(len(classes) - tot_pos)
    order = sorted(range(len(probs)), key=lambda i: probs[i])
    tp, fn, fp, tn = tot_pos, 0.0, tot_neg, 0.0
    out = []
    threshold = 0.0
    cum_pos = cum_neg = 0.0
    for k, i in enumerate(order):
        if k == 0 or probs[i] > threshold:
            tp -= cum_pos
            fn += cum_pos
            fp -= cum_neg
            tn += cum_neg
            threshold = probs[i]
            out.append((fp / (fp + tn) if fp + tn > 0 else 0.0, tp / (tp + fn) if tp + fn > 0 else 0.0, threshold))
            cum_pos = cum_neg = 0.0
            if k == len(order) - 1:
                break
        if classes[i] == positive:
            cum_pos += 1.0
        else:
            cum_neg += 1.0
    return out


def roc_area(curve) -> float:
    """ThresholdCurve.getROCArea: trapezoids from the first point, closed at (0, 0)."""
    if not curve:
        return float("nan")
    area = 0.0
    xlast, ylast = 1.0, 1.0
    fp0, tp0 = curve[0][0], curve[0][1]
    for x, y, _ in curve[1:]:
        x, y = x / fp0, y / tp0
        area += (y + ylast) * (xlast - x) / 2.0
        xlast, ylast = x, y
    if xlast > 0.0:
        area += ylast * xlast / 2.0
    return area


def roc_hull(curve) -> list[tuple[float, float]]:
    """Upper convex hull of the ROC points, from (0, 0) to (1, 1)."""
    pts = sorted({(0.0, 0.0), (1.0, 1.0), *((x, y) for x, y, _ in curve)})
    hull: list[tuple[float, float]] = []
    for p in pts:
        while len(hull) >= 2:
            (x1, y1), (x2, y2) = hull[-2], hull[-1]
            if (x2 - x1) * (p[1] - y1) - (y2 - y1) * (p[0] - x1) >= 0:
                hull.pop()
            else:
                break
        hull.append(p)
    return hull


def evaluate(classes: list[int], scores: list[float]) -> dict:
    """Accuracy, precision, recall and FP rate of class 0, kappa, ROC curve and area, as Weka gives them."""
    cm = confusion(classes, scores)
    n = sum(map(sum, cm))
    pred0 = cm[0][0] + cm[1][0]
    curve = roc_curve(classes, scores, 0)
    return {
        "n": n,
        "confusion": cm,
        "pct_correct": 100.0 * (cm[0][0] + cm[1][1]) / n,
        "precision_disease": cm[0][0] / pred0 if pred0 else 0.0,
        "recall_disease": cm[0][0] / (cm[0][0] + cm[0][1]),
        "fp_rate_disease": cm[1][0] / (cm[1][0] + cm[1][1]),
        "kappa": kappa(cm),
        "auc_disease": roc_area(curve),
        "roc": [list(p) for p in curve],
    }
