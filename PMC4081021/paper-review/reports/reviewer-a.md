# Reviewer A report: s001-pcbi-1003686, pages 1–9

All nine page files (`pages/page-0001.json` … `page-0009.json`) are edited, valid JSON and `reviewed: true`, with specific `review_notes`. I checked every page against its preview and against 3–4x PyMuPDF crops, using rotated renders for page 9. I also cross-checked prose and Table 1 against the publisher JATS (`sources/fulltext.xml`), which has math only as images. Item IDs are unique across all 17 pages. My pages use three asset names: `figure-1`, `figure-2` and `table-1`.

I did not touch `plan.json`, `bundle.json`, `adjudications.json` or page 10+. I ran no build commands.

Note on scope: the brief says "Pages 8 and 10 of other ranges are read-only context". It also lists 0001–0009 as my exclusive pages, so I edited page 8. Please confirm that no other reviewer also edited page 8.

## Conventions used (for consistency with reviewer B)

- **Headings:** the title stays `#`. Main sections are `##` (Abstract, Introduction, Author Summary, Methods, Results). Subsections are `###`. The paper's bold run-in paragraph heads are split into separate `####` heading items, with the trailing period dropped; the publisher XML treats them as level-3 `<sec>` titles. The new heading IDs end in `h`, e.g. `p0005-b015h`.
- **Model names:** written as `ℳ<sub>H3,2</sub>`, following the coordinator's note. In the Table 1 CSV they are written `ℳH1,1`.
- **Inline math:** LaTeX `$...$`, re-transcribed from crops. The native layer garbles every symbol-font glyph:
  - `j`→ξ, `h`→θ, `Q`→φ, `m`→μ, `S`→Σ, `n`→ν
  - `~`→=, `D`→|, `z`→+, `{`→−, `w`→>, `[`→∈
  - `½ \x03`→[ ]
- **Coverage-friendly variants:**
  - Reaction names in prose are `R<sub>1</sub>`.
  - Approximate values are written `∼1.6`.
  - Super/subscripts are written as `\mathcal{D}^e_k`, `t^e_k`, `x^e_i`, so the canonical text keeps the native order.
- **Display equations:** transcribed as LaTeX display math in `text` items. These are Eqs. (1)–(6), plus the unnumbered ML problem, the reaction schemes, the RREs and conservation relations, and the page-8 ODE systems. Each was checked symbol by symbol at 4x. The original equation bboxes are kept on the items. No `equation-N` image assets remain on my pages.
  - If you prefer images instead, flip these IDs back to `kind: "formula"` and give them an `asset_name`: `p0002-b015`, `p0002-b017`, `p0003-b007`, `p0004-b003`, `b008`, `b010`, `b017`, `p0005-b010`, `b013`, `p0006-b013`, `p0007-b004`, `p0008-b002`, `b004`.
- **Running header and footers:** set to `omit` with reasons. The two footer lines, the page number and the running header "ODE Constrained Mixture Modelling" were all confirmed as repeated furniture on every page.
- **Line-wrap hyphens:** real compound hyphens lost at line ends are restored: NGF-induced, time-dependent, ODE-MMs, anti-phospho-Erk, log-standard, TrkA:NGF-induced, log-normal. Soft hyphens are left joined.

## Per page

**Page 1**
- Changes:
  - Title heading kept as `#`.
  - CrossMark badge → `omit`.
  - Author line demoted from `##` heading to text, with the asterisk escaped.
  - Fixed © (native gave U+FFFD).
  - Split Competing Interests into new item `p0001-b010a`; added bold field labels as printed.
  - Italicised the journal name in "This is a *PLOS Computational Biology* Methods article."
  - Footers and page number omitted.
- Order: metadata, then the left column, then the right column. This was already correct.
- Doubt: the editor is printed "Jorg Stelling" with no umlaut, and I kept it.

**Page 2**
- Changes:
  - `p0002-b003` joins page 1 ("false positives / and/or false negatives").
  - `p0002-b006` joins `b005` across the column break.
  - The Author Summary box (`b001`, `b002`) is placed after the end of the Introduction (`b007`) and before `## Methods`. This keeps the prose unsplit; see the reading_order proposal below.
  - Fixed "für" and italicised the authority name.
  - Measurement-data and mixture-model inline math re-transcribed; Eq. (1) and the ML problem are now LaTeX.

**Page 3**
- Changes:
  - `b001` joins page 2; "not/ hardly" → "not/hardly", confirmed against the XML.
  - Figure 1 is one image covering panels A–D, including the embedded comparison table in panel C. Its bbox is tightened to [55,266,547,645] around the raster [58.1,270,543.3,641.3].
  - The caption is a separate item with a bold title.
  - Figure 1 + caption are placed at the paragraph boundary before `### Pathway models`, so the paragraph running onto page 4 is not split.
  - `b005` joins `b004` across the column break.
  - Eq. (2) and the inline math are LaTeX.

**Page 4**
- Changes:
  - `b001` joins page 3, and `b015` joins `b014` across the column break.
  - The extractor's formula `p0004-b017` had swallowed the paragraph under "Parameter estimation and model selection". I split it into new text `p0004-b017a` and Eq. (6) (bbox [345,279,556,368]).
  - Eqs. (3)–(6) are LaTeX.
- Doubt: `ν_i` vs. an italic `v_i`. The glyph is symbol-font "n", the same mapping as m→μ, so I chose ν.
- Kept as printed: "$j-$th" (printed with a minus sign).

**Page 5**
- Changes:
  - `b001` joins page 4, and `b012` joins `b011` across the column break.
  - Run-in heads become `####` headings: "Population model and artificial data" and "Hypothesis testing".
  - The reaction scheme and the RRE are LaTeX.
  - H1–H4 are list items.
- Kept as printed: the heading typo "NFG-induced", which is also in the XML.

**Page 6**
- Changes:
  - `b001` joins page 5, and `b007` joins `b006`.
  - Four run-in heads become `####`.
  - The extractor's "table" `p0006-b013` is really the R1–R5 reaction scheme of pathway model A. I converted it to LaTeX display math.
  - Intervals [10^{-6},10^{4}] and [10^{-2.5},10^{2.5}] re-transcribed.

**Page 7**
- Changes:
  - Figure 2 is one image covering panels A–G; its bbox is tightened to [55,57,547,537] around the raster [58.1,60.8,544.0,533.2].
  - The caption is a separate item; `w_1` is fixed.
  - The conservation relations are LaTeX.
  - `b003` continues the sentence after the page-6 reaction display, but is not joined because the previous item is display math.
- Kept as printed: "R1 and R2 describes", and "Basal and TrkA:NGF-induced … captured by R3 and R4". This order contradicts the R3/R4 definitions on page 6.
- Also kept as printed: the Figure 2 caption's "(B,E) Histograms", which the XML confirms.

**Page 8**
- Changes:
  - The extractor split the reduced RRE model into three formula items (`b004`, `b005`, `b006`). I merged them into `p0008-b004` and removed `b005`/`b006`.
  - Both ODE systems are LaTeX.
  - `b015` joins `b014`.
  - Three run-in `####` heads added: `b009h`, `b016h`, and the two-line head `b019h`.
  - `>1 nM` fixed (native gave "w1 nM").
  - Model names use ℳ<sub>…</sub>.
  - H1–H3 are list items.
- Kept as printed: "due the the" and "pERK".

**Page 9 (Table 1, printed rotated)**
- The extractor table was garbled: transposed, with the caption and footnote mixed in, minus signs read as "2" and ">" read as ".".
- I rebuilt it as a 25×12 CSV `table-1` (bbox [90,54,500,728]) and verified every cell against rotated renders and the JATS table.
- The CSV is flattened:
  - An explicit `Scenario` column repeats each scenario title.
  - The per-scenario scale headers are combined: "ℓ(θ*)(10^4) in Scenario 1; ℓ(θ*)(10^3) in Scenario 2", and the same for BIC.
  - Minus signs are stored as ASCII `-`; ΔBIC ">10" is kept as printed.
- Items:
  - Caption is `p0009-b001` (only "Table 1." is bold, as printed).
  - Footnote is `p0009-b004` (LaTeX for the ΔBIC rule).
  - The empty fragments `p0009-b002` and `b003` were removed.
- No `join_previous` across the float.

## Proposed shared changes for the coordinator

1. **`plan.json` title.** It is currently `pcbi.1003686`. Set it to "ODE Constrained Mixture Modelling: A Method for Unraveling Subpopulation Structures and Dynamics", so the builder drops the duplicate first-page title `p0001-b000`. Otherwise, omit `p0001-b000`.
2. **`reading_order` (optional).**
   - Move the Author Summary (`p0002-b001`, `p0002-b002`) to directly after the Abstract (`p0001-b005`). `p0002-b003` keeps its `join_previous` to `p0001-b016`.
   - You may also move Figure 2 (`p0007-b001`, `b002`) and Table 1 (`p0009-b001`, `b005`, `b004`) to the end of the simulation example, just before `p0006-b008` ("Application example"). Nothing in my pages joins across those positions.
   - Page 8's last item `p0008-b020` ends a paragraph ("…counterintuitive result.").
3. **`plan.json` notes (suggested).**
   - "Mathematical symbols in the PDF text layer use symbol fonts that extract incorrectly; inline and display math was re-transcribed as LaTeX from visual inspection of the source."
   - "Table 1 (printed rotated, two scenario blocks with separate header rows) is flattened into one CSV with a Scenario column; scenario-specific scale factors (10^4 / 10^3) are stated in the combined ℓ(θ*) and BIC headers."
4. **Adjudications.** Pages 2–9 will raise `missing_lines` and number diagnostics that come purely from symbol-font garbling, which no faithful transcription can match:
   - `½…\x03` brackets
   - equation numbers printed as `ð1Þ`
   - Greek letters mapped to Latin
   - `21.9534` for −1.9534 in Table 1
   - `DBIC` for ΔBIC
   - `w`/`&` for >/≫

   My builder-equivalent check (same `canonical()` as `pdf_to_skill.py`) leaves these misses per page: p1 0, p2 22, p3 10, p4 47, p5 10, p6 16, p7 3, p8 20, p9 27. I inspected each missed line, and all are garbled-glyph lines whose content is present in transcribed form.

## Remaining doubts

- The LaTeX display math was not rendered through KaTeX/MathJax here. I checked it manually:
  - balanced braces
  - no `\\[` after a line break
  - `\begin{aligned}{}[` guarded
- ν vs. v on page 4 (see above).
