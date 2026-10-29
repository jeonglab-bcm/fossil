# Fresh verifier report: odemm-paper (PMC4081021)

Package verified: `/Users/hyunhwanj/wss/fossil/PMC4081021/staging/odemm-paper`
Originals: `paper-review/originals/s001-pcbi-1003686.pdf` (17 pp.), `s002-pcbi-1003686-s002.pdf` (14 pp.); JATS `sources/fulltext.xml` for cross-checks.
Method: PyMuPDF renders (110 dpi full pages, 170–300 dpi clips) viewed directly, plus scripted word-level diffs of every package paragraph against the PDF text layer and the JATS paragraphs, and cell-by-cell CSV comparison. No package file was edited.

## Verdict

No content defects found. Text, reading order, figures, tables and equations match the originals. The defects below are about formatting, consistency, navigation and status. None changes what the paper says.

## Defects

| # | Document | Location | Source shows | Package shows | Severity |
|---|---|---|---|---|---|
| D1 | paper.md | Results › "Pathway model" (line 232), after the pathway model A reaction display | Display R1–R5, then the sentence continues on a new line "and is illustrated in Figure 3A. The reactions R1 and R2 describes …" | The closing `$$` and the prose "and is illustrated in Figure 3A …" are on the same line. Every other display in both files is on its own line(s). The text itself is correct. | Low (formatting; line-oriented tools and some renderers will treat the prose as part of the math block) |
| D2 | assets/table/*.csv vs assets/supp_table/*.csv | All table CSVs | Same typographic minus and model symbol ℳ<sub>H3,3</sub> in every table | `table-1.csv` uses ASCII `-` for negatives (`-1.9534`) and IDs `ℳH1,1`. `table-2.csv` and all supp tables use U+2212 `−` (`−5.2890`) and `ℳ_H1,1`. Also `[Erk]_0` in table-2 vs `[Erk]0` in supp table 1, and header `ℓ(θ*)(10⁴)` vs `ℓ(θ*) (10^4)`. The values are correct. | Low (a search for `ℳ_H3,3` misses Table 1; naive float parsing fails on U+2212, and no note mentions this) |
| D3 | supplement.md / index.md | After `### References` (lines 340–488) | Supplement Table 1, Figs 1–2 and Tables 2–4 are on pp. 9–14 after the reference list, with no heading | These floats are nested under the `### References` heading. index.md has no row pointing to the supplementary tables or figures. The order is faithful to the PDF. | Low (navigation: an agent going by headings would not look under "References") |
| D4 | supplement.md | §3.1.1–3.3.2 reaction and RRE displays | Species names upright (TrkA, NGF, pErk) | Bare names in math mode (`TrkA + NGF → TrkA:NGF`, `[pErk]`) render as italic variable products. paper.md uses `\mathrm{}` for the same equations. | Cosmetic |
| D5 | SKILL.md | Line 8 | — | "**Draft: source review or verification remains unresolved.**" `paper-review/build.json` names `staging/odemm-paper2` as the latest build. That build is byte-identical to this one except for SKILL.md ("Source review is complete with documented limitations."). `verification.json` reports `reviewed_with_limitations` with 0 issues. The folder I was given carries a stale draft label. | Informational (make sure the delivered folder comes from the current build) |
| D6 | references/index.md | Both navigation tables | — | The "Look here for" column is empty in every row. | Informational |

## Coverage and results by check

### 1. Structure and reading order
- **Headings:** all 31 main-paper headings are present in source order, including the run-in headings used as `####`. The source typo "NFG-induced" is kept. All supplement headings 1–4 and their subsections are present, and the Contents list matches p. 1.
- **Paragraph order (JATS):** 236 start/end 9-word keys of every JATS body paragraph and paragraph chunk were checked. Each occurs exactly once in paper.md and in source order. The one apparent miss was a `$>1$` inline-math artefact.
- **Word-level text:** every paragraph in paper.md and supplement.md was diffed against the PDF text layer, and paper.md also against JATS. The only differences are inline math removed by the diff, decomposed diacritics in the PDF text layer, page furniture, and ligature glyphs (ﬁ, ﬀ) in the supplement. No word was dropped, added or substituted.
- **Paragraphs across page breaks and floats:** checked intact at p2→3, 3→4, 4→5, 5→6, 6→7→8, 8→10, 10→11, 11→12→13, 13→14 and 14→15.
- **Line-wrap hyphens:** every PDF line-end hyphen resolves correctly, keeping real compounds such as anti-phospho-Erk, Discreteness-induced and laminin-precoated.
- **Float placement:** Fig 1 sits after Mixture models. Fig 2 and Table 1 close the simulation example. Fig 3 ends "Quantification…". Table 2 sits between two paragraphs of "Comparison of pathway models". Figs 4 and 5 follow "As subpopulations 1 and 2…". Fig 6 sits before the Discussion. All are at paragraph boundaries with no spliced sentence. The supplement keeps the PDF order.

### 2. Figures (all 8 checked against the page renders)
- **Crops:** figure-1 to figure-6 and supplementary-figure-1/2 include every panel letter, legend and axis, with no edge clipping. The supp figures keep the full green frames and the top legend.
- **Smallest labels:** these are legible: Fig 5A pathway labels (extracellular, GDP/GTP, Ras/Raf/Mek), the Fig 3D and 4D parameter axes, and the Supp Fig tick labels and σ subscripts.
- **Captions:** they match the source. JATS diffs differ only in title, DOI and formula placeholders. Source errors are kept and noted: Fig 4D names ℳ<sub>H1,2/H1,3</sub>, Supp Fig 2 names ℳ<sub>H3,2</sub>, Fig 6 says "NFG" and Fig 5 says "media". I confirmed independently that Supp Fig 2's panels match ℳ<sub>H3,3</sub>: the k1 peak is about −0.55 and w1 about 0.688, which agrees with Supp Table 2.

### 3. Tables
- **Table 1:** all 240 data cells match JATS with 0 mismatches. They also match the PDF p. 9 text layer, and model labels and row order were checked visually.
- **Table 2:** all 90 data cells match JATS and the PDF p. 11 text, with 0 mismatches.
- **Supp Table 1:** all 297 cells (27 rows × 11) match the PDF p. 9 text, with 0 mismatches.
- **Supp Tables 2–4:** all 273 non-empty cells match the PDF text, with 0 mismatches. The 3 rows my script flagged were the merged weight "1" cells, which I confirmed visually.
- **Visual spot-check:** more than 30 cells checked on renders. On p. 13 I checked rows ℳ<sub>H1,1</sub>, ℳ<sub>H2,3</sub> and ℳ<sub>H3,3</sub> (subpopulation 1) and ℳ<sub>H2,2</sub> and ℳ<sub>H3,2</sub> (subpopulation 2), all 5 columns each. On p. 12 I checked the swapped ℳ<sub>H3,1</sub> weight intervals, ℳ<sub>H2,2</sub> log10(k2), ℳ<sub>H3,3</sub> log10(k3[TrkA]0,1) and ℳ<sub>H2,1</sub> s[Erk]0,2. On p. 9 I checked model B ℳ<sub>H3,2</sub> and model C ℳ<sub>H2,3</sub>.
- **Merged cells:** they are represented by explicit "(merged cell)" columns, which is consistent with the PDF.

### 4. Equations
- **Main paper:** numbered equations (1)–(6) and the unnumbered maximum-likelihood problem in Methods were compared with 110–300 dpi renders. This covered sums and limits, the superscripts and subscripts y<sub>j</sub><sup>k,e</sup> and φ<sub>i</sub><sup>e</sup>(t<sub>k</sub>), the constraints and tags. All are correct. The unnumbered Results displays (conversion RRE, model A reactions, conservation, RRE, reformulated RRE) are also correct.
- **Supplement:** 16 display blocks were checked. These were model A (reactions, conservation, RRE, reformulated ODE, initial condition), model B (reactions, conservation, RRE, reformulated RRE, the 5-line initial-condition fraction chain) and model C (R3 Hill-type rate, RRE, parameter vector with K3 listed twice as printed, reformulated RRE, reduced vector). All are correct. Source typos are kept: the unbalanced "(k3" numerator in model C, and x1 = [TrkA:NGF]/k3 in model A, which is noted.
- **Syntax:** all `$`/`$$` delimiters are balanced and no braces are unbalanced in either file.

### 5. Prose and references
- **Word-by-word reading:** more than 15 paragraphs were read against the renders: Abstract, Intro ¶1–3, Ethics, Measurement data, Mixture models, Pathway models ¶3, Population model, Hypothesis testing bounds, Interpretation, Pathway model, Size/characteristics ¶3, Validation ¶2, Discussion ¶1, and supplement §1.3, §1.7, §2 and §3.2.3. This is in addition to the automated diff of every paragraph.
- **References:** main references are numbered 1–85 contiguously, and the PDF has 85 entries. Their text matches as printed, including "8519–8124", "acidtransformation", "Ibàñez", "Proc Nati" and the missing fl/ffi ligatures. Supplement references [1]–[4] match.

### 6. Retrieval test (package only)
**Question:** What parameter bounds and how many multi-start runs were used for pathway model B, and which model won?

**Answer from the package:**
- **Runs** (supplement §2): at least 100 local optimiser runs per model. The number was increased if the best objective value was found fewer than 5 times. All parameters except the weights were log-transformed.
- **Bounds** (§3.2.3): k<sub>i</sub> ∈ [10<sup>−3</sup>, 10<sup>3</sup>], narrowed from model A because of ODE-solver problems. w<sub>i</sub> ∈ [0, 1]. Normal SDs ∈ [10<sup>−1</sup>, 10<sup>2</sup>] and log-normal shape ∈ [10<sup>−1</sup>, 10<sup>1</sup>].
- **Winner** (`supplementary-table-1.csv`): ℳ<sub>H3,3</sub>, with BIC 7.1965 × 10<sup>4</sup> and ΔBIC 0. For comparison, Table 2 (model A) has ℳ<sub>H3,3</sub> at BIC 7.2001 × 10<sup>4</sup>.

The package was sufficient, and its `rg`/`sed` workflow found the evidence in 3 commands.
