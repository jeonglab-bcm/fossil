"""ROC and ROC50 scores (Gribskov and Robinson 1996), as in Liao and Noble's benchmark.

ROC_n = (1 / (n P)) sum_{i=1..n} t_i, with t_i the number of positives scored above the i-th
highest-scoring negative and P the number of positives; ROC uses n = all negatives, ROC50
n = 50. A positive tied with a negative counts one half.
"""
import numpy as np


def roc_n(scores, positive, n=None):
    scores = np.asarray(scores, dtype=float)
    positive = np.asarray(positive, dtype=bool)
    pos = np.sort(scores[positive])
    neg = np.sort(scores[~positive])[::-1]
    if n is None:
        n = len(neg)
    n = min(n, len(neg))
    P = len(pos)
    neg = neg[:n]
    above = P - np.searchsorted(pos, neg, side="right")
    ties = np.searchsorted(pos, neg, side="right") - np.searchsorted(pos, neg, side="left")
    return float((above + 0.5 * ties).sum() / (n * P))


def roc_scores(scores, positive):
    return roc_n(scores, positive), roc_n(scores, positive, 50)
