# Mockup: AI review section in the results-check PR comment

This is a draft for review. Nothing is built yet. Each case below shows the section that would be added at the end of the existing per-paper comment (after the diffs and figure overlays). The text uses real items from PMC2661051, as changed in PR #89.

Rules the AI follows:
- It reviews only items whose verdict, values, cause or review the PR changes.
- It uses only what is in the repository: paper value, our value, tolerance, verdict, cause, hypotheses, reviewer note. It does not add reasons of its own.
- It never edits files. A normal PR approval is the final conclusion.
- If the AI step cannot run, the check fails (case 7).

---

## Case 1: a PR that changes several items (normal case)

> #### 🤖 AI review of the 5 items this PR changes
>
> | Item | Verdict | In one line | |
> | --- | --- | --- | --- |
> | Table 4, significance assessment | **exact** | All 36 rates are within the allowed band. | ✅ |
> | Table 2, statistic x transformation | **partly** (reviewer; computed agrees) | Numbers match, but one setting was picked after looking at the paper. | ✅ |
> | Table 5, globaltest | **agrees** (reviewer; computed partly) | 35 of 36 match; the odd one out was chance. | ✅ |
> | Fig. 2 right, p53 sets with p ≤ 0.01 | **partly** | 9 of 16 bars match; cond. FDR finds far fewer sets. Cause still open. | ✅ |
> | Text: globaltest is very close to the mean | **differs** | Off by 0.06 against a 0.05 limit we set, which is within chance. | ⚠️ worth a look |
>
> <details><summary><b>Table 4: exact</b>, why it matched</summary>
>
> All 36 rates in the table land within the allowed band of the paper's printed values. Example: set 1, parametric is 0.75 here and 0.82 in the paper, with ±0.15 allowed. No setting had to be guessed, so this is a clean match.
> </details>
>
> <details><summary><b>Table 2: partly</b> (reviewer overruled <i>agrees</i>), why it only partly matched</summary>
>
> **The numbers alone say "agrees":** all 135 of 135 rates are inside the chance band.
> **Why it is still "partly":** the paper does not give two settings. One of them, the cutoff for the binary transformation, was chosen as p ≤ 0.05 after the paper's rule (local fdr ≤ 0.2) was tried and gave much lower rates (0.13 against 0.61). A match that relies on a setting picked to fit is weaker, so reviewer SophSM [set it to partly](https://github.com/jeonglab-bcm/fossil/pull/89#pullrequestreview-5945209320).
> </details>
>
> <details><summary><b>Table 5: agrees</b> (reviewer overruled <i>partly</i>), why it matched</summary>
>
> 35 of 36 rates match. The one that does not, set 3 parametric (0.13 here, 0.02 in the paper), was rerun on 400 more data sets and came out at 0.050. So the 0.13 was bad luck in our 100 data sets, not a real difference. Reviewer SophSM accepted this and set the verdict to agrees.
> </details>
>
> <details><summary><b>Fig. 2 right: partly</b>, why it only partly matched</summary>
>
> 9 of 16 bars are within one set of the paper (Hotelling, globaltest, ES, maxmean).
> **The main miss:** cond. FDR finds 10 and 7 sets, against 38 and 35 in the paper. On the p53 data, the fdrtool package gives every gene a local fdr of 1, so our cond. FDR loses most of its power.
> **Smaller misses:** Wilcoxon, median and mean-by-permutation are off by 3 to 5 sets.
> **Status: open.** The cause is a likely explanation, not a proven one.
> </details>
>
> <details><summary>⚠️ <b>Text: globaltest is close to the mean: differs</b>, worth a look</summary>
>
> **Why it says differs:** the largest gap is 0.06 (set 9: 0.86 against 0.92), and we called "close" anything within 0.05.
> **Why it may deserve another look:** the repository's own cause says this gap is **within chance**. The 99% band for two shares of 100 is ±0.12, and the paper's own tables differ by up to 0.04. The 0.05 limit was our choice, not the paper's. By the evidence in the repository, the claim may hold and the verdict may be too harsh. The verdict is computed from a fixed 0.05 rule, so changing it would take a reviewer `review` block or a different limit.
> </details>
>
> **Final conclusion:** approve this PR if you accept the verdicts above. Before approving, check the ⚠️ item.

---

## Case 2: only matches, nothing to flag

> #### 🤖 AI review of the 2 items this PR changes
>
> | Item | Verdict | In one line | |
> | --- | --- | --- | --- |
> | Table 4, significance assessment | **exact** | All 36 rates are within the allowed band. | ✅ |
> | Text: Hotelling hardly detects the correlated sets | **exact** | The claim holds in our numbers too. | ✅ |
>
> *(one collapsed paragraph per item, as in case 1)*
>
> **Final conclusion:** nothing flagged. Approve this PR if the changes are what you meant.

---

## Case 3: an item that was not attempted

> | Item | Verdict | In one line | |
> | --- | --- | --- | --- |
> | Fig. 2 left, significant p53 sets against the cutoff | **not attempted** | Drawn and overlaid, but not scored: the curves can't be read off the paper's figure. | ✅ |
>
> <details><summary><b>Fig. 2 left: not attempted</b>, why it wasn't scored</summary>
>
> Our figure is drawn and overlaid on the paper's, but no number was compared. In the paper, sixteen curves with letter markers sit on top of each other, so their values can't be read. Reading by colour and marker was tried and failed. The same results are still checked another way: the 0.01 cutoff through Fig. 2 right, and the ranking through the text claims.
> </details>

---

## Case 4: a verdict the AI thinks is too generous

> | Item | Verdict | In one line | |
> | --- | --- | --- | --- |
> | Table 3, gene set statistics | **agrees** | All rates are within the band, but a setting is marked as guessed. | ⚠️ worth a look |
>
> <details><summary>⚠️ <b>Table 3: agrees</b>, worth a look</summary>
>
> The numbers match. But the item's assumptions list a setting with source `our_choice`, and its own note says the setting was tuned after seeing the paper. For Table 2, the same situation led the reviewer to choose **partly**. You may want to be consistent here.
> </details>

*(This one is a made-up example to show the flag; Table 3 is partly in the repository.)*

---

## Case 5: a new paper (the PR adds results.json, so every item is new)

To keep the comment readable, the AI gives a short explanation per item only for the ones that don't match. Matched items appear as table rows only.

> #### 🤖 AI review of PMC2661051 (new: 46 items)
>
> **19 exact, 7 agrees, 8 partly, 8 differs, 4 not attempted.**
>
> **The main claims hold:** the mean of squared moderated t beats GSEA's ES and Hotelling.
> **What mostly does not match:**
> - Our cond. FDR is not the paper's (4 items).
> - The Hedenfalk gene mapping differs (3 items).
> - Chance, in one case.
>
> | Item | Verdict | In one line | |
> | --- | --- | --- | --- |
> | … one row per item, ⚠️ where flagged … | | | |
>
> *(collapsed explanations for the 20 partly / differs / not attempted items)*
>
> **Final conclusion:** approve this PR if you accept the verdicts above. Before approving, check the ⚠️ items.

---

## Case 6: the PR changes no verdicts

For example, a PR that only changes the pipeline code or the README.

> #### 🤖 AI review
> No item's verdict, values, cause or review changes in this PR. There is nothing to review.

---

## Case 7: the AI step could not run (the check fails)

> #### 🤖 AI review: ❌ not run
> `ANTHROPIC_API_KEY` is not available to this run. A PR from a fork does not get repository secrets.
> The **Results check / AI review** check is marked failed. Re-run it once the key is available, or have a maintainer push the branch to this repository.

The same thing happens on an API error. That error is shown in place of the key message, for example `529 overloaded, retried 3 times`.

---

<sub>Mockup for discussion. Uses real items from PMC2661051 (PR #89) except case 4.</sub>
