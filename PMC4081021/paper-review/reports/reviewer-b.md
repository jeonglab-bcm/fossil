# Reviewer B report: s001-pcbi-1003686, pages 10-17

Scope: `documents/s001-pcbi-1003686/pages/page-0010.json` through `page-0017.json` (exclusive). Page 9 was used read-only as context; pages 1-8 were read only to confirm cross-page continuations. No shared files (plan.json, bundle.json, adjudications.json) were edited and no build command was run.

Every page was checked against its preview, bbox overlays drawn on renders of `source.pdf`, 3-6x PyMuPDF crops of captions, inline math, the rotated Table 2 and the reference list, and the evidence lines. All eight pages are set to `reviewed: true` with specific `review_notes`. Each file parses as JSON, and the engine's read-only `load_plan()` accepts the whole document: 334 items, all IDs unique, asset names unique. A line-coverage check that reproduces the verifier's `canonical()` finds no missing native lines on pages 10, 12, 13, 16 and 17. The few remaining misses on pages 11, 14 and 15 are parser-only (listed below).

## Conventions used (please harmonise with reviewer A)

- **Model symbols:** written `ℳ<sub>H1,2</sub>` (U+2133 plus HTML sub). I chose this over LaTeX because the verifier's `canonical()` reduces it to `mh12`, which matches the text layer's `MH1,2`. LaTeX `\mathcal{M}_{...}` would make every such line fail line coverage. Other inline math is also written with `<sub>`/Unicode, e.g. `Δ<sub>BIC</sub>`, `[Erk]<sub>0</sub>`, `*s*<sub>1</sub>[pErk]`, `*n* = 4`, `≈30%`.
- **Headings:** `## Discussion`, `## Supporting Information`, `## Acknowledgments`, `## Author Contributions` and `## References`. The JATS XML (`sources/fulltext.xml`) shows "Comparison of pathway models" and "Validation of subpopulation structure" as level-3 secs under "Application example: NGF-induced Erk1/2 signalling". I split these bold run-in titles into `####` headings (new IDs `p0010-b004h` and `p0011-b007h`). The earlier run-ins on pages 6-8 have the same JATS status ("Experimental data", "Pathway model", "Inference of subpopulation structure", "Size and characteristics of subpopulations", "Quantification of kinetic parameters and abundance differences") and should be treated the same way. That makes Results `##`, "Simulation example…" and "Application example…" `###`, and the run-ins `####`. Pages 1-9 still carry `#`-level headings from extraction.
- **Captions:** each figure caption is a separate `caption` item with the full printed text and doi, and its title sentence is bolded.
- **Figure assets:** `figure-3`, `figure-4`, `figure-5` and `figure-6`, labelled "Figure N".
- **Table 2:** `table-2`, transcribed as a CSV.

## Per page

### Page 10
- **Order:** p0010-b003 (the unindented left-column paragraph that continues p0008-b020), then Figure 3, its caption, the `#### Comparison of pathway models` heading, p0010-b004, p0010-b005 (`join_previous: space`, the same paragraph across columns), and p0010-b006.
- **join_previous on p0010-b003 is not set.** The paragraph does continue from page 8 ("…counterintuitive result. While the kinetic parameters…"), but in default order page 9 (Table 1) sits in between, so the join would fail or glue onto a page-9 caption. See the reading_order proposal below.
- **Fixes:** model symbols restored (the text layer prints `MH1,2`), and `n~4` became `n = 4` in the caption.
- **Figure 3 bbox** `[53,55,550,491]` was verified to enclose panels A-D and their labels.
- Header, both footers and the page number are set to `omit` with reasons.

### Page 11
- **Order:** p0011-b004 (`join_previous: space`; continues "…a negative | feedback"), then Table 2 as title caption p0011-b001, CSV table p0011-b003 and footnote caption p0011-b002. The table is placed at the paragraph boundary after p0011-b004. After it come p0011-b005, p0011-b006, the `#### Validation of subpopulation structure` heading, and p0011-b007 to p0011-b009.
- **Table 2:** it is printed rotated in the left half of the page. I transcribed all 10 rows x 11 columns from a 3x render and cross-checked them against the publisher XML.
  - The text layer encodes minus as `2` (e.g. `25.2890` is printed −5.2890) and `>10` as `.10`. The CSV uses the printed `−5.2890` (U+2212) and `>10`.
  - Headers are `ℓ(θ*)(10⁴)`, `BIC (10⁴)` and `ΔBIC`. The top-left header cell is blank, as in the source.
  - In the CSV, model names are written `ℳ_H1,1` and variability values `[Erk]_0` / `[TrkA]_0`.
- **Bboxes:** table `[91,55,238,727]` (from the vector rules), title `[65,288,76,726]`, footnote `[243,56,286,726]`.
- **Text fixes:**
  - "non-identifiable" and "2-dimensional" lost their compound hyphens at line breaks; restored.
  - Restored italic *Materials and Methods* and `ℳ<sub>H3,3</sub>`.
  - Footnote math restored as `Δ<sub>BIC</sub> = BIC<sub>i</sub> − BIC<sub>opt</sub> > 10`.

### Page 12
- **Order:** p0012-b003 and p0012-b004, both `join_previous: space`. They are one paragraph that runs from p0011-b009 to p0013-b003. Figure 4 and its caption follow them.
- **Fixes:** `&30%` became `≈30%`, `ODEMMs` became `ODE-MMs`, `colabelling` became `co-labelling`, `n~4` became `n = 4`, and model symbols were restored.
- **Possible source error, kept as printed:** the caption's panel (D) text says ℳ<sub>H1,2</sub> and ℳ<sub>H1,3</sub>, verified at 5x, although panel D's legend shows MH3,2/MH3,3.
- **Figure 4 bbox** checked: it covers panels A-D, the legends and the w1 strip.

### Page 13
- **Order:** p0013-b003, then Figure 5 and its caption, then p0013-b004 ("To conclude", an indented new paragraph).
- **join_previous on p0013-b003 is not set**, although it continues p0012-b004 ("…from the co-labelling | data using mixture modelling…"). In default order the Figure 4 caption precedes it. See the reading_order proposal.
- **Caption:** restored "NGF-induced" and "ODE-constrained". The source typos "three model" and "mean or media" are kept.
- **Figure 5 bbox** `[53,55,439,583]` covers panels A-C and the legend.

### Page 14
- **Order:** p0014-b001 (`join_previous: space`; ends the Results paragraph begun at p0013-b004), then Figure 6 and its caption. I placed them before `## Discussion` so the figure stays with Results and does not split the Discussion paragraph that crosses to page 15. Then come p0014-b003 to p0014-b007, with p0014-b005 joined to p0014-b004 across columns.
- **Caption math:** `n = 3`, `*s*<sub>1</sub>[pErk]` and `*s*<sub>2</sub>([Erk] + [pErk])`. The source typo "1 nM NFG" is kept.
- Prose de-hyphenation was checked against the evidence lines.

### Page 15
- **Order:** the left-column Discussion; then the right column (end of Discussion, Supporting Information, Acknowledgments, Author Contributions); then the full-width References (refs 1-7 left, 8-13 right).
- **Joins:** p0015-b001 continues p0014-b007 and p0015-b005 continues p0015-b004 (both `space`, valid in default order).
- **Fixes:**
  - Restored "stimulus-induced", "Fröhlich" and "reagents/materials".
  - The stand-alone "(ZIP)" item p0015-b009 is merged into the Code S1 item, matching how "(PDF)" sits in the S1 item.
- **References 1-13:** one item per entry, rebuilt from evidence lines. Diacritics repaired (Schütte, Ibàñez as printed with a grave accent, Špidlen) and the wrap "high-dimensional" fixed.

### Page 16
- **Merged references:** extraction had joined refs 22-24, 25-27, 31-33, 34-35, 36-37 and 38-39, so nine references were not separate items. The page is rebuilt as one text item per reference (14-77).
- **IDs:** the original ID is kept for the first reference in each old item, and split-offs get suffixes (`p0016-b009a/b`, `b010a/b`, `b014a/b`, `b015a`, `b016a`, `b017a`).
- **Fixes:** diacritics repaired (Allgöwer, Schöberl, Krüger, Böhm, González, Bäck, Klingmüller) and wrap joins fixed (Discreteness-induced, High-dimensional, JAK2/STAT5, 189–228, 247–249, TRAIL-induced).
- **Checks:** numbering is continuous and matches the publisher list.

### Page 17
- Refs 78-85; the rest of the page is blank. Refs 82 and 83 were merged; ref 83 is now `p0017-b005a`.
- "Trümbach" and "Input–output" repaired.
- The last reference is 85.

## Remaining doubts and limitations

- **Missing ligatures in the source.** The reference font in the source PDF itself has no fl/ffi glyphs: it renders "ow cytometry", "immunouorescence", "uctuations", "uorescent" and "affnity" (verified at 5x; the publisher XML has the same defect). I kept these as printed. As a result, a search for "flow cytometry" will not hit refs 7 and 14-17.
- **Source typos kept as printed:** "acidtransformation", "8519–8124", "Proc Nati Acad", "M P Vecchi MP", "Mol Syst Biol 516", "1 nM NFG", "mean or media", and the Figure 4 (D) model names.

## Proposed shared changes for the coordinator

### 1. plan.json `reading_order` (needed for two joins)
Use default order everywhere except for these two changes.

- **(a) Page 9 vs p0010-b003.** p0010-b003 must come immediately after p0008-b020. Move the non-omitted p0009 items (the Table 1 block) elsewhere: either right after p0010-b003, or to where Table 1 is first cited in the simulation-example Results. Then set `"join_previous": "space"` on p0010-b003.
- **(b) Figure 4.** Move p0012-b001 and p0012-b002 (Figure 4 and its caption) to directly after p0013-b003, then set `"join_previous": "space"` on p0013-b003.

The resulting segment for my range:

```
… p0008-b020, p0010-b003*, [p0009 Table 1 items, or wherever placed],
p0010-b001, p0010-b002, p0010-b004h, p0010-b004, p0010-b005, p0010-b006,
p0011-b004, p0011-b001, p0011-b003, p0011-b002, p0011-b005, p0011-b006,
p0011-b007h, p0011-b007, p0011-b008, p0011-b009,
p0012-b003, p0012-b004, p0013-b003*, p0012-b001, p0012-b002,
p0013-b001, p0013-b002, p0013-b004,
then pages 14-17 in their page-file order (all non-omitted items).
```

`*` marks the items that need `join_previous: space` once the reading_order is in place. I did not set them, because without the reorder they would join to the wrong item.

### 2. Plan `notes` (suggested)
- "The reference list font in the source PDF lacks fl/ffi ligature glyphs (e.g. 'ow cytometry' = flow cytometry, 'immunouorescence' = immunofluorescence, 'uctuations' = fluctuations, 'affnity' = affinity); references are transcribed as printed."
- Optionally: "Figure 4 caption panel (D) names ℳH1,2/ℳH1,3 as printed, although the panel shows ℳH3,2/ℳH3,3."

### 3. Expected parser-only diagnostics to adjudicate after the build
These are visible-source checks I have already done.

- **p11, Table 2 (text-layer encoding):**
  - Minus printed as `2`: `25.2890` is −5.2890, and likewise for all nine ℓ(θ*) values.
  - `.10` is >10, `DBIC` is ΔBIC, and `,(h\x02)(104)` is ℓ(θ*)(10⁴).
  - Expect numeric-token differences for 10⁴ (`104` in the text layer).
- **p11, Table 2 footnote:** `½Erk\x030` is [Erk]₀, and `DBIC~BICi{BICoptw10` is ΔBIC = BICi − BICopt > 10.
- **p14, Figure 6 caption:** `s1½pErk\x03` is s₁[pErk], and `s2(½Erk\x03z½pErk\x03)` is s₂([Erk] + [pErk]).
- **p15, ref 12:** `Sˇpidlen` is Špidlen (U+02C7 is alphanumeric under `canonical()`).

### 4. Consistency with reviewer A
- Adopt the same model-symbol notation (`ℳ<sub>…</sub>`) and the `####` run-in subsection headings on pages 6-8.
- Use `table-1` for the page-9 Table 1 (`table-2` is taken by page 11).
