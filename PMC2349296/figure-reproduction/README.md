# Figure and table reproduction (PMC2349296)

We rerun the paper's two PPI extraction methods on the five unified corpora and redraw Figs 1
and 2. The conversion programs (mars.cs.utu.fi/PPICorpora) and the authors' RelEx
reimplementation are lost. What survives:

- **The unified corpora**, only as a third-party copy: `github.com/metalrt/ppi-dataset`, commit
  `dd49ea3` (2021-07-04), simple Turku XML split into `-train`/`-test` by the copy's author. We
  merge the two files. HPRD50, IEPA and LLL match the paper's counts. AIMed has 1,943 of 1,955
  sentences and no self-interactions (about 5% of AIMed's interactions in the paper). BioInfer
  is the later "much improved" binarization (2,534 interactions; the paper's Causal-Change
  version had about 1,430). A 2018 Wayback capture of the PPICorpora page still links the
  paper's BioInfer file (`bioinfer-1.1.1-unified-format.zip`), but the file itself was never
  archived.
- **MedPost** (NCBI FTP, 2008-07-15 release), the paper's tagger.
- **Stanford Lexicalized Parser 1.5.1** (2006-06-11), the version the paper names, still on
  `downloads.cs.stanford.edu`. It runs on Java 11.
- **RelEx's relation restriction terms**: Fundel et al.'s supplementary page, captured by the
  Wayback Machine in 2014, lists 175 stems. They expand to 1,048 terms, the number in Fundel et
  al.'s paper. The pipeline downloads the capture, checks its SHA-256 and extracts the list
  (`pipeline/extract_terms.py`); the list itself is not redistributed here.

## Results

Each cell is published / ours at the printed precision. The full tables, with every
difference marked, are in [`output/report.md`](output/report.md).

| Corpus | Co-occurrence P / R / F | RelEx P / R / F | Filtered co-occ. F | Filtered RelEx F |
| --- | --- | --- | --- | --- |
| AIMed | 0.17 / 0.95 / 0.29 · **0.17 / 1.00 / 0.29** | 0.40 / 0.50 / 0.44 · **0.40 / 0.50 / 0.44** | 0.68 · **0.70** | 0.63 · **0.64** |
| BioInfer | 0.13 / 0.99 / 0.23 · **0.26 / 1.00 / 0.42** | 0.39 / 0.45 / 0.41 · **0.59 / 0.30 / 0.40** | 0.70 · **0.65** | 0.57 · **0.43** |
| HPRD50 | 0.38 / 1.0 / 0.55 · **0.38 / 1.0 / 0.55** | 0.76 / 0.64 / 0.69 · **0.72 / 0.61 / 0.66** | 0.78 · **0.78** | 0.76 · **0.72** |
| IEPA | 0.41 / 1.0 / 0.58 · **0.41 / 1.0 / 0.58** | 0.74 / 0.61 / 0.67 · **0.70 / 0.53 / 0.60** | 0.94 · **0.94** | 0.75 · **0.69** |
| LLL | 0.50 / 1.0 / 0.66 · **0.50 / 1.0 / 0.66** | 0.82 / 0.72 / 0.77 · **0.93 / 0.68 / 0.78** | 0.66 · **0.66** | 0.77 · **0.78** |

- **Co-occurrence and Table 3** are arithmetic on the annotation: all entity pairs in a
  sentence, scored with the paper's rules (undirected, untyped, entities by occurrence). Where
  the corpus is the paper's, they equal the paper at the printed precision.
- **Table 3 tokens are MedPost tokens.** MedPost's tokenizer gives 25.2, 31.3, 26.1, 32.2 and
  29.6 tokens per sentence, the paper's values on all five corpora (a PTB-style regex gives
  25.2, 31.4, 25.8, 32.4, 29.9). BioInfer's sentences are the paper's; only its annotation changed.
- **RelEx** is our reimplementation (`pipeline/relex.py`), developed on HPRD50 only and then run
  once on all corpora. AIMed comes back at the published values.
- **Figs 1 and 2** are base R plots. We draw them with base R on the published pixel grid
  (`pipeline/figures.R`). A render of the paper's own values matches the published images to
  0.2 to 0.4 px (chamfer), with no residual shift in any region. A render of our values moves
  only where the data differ.

### The claims in the text

`pipeline/claims.R` computes each summary number. From the published tables it returns the
paper's numbers exactly (13.4, 19.4, 10.6 points; 21.1 to 32.4%; Kendall p = 0.083), so the
arithmetic is identified.

| Statistic | Paper | Ours | Ours with the paper's BioInfer row |
| --- | --- | --- | --- |
| Average F gap between the methods | 13 | 8.2 | 11.5 |
| Average pairwise RelEx F difference between corpora | 19 | **19.5** | 19.2 |
| … after filtering | 11 | 15.7 | 10.1 |
| Relative reduction in F error, co-occurrence to RelEx | 21–32% | −2 to 35% | 4 to 35% |
| Co-occurrence beats RelEx on every filtered corpus except LLL | yes | **yes** | yes |
| Kendall p, I/EP against RelEx F | ≈ 0.08 | 0.23 | **0.083** |
| Kendall p, sentences without interactions against RelEx F | n.s. | 0.82 | 0.23 |

The main claim holds: the same method's F varies by 19 points between corpora, more than the
gap between a naive and an advanced method. The filtering and correlation claims depend on
BioInfer. They come back when the paper's BioInfer row replaces the surviving copy's, and not
otherwise. The 21% lower bound comes from IEPA, where our RelEx is 7 points below the paper's.

## What the code does, against the papers

- **Entity names inside words.** "p53-dependent": the paper does not say how such entities
  were tokenized. We insert a space at every entity boundary inside a word before MedPost
  (`preprocess.py`), so every entity is a whole number of tokens.
- **Relation order in Stanford Parser 1.5.1.** For a word pair with two candidate relations
  (`rel` and `nsubj`, say), `GrammaticalStructure.getGrammaticalRelation` keeps whichever comes
  last in a `HashSet` of relation objects hashed by identity. The order, and so some relations,
  depend on the JVM build: Java 11 and Java 24 parse HPRD50 differently, each the same run after
  run. The paper's 2007 JVM had its own order. We run the parser with
  `-XX:+UnlockExperimentalVMOptions -XX:hashCode=2`, which makes every identity hash equal; the
  sets then iterate in insertion order, and Java 11 and Java 24 give byte-identical output. Across
  the three variants (`output/parser_noise/`), every RelEx P, R and F moves by 0.01 at most.
- **Parser input.** MedPost's Penn tags constrain the PCFG (`englishPCFG.ser.gz`; the paper
  does not say which grammar). Brackets become `-LRB-`/`-RRB-`. Output is collapsed typed
  dependencies. 1.5.1's XML output does not escape `<` or `&`, so it is read line by line.
- **Chunking.** Pyysalo et al. chunk "based on an analysis of the dependency graph"; we merge a
  noun with its contiguous `nn`, `amod`, `det`, `num`, `poss` modifiers, and every multi-token
  entity into one chunk.
- **Rule 1 start points.** Fundel et al. start paths at chunks with an incoming subject edge.
  With dependency chunks, "the N-terminus of CCR2" is two chunks, so we also start from protein
  chunks in the subject's nominal subtree, and resolve "which"/"that" subjects of relative
  clauses to the noun they modify. This was the one change made on HPRD50 after the first run
  (HPRD50 F 0.56 → 0.66; LLL F 0.63 → 0.77 was seen at the same time).
- **Negation.** Fundel et al. name "not, without, lack, unable"; the rest of our list is ours.
- **MedPost on x86_64.** `MPtok.C` defines `NUM_ABB` as `sizeof common_abb` (bytes, not
  entries), so the tokenizer reads past the table and crashes. `build_medpost.sh` divides by the
  entry size and builds at `-O0` (`-O2` still crashes). Two more fixes: the tagger deletes an
  uninitialized lexicon pointer, and `run_tokenizer` falls off the end of an `int` function. On
  the ubuntu-24.04 CI runner the second lost the tokenizer's last buffered output (18 AIMed
  sentences). With all three fixes, a build with AddressSanitizer and fatal UBSan and a plain
  build give byte-identical output on all five corpora. Only the tokenizer and tagger are built.

## Layout

```text
figure-reproduction/
├── main.nf, nextflow.config     Nextflow pipeline; run_skyriver.sbatch runs it on Slurm
├── pipeline/
│   ├── fetch_inputs.sh          corpora, MedPost, Stanford Parser 1.5.1, with SHA-256 checks
│   ├── corpus.py                loader and scorer (the paper's evaluation rules)
│   ├── cooccurrence.py          co-occurrence (Tables 2, 4), statistics (Table 3)
│   ├── build_medpost.sh         builds MedPost's tokenizer and tagger
│   ├── preprocess.py            MedPost input, token alignment, parser input, MedPost token counts
│   ├── relex.py, extract_terms.py  RelEx reimplementation; Fundel et al.'s terms from the capture
│   ├── claims.R                 summary numbers and Kendall tests (R cor.test)
│   ├── figures.R                Figs 1 and 2 in base R
│   ├── compare_figures.py       pixel comparison, overlay and difference images
│   ├── fit_figures.py           fits the presentation parameters (params/)
│   ├── check_reproduction.py    check step and report.md
│   ├── build_page.py, page_template.html   the comparison page
│   ├── published_values.csv, published_tables.csv   the paper's numbers
│   └── params/                  figure parameters, fit log, comparison regions
├── published/                   Figs 1 and 2 as published (CC BY 2.0)
└── output/                      committed results of a full run
```

## Run

```bash
nextflow run PMC2349296/figure-reproduction/main.nf --outdir results
```

The pipeline needs Python 3 with numpy, pillow and scipy, R (base only), Java 11 or later, a C++
compiler, Perl and curl. On the Skyriver cluster, do not run it on the login node. Submit it
from this folder: `sbatch run_skyriver.sbatch`. The Nextflow head then runs on `debugq` and
every process is its own `defq15` job. The parser step takes up to 11 minutes and 3.8 GB per
corpus. CI (`.github/workflows/reproduce-pmc2349296.yml`) runs the same pipeline on an x86_64
`ubuntu-24.04` runner, on every pull request and push to main that touches this folder.

The check step fails when co-occurrence or the Table 3 statistics differ from the paper at the
printed precision on HPRD50, IEPA or LLL, when the MedPost token counts differ on any corpus,
when the claims computed from the published tables differ from the paper's text, or when the
run differs from the committed results in `output/`.

`results.json` lists the results this reproduction stands on, with the tolerance each may move by.
A pull request that creates or changes it is checked against the committed outputs, and every rerun
is checked against the run (see the [top-level README](../../README.md#results-check)).

## Fitted, not measured

- Figures: point size 12 (R's default), symbol size `cex` 1.2, legend symbol spacing
  `x.intersp` 1.4 (Fig. 1) and 1.3 (Fig. 2); `mgp` and legend line spacing stay at R's defaults.
  Fitted on a render of the published values (`params/fit_figures.csv`). Axis positions, legend
  corners and the grey of Fig. 2 are measured from the published images. The renders use DejaVu
  Sans; the published text is a Helvetica-like face.
- RelEx: the choices listed above. Each changes the RelEx numbers; none changes co-occurrence or
  Table 3.

## Limits

- BioInfer is not the paper's version, so every BioInfer number and every statistic over the
  five corpora differs for that reason.
- RelEx is a reimplementation of a reimplementation. Its numbers carry our choices.
- MedPost is the 2008-07-15 release; the paper (submitted early 2008) used an earlier one.
- Figs 3 and 4, Tables 1 and 5 are not reproduced (see the folder README).
